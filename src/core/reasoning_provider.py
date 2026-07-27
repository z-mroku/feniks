import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import ServerError
from pydantic import BaseModel, Field


class ReasoningMode(Enum):
    """
    Określa etap procesu rozumowania FENIKSA.

    DIAGNOSIS:
        Najpierw ustalamy, czy problem rzeczywiście istnieje.
        Nie wolno jeszcze projektować jego rozwiązania.

    SOLUTION:
        Problem został wcześniej potwierdzony dowodami.
        Można projektować i porównywać rozwiązania.
    """

    DIAGNOSIS = "DIAGNOZA"
    SOLUTION = "ROZWIAZANIE"


class ReasoningResult(BaseModel):
    """
    Ustrukturyzowany wynik zewnętrznego rozumowania.

    Wynik NIE jest automatycznie uznawany za prawdę.
    Jest propozycją analizy, którą FENIKS musi później
    zweryfikować własnymi mechanizmami.
    """

    problem_understood_as: str
    known_facts: list[str]
    unknowns: list[str]
    hypothesis: str
    variable_under_test: str
    controlled_variables: list[str]
    experiment: str
    expected_observations: list[str]
    conclusion_rule: str
    cannot_conclude_yet: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class ReasoningProvider(ABC):
    """Wspólny interfejs zewnętrznych dostawców rozumowania."""

    @abstractmethod
    def analyze(
        self,
        title: str,
        description: str,
        evidence: list[str],
        unknowns: list[str],
        history: Optional[list[str]] = None,
        mode: ReasoningMode = ReasoningMode.DIAGNOSIS,
    ) -> ReasoningResult:
        raise NotImplementedError


class GeminiReasoningProvider(ReasoningProvider):
    """
    Dostawca rozumowania wykorzystujący Gemini API.

    Model zewnętrzny jest warstwą analityczną, nie źródłem prawdy.
    Przy przejściowym błędzie 503 modelu podstawowego provider może
    użyć jawnie określonego modelu zapasowego.
    """

    MODEL = "gemini-3.5-flash"
    FALLBACK_MODEL = "gemini-3.6-flash"

    SYSTEM_INSTRUCTION = """
Jesteś zewnętrzną warstwą analityczną systemu FENIKS.

Twoja odpowiedź jest propozycją rozumowania, a nie źródłem prawdy.

Musisz ściśle rozdzielać:
1. fakty wynikające z dostarczonych danych,
2. niewiadome,
3. hipotezy,
4. proponowane eksperymenty,
5. kryteria rozstrzygnięcia.

Nie wolno ci:
- wymyślać wyników eksperymentów,
- przedstawiać przewidywania jako obserwacji,
- tworzyć arbitralnych progów liczbowych bez uzasadnienia,
- uznawać hipotezy za fakt,
- udawać wiedzy, której nie ma w dostarczonych danych.

Jeżeli danych jest za mało, powiedz to wprost.
Nie wypełniaj luk pozorną pewnością.

Jeżeli proponujesz wartość liczbową, której nie można wyprowadzić
z dostarczonych danych, oznacz ją jako parametr wymagający
ustalenia eksperymentalnego.

Każdy eksperyment musi dotyczyć konkretnego badanego problemu.

Historia FENIKSA może być wykorzystana jako kontekst,
ale nie wolno automatycznie traktować jej jako dowodu
prawdziwości obecnej hipotezy.
"""

    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
    ):
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("Brak GEMINI_API_KEY w środowisku.")

        self.model = model or self.MODEL
        self.fallback_model = fallback_model or self.FALLBACK_MODEL
        self.client = genai.Client()

        self.last_model_used: Optional[str] = None
        self.last_fallback_used: bool = False
        self.last_primary_error: Optional[str] = None

    def analyze(
        self,
        title: str,
        description: str,
        evidence: list[str],
        unknowns: list[str],
        history: Optional[list[str]] = None,
        mode: ReasoningMode = ReasoningMode.DIAGNOSIS,
    ) -> ReasoningResult:
        history = history or []

        prompt = self._build_prompt(
            title=title,
            description=description,
            evidence=evidence,
            unknowns=unknowns,
            history=history,
            mode=mode,
        )

        self.last_model_used = None
        self.last_fallback_used = False
        self.last_primary_error = None

        try:
            text = self._generate(self.model, prompt)
            self.last_model_used = self.model
        except ServerError as exc:
            if getattr(exc, "code", None) != 503:
                raise
            self.last_primary_error = str(exc)
            text = self._generate(self.fallback_model, prompt)
            self.last_model_used = self.fallback_model
            self.last_fallback_used = True

        return ReasoningResult.model_validate_json(text)

    def _generate(self, model: str, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=ReasoningResult,
                temperature=0.2,
            ),
        )

        if not response.text:
            raise RuntimeError(
                f"Gemini ({model}) nie zwróciło treści analizy."
            )

        return response.text

    def _build_prompt(
        self,
        title: str,
        description: str,
        evidence: list[str],
        unknowns: list[str],
        history: list[str],
        mode: ReasoningMode,
    ) -> str:
        evidence_text = (
            "\n".join(f"- {item}" for item in evidence)
            if evidence else "- BRAK DOSTARCZONYCH DOWODÓW"
        )
        unknowns_text = (
            "\n".join(f"- {item}" for item in unknowns)
            if unknowns else "- BRAK JAWNIE ZAPISANYCH NIEWIADOMYCH"
        )
        history_text = (
            "\n".join(f"- {item}" for item in history)
            if history else "- BRAK DOSTARCZONEJ HISTORII"
        )

        if mode == ReasoningMode.DIAGNOSIS:
            mode_instruction = """
TRYB: DIAGNOZA

Ustal, czy opisany problem rzeczywiście istnieje.
NIE PROPONUJ JESZCZE ROZWIĄZANIA PROBLEMU.

Hipoteza ma dotyczyć zachowania OBECNEGO systemu.
Eksperyment ma badać OBECNY system bez jego modyfikowania.

Jeżeli dane nie wystarczają do potwierdzenia problemu,
zaproponuj eksperyment pozwalający go potwierdzić albo obalić.
"""
        elif mode == ReasoningMode.SOLUTION:
            mode_instruction = """
TRYB: POSZUKIWANIE ROZWIĄZANIA

Problem został wcześniej potwierdzony eksperymentalnie
lub dowodami. Możesz proponować możliwe rozwiązania,
ale żadnego nie przedstawiaj jako sprawdzonego.

Oddziel propozycję od faktu, wskaż założenia i słabości,
sposób testowania oraz kryterium powodzenia.
Nie wymyślaj wyników przyszłych testów.
"""
        else:
            raise ValueError(f"Nieobsługiwany tryb rozumowania: {mode}")

        return f"""
{mode_instruction}

PROBLEM:
{title}

OPIS:
{description}

DOSTĘPNE DOWODY:
{evidence_text}

NIEWIADOME:
{unknowns_text}

ISTOTNA HISTORIA FENIKSA:
{history_text}

Przeanalizuj dokładnie ten problem.

Historia jest kontekstem, a nie automatycznym dowodem.
Nie wymyślaj brakujących danych.
Jeżeli czegoś nie da się obecnie ustalić, pozostaw to
jako niewiadomą lub granicę wnioskowania.

Nie przedstawiaj przewidywanego wyniku eksperymentu
jako wyniku rzeczywiście zaobserwowanego.

Zwrócony wynik będzie dopiero kandydatem do dalszej
weryfikacji przez FENIKSA.
"""
