import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from google import genai
from google.genai import types
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

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class ReasoningProvider(ABC):
    """
    Wspólny interfejs zewnętrznych dostawców rozumowania.

    Rdzeń FENIKSA nie powinien wiedzieć,
    czy analiza pochodzi z Gemini, OpenAI
    czy przyszłego modelu lokalnego.
    """

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

    Gemini może:
    - analizować problem,
    - tworzyć hipotezę,
    - projektować eksperyment,
    - proponować rozwiązania, jeśli FENIKS jawnie
      przełączy analizę w tryb SOLUTION.

    Gemini NIE może:
    - samodzielnie zapisywać pamięci FENIKSA,
    - zmieniać kodu FENIKSA,
    - samodzielnie rozstrzygać prawdy,
    - wykonywać proponowanego eksperymentu,
    - uznawać swojej odpowiedzi za dowód.
    """

    MODEL = "gemini-3.5-flash"

    SYSTEM_INSTRUCTION = """
Jesteś zewnętrzną warstwą analityczną systemu FENIKS.

Twoja odpowiedź jest propozycją rozumowania,
a nie źródłem prawdy.

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

Jeżeli proponujesz wartość liczbową, której nie można
wyprowadzić z dostarczonych danych, musisz jawnie
oznaczyć ją jako parametr wymagający ustalenia
eksperymentalnego.

Każdy eksperyment musi dotyczyć konkretnego
badanego problemu.

Historia FENIKSA może być wykorzystana jako kontekst,
ale nie wolno automatycznie traktować jej jako dowodu
prawdziwości obecnej hipotezy.
"""

    def __init__(
        self,
        model: Optional[str] = None,
    ):
        """
        Tworzy dostawcę Gemini.

        Klucz API pobierany jest wyłącznie
        ze zmiennej środowiskowej GEMINI_API_KEY.
        """

        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError(
                "Brak GEMINI_API_KEY w środowisku."
            )

        self.model = model or self.MODEL

        self.client = genai.Client()

    def analyze(
        self,
        title: str,
        description: str,
        evidence: list[str],
        unknowns: list[str],
        history: Optional[list[str]] = None,
        mode: ReasoningMode = ReasoningMode.DIAGNOSIS,
    ) -> ReasoningResult:
        """
        Przeprowadza analizę problemu.

        Domyślnym trybem jest DIAGNOSIS.

        Oznacza to, że FENIKS najpierw bada,
        czy problem rzeczywiście istnieje.

        Tryb SOLUTION powinien być używany dopiero,
        gdy problem został wcześniej potwierdzony
        rzeczywistym eksperymentem lub dowodami.
        """

        history = history or []

        prompt = self._build_prompt(
            title=title,
            description=description,
            evidence=evidence,
            unknowns=unknowns,
            history=history,
            mode=mode,
        )

        response = self.client.models.generate_content(
            model=self.model,
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
                "Gemini nie zwróciło treści analizy."
            )

        return ReasoningResult.model_validate_json(
            response.text
        )

    def _build_prompt(
        self,
        title: str,
        description: str,
        evidence: list[str],
        unknowns: list[str],
        history: list[str],
        mode: ReasoningMode,
    ) -> str:
        """
        Buduje instrukcję przekazywaną do modelu.

        Instrukcja zależy od aktualnego etapu
        rozumowania FENIKSA.
        """

        evidence_text = (
            "\n".join(
                f"- {item}"
                for item in evidence
            )
            if evidence
            else "- BRAK DOSTARCZONYCH DOWODÓW"
        )

        unknowns_text = (
            "\n".join(
                f"- {item}"
                for item in unknowns
            )
            if unknowns
            else "- BRAK JAWNIE ZAPISANYCH NIEWIADOMYCH"
        )

        history_text = (
            "\n".join(
                f"- {item}"
                for item in history
            )
            if history
            else "- BRAK DOSTARCZONEJ HISTORII"
        )

        if mode == ReasoningMode.DIAGNOSIS:
            mode_instruction = """
TRYB: DIAGNOZA

Twoim zadaniem jest ustalić,
czy opisany problem rzeczywiście istnieje.

NIE PROPONUJ JESZCZE ROZWIĄZANIA PROBLEMU.

Nie projektuj:

- nowych algorytmów naprawczych,
- nowych funkcji agregacji,
- progów naprawczych,
- zmian architektury,
- mechanizmów mających usunąć problem.

Hipoteza ma dotyczyć zachowania OBECNEGO systemu.

Eksperyment ma badać OBECNY system
bez jego modyfikowania.

Jeżeli obecne dane nie wystarczają do potwierdzenia
problemu, zaprojektuj eksperyment pozwalający
go potwierdzić albo obalić.

Najpierw FENIKS musi uzyskać dowód,
że problem rzeczywiście istnieje.

Dopiero po potwierdzeniu problemu może zostać
uruchomiony osobny etap poszukiwania rozwiązania.
"""

        elif mode == ReasoningMode.SOLUTION:
            mode_instruction = """
TRYB: POSZUKIWANIE ROZWIĄZANIA

Problem został wcześniej potwierdzony
eksperymentalnie lub dowodami.

Możesz teraz proponować możliwe rozwiązania.

Nie przedstawiaj jednak żadnego rozwiązania
jako sprawdzonego lub prawdziwego.

Musisz:

- oddzielić propozycję od faktu,
- wskazać założenia rozwiązania,
- wskazać potencjalne słabości rozwiązania,
- określić sposób jego przetestowania,
- określić kryterium powodzenia testu.

Nie wymyślaj wyników przyszłych testów.

Jeżeli parametr rozwiązania nie jest znany,
oznacz go jako wymagający ustalenia
eksperymentalnego.
"""

        else:
            raise ValueError(
                f"Nieobsługiwany tryb rozumowania: {mode}"
            )

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

Nie zakładaj, że historia jest dowodem
prawdziwości obecnego twierdzenia.

Nie wymyślaj brakujących danych.

Nie przedstawiaj przewidywanego wyniku
eksperymentu jako wyniku rzeczywiście
zaobserwowanego.

Zwrócony wynik będzie dopiero kandydatem
do dalszej weryfikacji przez FENIKSA.
"""