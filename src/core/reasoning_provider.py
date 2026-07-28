# -*- coding: utf-8 -*-

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from infrastructure.model_gateway import ModelGateway


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
    Ustrukturyzowany kandydat rozumowania.

    ReasoningResult NIE jest automatycznie prawdą.

    Jest wynikiem zewnętrznej warstwy analitycznej,
    który FENIKS może następnie poddać własnej kontroli,
    walidacji i dalszemu procesowi poznawczemu.
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


class ReasoningExecutionState(Enum):
    """
    Stan wykonania zewnętrznego rozumowania.

    REASONED:
        Zewnętrzna warstwa analityczna rzeczywiście
        zwróciła wynik zgodny z kontraktem ReasoningResult.

    UNAVAILABLE:
        Rozumowanie nie zostało wykonane, ponieważ
        dostępne modele były chwilowo niedostępne.

    Stan infrastruktury nie jest stanem wiedzy.
    """

    REASONED = "REASONED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ReasoningExecutionResult:
    """
    Wynik wykonania zewnętrznej warstwy rozumowania.

    Ten obiekt świadomie oddziela:

    - wynik poznawczy,
    - stan wykonania infrastruktury.

    Niedostępność modelu nie może zostać przedstawiona
    jako hipoteza, niewiadoma ani wynik rozumowania.
    """

    state: ReasoningExecutionState
    reasoning: Optional[ReasoningResult]

    model_used: Optional[str]
    fallback_used: bool

    primary_error: Optional[str] = None
    fallback_error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.state is ReasoningExecutionState.REASONED:
            if self.reasoning is None:
                raise ValueError(
                    "Stan REASONED wymaga obiektu ReasoningResult."
                )

            if not self.model_used:
                raise ValueError(
                    "Stan REASONED wymaga informacji o użytym modelu."
                )

        elif self.state is ReasoningExecutionState.UNAVAILABLE:
            if self.reasoning is not None:
                raise ValueError(
                    "Stan UNAVAILABLE nie może zawierać "
                    "wyniku rozumowania."
                )

            if self.model_used is not None:
                raise ValueError(
                    "Stan UNAVAILABLE nie może wskazywać modelu "
                    "jako skutecznie użytego."
                )

        else:
            raise ValueError(
                f"Nieobsługiwany stan wykonania: {self.state}"
            )

    @property
    def reasoned(self) -> bool:
        return self.state is ReasoningExecutionState.REASONED

    @property
    def unavailable(self) -> bool:
        return self.state is ReasoningExecutionState.UNAVAILABLE


class ReasoningProvider(ABC):
    """
    Wspólny kontrakt zewnętrznych dostawców rozumowania.

    Provider nie jest źródłem prawdy.

    Jego zadaniem jest dostarczenie kandydata analizy
    albo jawne poinformowanie, że analiza nie została
    wykonana z powodu niedostępności infrastruktury.
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
    ) -> ReasoningExecutionResult:
        raise NotImplementedError


class GeminiReasoningProvider(ReasoningProvider):
    """
    Zewnętrzna warstwa analityczna wykorzystująca Gemini API.

    Gemini jest narzędziem FENIKSA, a nie FENIKSEM.

    Provider:
    - przygotowuje zadanie analityczne,
    - zleca wykonanie modelowi przez ModelGateway,
    - waliduje rzeczywistą odpowiedź,
    - zwraca jawny stan wykonania.

    Provider nie:
    - uznaje odpowiedzi modelu za prawdę,
    - wymyśla wyniku przy awarii modeli,
    - ukrywa niedostępności infrastruktury,
    - zapisuje wyniku do wiedzy FENIKSA.
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
5. kryteria rozstrzygnięcia,
6. granice tego, czego obecnie nie można uczciwie ustalić.

Nie wolno ci:
- wymyślać wyników eksperymentów,
- przedstawiać przewidywania jako obserwacji,
- tworzyć arbitralnych progów liczbowych bez uzasadnienia,
- uznawać hipotezy za fakt,
- udawać wiedzy, której nie ma w dostarczonych danych,
- traktować historii jako automatycznego dowodu
  prawdziwości obecnej hipotezy.

Jeżeli danych jest za mało, powiedz to wprost.
Nie wypełniaj luk pozorną pewnością.

Jeżeli proponujesz wartość liczbową, której nie można
wyprowadzić z dostarczonych danych, oznacz ją jako parametr
wymagający ustalenia eksperymentalnego.

Każdy eksperyment musi dotyczyć konkretnego badanego problemu.

Historia FENIKSA może być wykorzystana jako kontekst,
ale pozostaje kontekstem, dopóki nie istnieją niezależne
podstawy pozwalające potraktować ją inaczej.

