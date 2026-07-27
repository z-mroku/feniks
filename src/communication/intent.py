# -*- coding: utf-8 -*-

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from infrastructure.model_gateway import ModelGateway
from model_of_others.intent_hypothesis import IntentHypothesis
from perception.perception import Perception


class IntentAnalysis(BaseModel):
    """
    Ustrukturyzowana propozycja interpretacji intencji
    zwracana przez zewnętrzny model językowy.
    """

    interpretation: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    evidence: list[str]

    alternatives: list[str]

    uncertainty: Optional[str] = None


class IntentExecutionState(Enum):
    """
    Stan wykonania interpretacji intencji.

    INTERPRETED:
        Zewnętrzny model rzeczywiście zwrócił poprawną analizę
        i można było zbudować hipotezę intencji.

    UNAVAILABLE:
        Infrastruktura modelowa była chwilowo niedostępna
        i interpretacji nie wykonano.
    """

    INTERPRETED = "INTERPRETED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class IntentExecution:
    """
    Wynik wykonania warstwy interpretacji intencji.

    Obiekt rozdziela wynik poznawczy od stanu infrastruktury.

    Brak hipotezy nie oznacza:
    - braku intencji człowieka,
    - niejasnej intencji,
    - niskiej pewności,
    - braku znaczenia wypowiedzi.

    Może oznaczać wyłącznie to, że interpretacji
    nie udało się wykonać.
    """

    state: IntentExecutionState
    hypothesis: Optional[IntentHypothesis] = None

    model_used: Optional[str] = None
    fallback_used: bool = False

    primary_error: Optional[str] = None
    fallback_error: Optional[str] = None

    @property
    def interpreted(self) -> bool:
        """
        Informuje, czy rzeczywiście powstała
        hipoteza interpretacji intencji.
        """

        return (
            self.state is IntentExecutionState.INTERPRETED
            and self.hypothesis is not None
        )

    @property
    def unavailable(self) -> bool:
        """
        Informuje, czy interpretacja nie została wykonana
        z powodu niedostępności infrastruktury modelowej.
        """

        return self.state is IntentExecutionState.UNAVAILABLE