Zwracany wynik będzie kandydatem do dalszej weryfikacji
przez FENIKSA.
"""

    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        gateway: Optional[ModelGateway] = None,
    ) -> None:
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError(
                "Brak GEMINI_API_KEY w środowisku."
            )

        self.model = model or self.MODEL
        self.fallback_model = (
            fallback_model or self.FALLBACK_MODEL
        )

        self.client = genai.Client()

        self.gateway = gateway or ModelGateway()

        self.last_model_used: Optional[str] = None
        self.last_fallback_used: bool = False
        self.last_primary_error: Optional[str] = None
        self.last_fallback_error: Optional[str] = None

        self.attempt_count = 0
        self.analysis_count = 0

    def analyze(
        self,
        title: str,
        description: str,
        evidence: list[str],
        unknowns: list[str],
        history: Optional[list[str]] = None,
        mode: ReasoningMode = ReasoningMode.DIAGNOSIS,
    ) -> ReasoningExecutionResult:
        """
        Próbuje przeprowadzić zewnętrzne rozumowanie.

        Każde wywołanie zwiększa licznik prób.

        Licznik wykonanych analiz zwiększa się wyłącznie wtedy,
        gdy model rzeczywiście zwrócił odpowiedź i odpowiedź
        przeszła walidację ReasoningResult.

        Niedostępność modeli nie tworzy ReasoningResult.
        """

        if not isinstance(title, str):
            raise TypeError("title musi być tekstem.")

        if not isinstance(description, str):
            raise TypeError("description musi być tekstem.")

        if not isinstance(evidence, list):
            raise TypeError("evidence musi być listą.")

        if not isinstance(unknowns, list):
            raise TypeError("unknowns musi być listą.")

        if history is not None and not isinstance(history, list):
            raise TypeError("history musi być listą albo None.")

        if not isinstance(mode, ReasoningMode):
            raise TypeError(
                "mode musi być wartością ReasoningMode."
            )

        history_items = history or []

        prompt = self._build_prompt(
            title=title,
            description=description,
            evidence=evidence,
            unknowns=unknowns,
            history=history_items,
            mode=mode,
        )

        self.attempt_count += 1

        self.last_model_used = None
        self.last_fallback_used = False
        self.last_primary_error = None
        self.last_fallback_error = None

        gateway_result = self.gateway.execute(
            primary_model=self.model,
            fallback_model=self.fallback_model,
            generate=lambda model: self._generate(
                model=model,
                prompt=prompt,
            ),
        )

        self.last_model_used = gateway_result.model_used
        self.last_fallback_used = gateway_result.fallback_used
        self.last_primary_error = gateway_result.primary_error
        self.last_fallback_error = gateway_result.fallback_error

        if gateway_result.unavailable:
            return ReasoningExecutionResult(
                state=ReasoningExecutionState.UNAVAILABLE,
                reasoning=None,
                model_used=None,
                fallback_used=gateway_result.fallback_used,
                primary_error=gateway_result.primary_error,
                fallback_error=gateway_result.fallback_error,
            )

        if gateway_result.text is None:
            raise RuntimeError(
                "ModelGateway zgłosił sukces bez treści odpowiedzi."
            )

        reasoning = ReasoningResult.model_validate_json(
            gateway_result.text
        )

        self.analysis_count += 1

        return ReasoningExecutionResult(
            state=ReasoningExecutionState.REASONED,
            reasoning=reasoning,
            model_used=gateway_result.model_used,
            fallback_used=gateway_result.fallback_used,
            primary_error=gateway_result.primary_error,
            fallback_error=gateway_result.fallback_error,
        )

    def _generate(
        self,
        model: str,
        prompt: str,
    ) -> str:
        """
        Wykonuje pojedynczą próbę wywołania konkretnego modelu.

        Ta metoda nie decyduje o fallbacku.
        Polityka dostępności należy wyłącznie do ModelGateway.
        """

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

        if mode is ReasoningMode.DIAGNOSIS:
            mode_instruction = """
TRYB: DIAGNOZA

Ustal, czy opisany problem rzeczywiście istnieje.
NIE PROPONUJ JESZCZE ROZWIĄZANIA PROBLEMU.

Hipoteza ma dotyczyć zachowania OBECNEGO systemu.
Eksperyment ma badać OBECNY system bez jego modyfikowania.

Jeżeli dane nie wystarczają do potwierdzenia problemu,
zaproponuj eksperyment pozwalający go potwierdzić albo obalić.
"""

        elif mode is ReasoningMode.SOLUTION:
            mode_instruction = """
TRYB: POSZUKIWANIE ROZWIĄZANIA

Problem został wcześniej potwierdzony eksperymentalnie
lub dowodami.

Możesz proponować możliwe rozwiązania,
ale żadnego nie przedstawiaj jako sprawdzonego.

Oddziel propozycję od faktu.
Wskaż:
- założenia,
- słabości,
- sposób testowania,
- kryterium powodzenia.

Nie wymyślaj wyników przyszłych testów.
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

DOSTARCZONE DOWODY:
{evidence_text}

JAWNE NIEWIADOME:
{unknowns_text}

HISTORIA / KONTEKST:
{history_text}

Analizuj dokładnie ten problem.

Historia jest kontekstem, a nie automatycznym dowodem.

Nie wymyślaj brakujących danych.

Jeżeli czegoś nie da się obecnie ustalić,
pozostaw to jako niewiadomą albo granicę wnioskowania.

Nie przedstawiaj przewidywanego wyniku eksperymentu
jako wyniku rzeczywiście zaobserwowanego.

Oddziel:
- to, co wiadomo,
- to, czego nie wiadomo,
- hipotezę,
- sposób jej sprawdzenia,
- warunek pozwalający wyciągnąć wniosek,
- to, czego nawet po obecnej analizie nie wolno jeszcze uznać
  za rozstrzygnięte.

Zwrócony wynik będzie dopiero kandydatem
do dalszej weryfikacji przez FENIKSA.
"""

    def stats(self) -> dict:
        """
        Zwraca dane audytowe providera.

        Liczba prób i liczba rzeczywiście wykonanych analiz
        są celowo rozdzielone.
        """

        return {
            "modul_gotowy": True,
            "liczba_prob": self.attempt_count,
            "liczba_analiz": self.analysis_count,
            "ostatni_model": self.last_model_used,
            "ostatni_fallback": self.last_fallback_used,
            "ostatni_blad_primary": self.last_primary_error,
            "ostatni_blad_fallback": self.last_fallback_error,
        }