class IntentInterpreter:
    """
    Interpreter intencji FENIKSA.

    Jego zadaniem jest zaproponowanie możliwej interpretacji
    tego, czego człowiek chce lub do czego zmierza.

    Jeżeli interpretacja zostanie wykonana, jej wynikiem
    ZAWSZE pozostaje IntentHypothesis.

    Interpreter:
    - nie ogłasza intencji człowieka faktem,
    - nie odpowiada użytkownikowi,
    - nie rozwiązuje problemu,
    - nie zapisuje interpretacji jako wiedzy,
    - nie zmienia surowej wypowiedzi,
    - nie udaje interpretacji, gdy modele są niedostępne.

    Warstwa modelowa jest traktowana jako zewnętrzne
    narzędzie semantyczne, a nie jako źródło prawdy.
    """

    MODEL = "gemini-3.5-flash"
    FALLBACK_MODEL = "gemini-3.6-flash"

    SYSTEM_INSTRUCTION = """
Jesteś warstwą interpretacji intencji systemu FENIKS.

Twoim zadaniem NIE jest odpowiadanie użytkownikowi.

Masz wyłącznie zaproponować hipotezę dotyczącą tego,
co człowiek prawdopodobnie chce przekazać, osiągnąć
albo uzyskać poprzez swoją wypowiedź.

Najważniejsze zasady:

1. Intencja człowieka nie jest bezpośrednio obserwowalnym faktem.

2. Twoja interpretacja zawsze pozostaje hipotezą.

3. Nie sprowadzaj wypowiedzi wyłącznie do etykiet typu:
   QUESTION, COMMAND, CHAT, REQUEST.

4. Opisz intencję znaczeniowo i po ludzku.

5. Oddziel przesłanki obecne w wypowiedzi od własnej interpretacji.

6. Jeżeli istnieją rozsądne alternatywne interpretacje,
   wskaż je.

7. Jeżeli czegoś nie można ustalić, zachowaj tę niepewność.

8. Nie wymyślaj kontekstu, którego nie otrzymałeś.

9. Nie rozwiązuj problemu użytkownika.

10. Nie twórz odpowiedzi dla użytkownika.

11. Nie przypisuj człowiekowi stanu emocjonalnego jako faktu
    tylko dlatego, że używa wulgaryzmu, języka potocznego,
    błędów językowych, wielkich liter albo mocnej interpunkcji.

12. Nie traktuj własnej interpretacji jako dowodu
    potwierdzającego tę samą interpretację.

13. Jeżeli kontekst rozmowy został dostarczony,
    możesz go wykorzystać wyłącznie w takim zakresie,
    w jakim rzeczywiście coś wnosi do interpretacji.

14. Jeżeli dostępne dane pozwalają na kilka rozsądnych
    interpretacji, nie ukrywaj alternatyw.

Wulgaryzm, potoczność, błąd językowy lub emocjonalny sposób
wypowiedzi nie są same w sobie dowodem konkretnej intencji.

Nie poprawiaj człowieka.

Najpierw próbuj zrozumieć, co jego wypowiedź może znaczyć,
ale zachowuj granicę pomiędzy obserwacją a interpretacją.
"""

    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        gateway: Optional[ModelGateway] = None,
    ) -> None:
        """
        Tworzy interpreter intencji.

        ModelGateway odpowiada wyłącznie za techniczną politykę:

            primary -> ewentualny fallback -> wynik techniczny

        IntentInterpreter pozostaje odpowiedzialny za:
        - budowę promptu,
        - interpretację odpowiedzi modelu,
        - utworzenie IntentHypothesis,
        - zachowanie granicy pomiędzy hipotezą a faktem.
        """

        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError(
                "Brak GEMINI_API_KEY w środowisku."
            )

        self.model = model or self.MODEL

        self.fallback_model = (
            fallback_model or self.FALLBACK_MODEL
        )

        self.client = genai.Client()

        self.gateway = (
            gateway
            if gateway is not None
            else ModelGateway()
        )

        self.last_model_used: Optional[str] = None
        self.last_fallback_used: bool = False

        self.last_primary_error: Optional[str] = None
        self.last_fallback_error: Optional[str] = None

        # Liczba wszystkich prób interpretacji,
        # niezależnie od tego, czy infrastruktura
        # pozwoliła uzyskać wynik.
        self.attempt_count = 0

        # Liczba interpretacji zakończonych
        # rzeczywistym wynikiem poznawczym.
        self.analysis_count = 0

    def interpret(
        self,
        perception: Perception,
        conversation_context: Optional[list[str]] = None,
    ) -> IntentExecution:
        """
        Próbuje zinterpretować intencję człowieka.

        Metoda rozdziela:

        1. próbę wykonania interpretacji,
        2. stan infrastruktury,
        3. rzeczywiście powstałą hipotezę poznawczą.

        Jeżeli model podstawowy zwróci błąd 503,
        ModelGateway może użyć modelu zapasowego.

        Jeżeli również model zapasowy jest niedostępny,
        zwracany jest stan UNAVAILABLE.

        W takim przypadku NIE powstaje sztuczna
        IntentHypothesis.
        """

        if not isinstance(perception, Perception):
            raise TypeError(
                "IntentInterpreter oczekuje obiektu Perception."
            )

        if conversation_context is None:
            context: list[str] = []

        else:
            if not isinstance(conversation_context, list):
                raise TypeError(
                    "conversation_context musi być listą tekstów."
                )

            if not all(
                isinstance(item, str)
                for item in conversation_context
            ):
                raise TypeError(
                    "Każdy element conversation_context "
                    "musi być tekstem."
                )

            context = list(conversation_context)

        prompt = self._build_prompt(
            perception=perception,
            conversation_context=context,
        )

        self.attempt_count += 1

        # Stan ostatniego wywołania jest zerowany przed
        # każdą nową próbą, aby poprzedni wynik nie został
        # przypadkowo uznany za stan bieżącego wykonania.
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

        self.last_primary_error = (
            gateway_result.primary_error
        )

        self.last_fallback_error = (
            gateway_result.fallback_error
        )

        if gateway_result.unavailable:
            return IntentExecution(
                state=IntentExecutionState.UNAVAILABLE,
                hypothesis=None,
                model_used=None,
                fallback_used=gateway_result.fallback_used,
                primary_error=gateway_result.primary_error,
                fallback_error=gateway_result.fallback_error,
            )

        if not gateway_result.succeeded:
            raise RuntimeError(
                "ModelGateway zwrócił nierozpoznany stan "
                "wykonania interpretacji intencji."
            )

        if gateway_result.text is None:
            raise RuntimeError(
                "ModelGateway zgłosił sukces bez treści "
                "interpretacji intencji."
            )

        analysis = IntentAnalysis.model_validate_json(
            gateway_result.text
        )

        interpretation = analysis.interpretation.strip()

        if not interpretation:
            raise RuntimeError(
                "Model zwrócił pustą interpretację intencji."
            )

        evidence = tuple(
            item.strip()
            for item in analysis.evidence
            if item.strip()
        )

        alternatives = tuple(
            item.strip()
            for item in analysis.alternatives
            if item.strip()
        )

        uncertainty = (
            analysis.uncertainty.strip()
            if analysis.uncertainty
            and analysis.uncertainty.strip()
            else None
        )

        hypothesis = IntentHypothesis(
            interpretation=interpretation,
            confidence=analysis.confidence,
            evidence=evidence,
            alternatives=alternatives,
            uncertainty=uncertainty,
        )

        # Dopiero w tym miejscu można uczciwie powiedzieć,
        # że powstał wynik interpretacji.
        self.analysis_count += 1

        return IntentExecution(
            state=IntentExecutionState.INTERPRETED,
            hypothesis=hypothesis,
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
        Wykonuje pojedyncze wywołanie konkretnego modelu.

        Ta metoda:
        - nie wybiera fallbacku,
        - nie interpretuje błędu 503,
        - nie tworzy IntentHypothesis,
        - nie podejmuje decyzji poznawczej.

        Polityka dostępności modeli należy do ModelGateway.
        """

        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=IntentAnalysis,
                temperature=0.2,
            ),
        )

        if not response.text:
            raise RuntimeError(
                f"Gemini ({model}) nie zwróciło "
                "analizy intencji."
            )

        return response.text

    def _build_prompt(
        self,
        perception: Perception,
        conversation_context: list[str],
    ) -> str:
        """
        Buduje dane wejściowe dla semantycznej
        interpretacji intencji.

        Surowa wypowiedź pozostaje niezmieniona.
        """

        if conversation_context:
            context_text = "\n".join(
                f"- {item}"
                for item in conversation_context
            )

        else:
            context_text = (
                "- BRAK DODATKOWEGO KONTEKSTU ROZMOWY"
            )

        return f"""
SUROWA WYPOWIEDŹ:
{perception.raw_content}

MODALNOŚĆ:
{perception.modality}

ŹRÓDŁO:
{perception.source}

KONTEKST ROZMOWY:
{context_text}

Zaproponuj najbardziej uzasadnioną hipotezę
dotyczącą intencji człowieka.

W polu interpretation opisz możliwą intencję człowieka.
Nie przedstawiaj jej jako pewnego faktu.

W polu confidence określ stopień pewności interpretacji
w zakresie od 0.0 do 1.0.

W polu evidence podaj wyłącznie przesłanki,
które rzeczywiście wynikają z wypowiedzi
lub dostarczonego kontekstu.

Nie wpisuj do evidence własnych domysłów dotyczących
emocji, charakteru, historii człowieka ani innych
informacji, których nie ma w dostarczonych danych.

W alternatives zachowaj inne rozsądne możliwości
interpretacji, jeżeli istnieją.

W uncertainty zapisz istotną granicę interpretacji,
jeżeli taka istnieje.

Nie odpowiadaj człowiekowi.
Nie rozwiązuj jego problemu.
Nie przedstawiaj swojej interpretacji jako faktu.
Nie wymyślaj brakującego kontekstu.
"""

    def stats(self) -> dict:
        """
        Zwraca stan samoobserwacji interpretera intencji.

        Liczba prób jest oddzielona od liczby rzeczywiście
        wykonanych analiz.
        """

        return {
            "modul_gotowy": True,
            "liczba_prob_interpretacji":
                self.attempt_count,
            "liczba_analiz_intencji":
                self.analysis_count,
            "ostatni_model":
                self.last_model_used,
            "ostatni_fallback":
                self.last_fallback_used,
            "ostatni_blad_primary":
                self.last_primary_error,
            "ostatni_blad_fallback":
                self.last_fallback_error,
            "gateway":
                self.gateway.stats(),
        }