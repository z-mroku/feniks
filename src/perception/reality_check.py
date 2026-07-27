import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from infrastructure.model_gateway import (
    ModelCallState,
    ModelGateway,
)
from model_of_others.intent_hypothesis import IntentHypothesis
from perception.perception import Perception


class EvidenceStatus(Enum):
    """
    Określa relację pomiędzy twierdzeniem przedstawionym
    jako przesłanka a rzeczywiście dostępnymi danymi.
    """

    GROUNDED = "UGRUNTOWANE"
    INFERENCE = "WNIOSKOWANIE"
    UNSUPPORTED = "NIEUZASADNIONE"


class EvidenceAssessment(BaseModel):
    """
    Struktura pojedynczej oceny zwracanej przez
    zewnętrzną warstwę modelową.

    Jest to jeszcze wynik technicznej interpretacji
    odpowiedzi modelu, a nie trwała wiedza FENIKSA.
    """

    evidence: str

    status: str

    explanation: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class RealityCheckAnalysis(BaseModel):
    """
    Strukturalna odpowiedź modelu wykonującego
    kontrolę przesłanek.
    """

    assessments: list[EvidenceAssessment]


@dataclass(frozen=True)
class CheckedEvidence:
    """
    Wynik rzeczywiście wykonanej kontroli
    pojedynczej przesłanki.
    """

    evidence: str
    status: EvidenceStatus
    explanation: str
    confidence: float


@dataclass(frozen=True)
class RealityCheckResult:
    """
    Wynik rzeczywiście wykonanej kontroli hipotezy
    względem surowego wejścia.

    Istnienie tego obiektu oznacza, że kontrola
    rzeczywiście została przeprowadzona.

    Nie rozstrzyga, czy sama hipoteza intencji
    jest prawdziwa.

    Sprawdza wyłącznie, czy przesłanki używane
    do jej budowy są uczciwie opisane jako:

    - ugruntowane,
    - wnioskowanie,
    - nieuzasadnione.
    """

    hypothesis: IntentHypothesis
    evidence: tuple[CheckedEvidence, ...]

    @property
    def grounded(self) -> tuple[CheckedEvidence, ...]:
        return tuple(
            item
            for item in self.evidence
            if item.status is EvidenceStatus.GROUNDED
        )

    @property
    def inferences(self) -> tuple[CheckedEvidence, ...]:
        return tuple(
            item
            for item in self.evidence
            if item.status is EvidenceStatus.INFERENCE
        )

    @property
    def unsupported(self) -> tuple[CheckedEvidence, ...]:
        return tuple(
            item
            for item in self.evidence
            if item.status is EvidenceStatus.UNSUPPORTED
        )


class RealityCheckExecutionState(Enum):
    """
    Stan wykonania kontroli rzeczywistości.

    CHECKED:
        Kontrola została rzeczywiście wykonana
        i istnieje jej wynik poznawczy.

    UNAVAILABLE:
        Kontrola nie została wykonana, ponieważ
        zewnętrzna warstwa modelowa była chwilowo
        niedostępna.

    UNAVAILABLE nie jest wynikiem poznawczym.
    Nie oznacza ani potwierdzenia, ani odrzucenia
    żadnej przesłanki.
    """

    CHECKED = "CHECKED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class RealityCheckExecution:
    """
    Koperta wykonania RealityCheck.

    Oddziela stan infrastruktury od wyniku poznawczego.

    Dzięki temu brak dostępu do modelu nie może zostać
    pomylony z rzeczywiście wykonaną kontrolą.

    Jeżeli state == CHECKED:
        result zawiera RealityCheckResult.

    Jeżeli state == UNAVAILABLE:
        result musi pozostać None.
    """

    state: RealityCheckExecutionState
    result: Optional[RealityCheckResult] = None

    model_used: Optional[str] = None
    fallback_used: bool = False

    primary_error: Optional[str] = None
    fallback_error: Optional[str] = None

    @property
    def checked(self) -> bool:
        return (
            self.state
            is RealityCheckExecutionState.CHECKED
        )

    @property
    def unavailable(self) -> bool:
        return (
            self.state
            is RealityCheckExecutionState.UNAVAILABLE
        )


class RealityCheck:
    """
    Kontrola zgodności interpretacji z rzeczywistym wejściem.

    RealityCheck nie ustala intencji człowieka.
    Nie tworzy odpowiedzi.
    Nie rozwiązuje problemu.
    Nie zapisuje wiedzy.

    Jego zadaniem jest pilnowanie granicy pomiędzy:

    - tym, co rzeczywiście znajduje oparcie w danych,
    - tym, co jest wnioskowaniem,
    - tym, czego dane nie uzasadniają.

    Dostępność modeli zewnętrznych jest problemem
    infrastrukturalnym i jest obsługiwana przez
    ModelGateway.

    Awaria modeli nie może zostać przedstawiona
    jako wynik kontroli rzeczywistości.
    """

    MODEL = "gemini-3.5-flash"
    FALLBACK_MODEL = "gemini-3.6-flash"

    SYSTEM_INSTRUCTION = """
Jesteś mechanizmem kontroli rzeczywistości systemu FENIKS.

Otrzymujesz:
1. surową wypowiedź człowieka,
2. kontekst rozmowy, jeśli został dostarczony,
3. listę twierdzeń przedstawionych jako evidence
   dla hipotezy dotyczącej intencji człowieka.

Nie ustalaj ponownie intencji użytkownika.

Dla każdego elementu evidence określ jego relację
z rzeczywiście dostępnymi danymi.

Dozwolone statusy:

UGRUNTOWANE
- treść rzeczywiście wynika bezpośrednio z wypowiedzi
  lub jawnie dostarczonego kontekstu.

WNIOSKOWANIE
- treść może być rozsądną interpretacją danych,
  ale nie jest bezpośrednio obserwowalnym faktem.

NIEUZASADNIONE
- treść wprowadza informację, której wypowiedź
  ani dostarczony kontekst nie uzasadniają.

Przykład:

Surowe:
"kurde, nie chcę kolejnego głupiego chatbota"

UGRUNTOWANE:
użytkownik użył słowa "kurde".

WNIOSKOWANIE:
użytkownik może być sfrustrowany.

NIEUZASADNIONE:
użytkownik od trzech dni jest sfrustrowany projektem.

Nie traktuj tonu, wulgaryzmu, znaków interpunkcyjnych
ani stylu wypowiedzi jako bezpośredniego dowodu
wewnętrznego stanu człowieka.

Nie poprawiaj dowodów.
Nie twórz nowych dowodów.
Masz je wyłącznie sklasyfikować i wyjaśnić dlaczego.
"""

    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
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
        self.gateway = ModelGateway()

        # Jawny stan ostatniej próby wykonania kontroli.
        # Służy do audytu i samoobserwacji.
        self.last_model_used: Optional[str] = None
        self.last_fallback_used: bool = False
        self.last_primary_error: Optional[str] = None
        self.last_fallback_error: Optional[str] = None

        # Liczy wyłącznie kontrole rzeczywiście wykonane.
        # Niedostępność modeli nie zwiększa tego licznika.
        self.check_count = 0

        # Liczy wszystkie próby uruchomienia RealityCheck,
        # również te zakończone niedostępnością modeli.
        self.attempt_count = 0

    def check(
        self,
        perception: Perception,
        hypothesis: IntentHypothesis,
        conversation_context: Optional[list[str]] = None,
    ) -> RealityCheckExecution:
        """
        Próbuje wykonać kontrolę przesłanek hipotezy.

        Metoda zawsze rozróżnia:

        1. rzeczywiście wykonaną kontrolę,
        2. brak możliwości wykonania kontroli z powodu
           chwilowej niedostępności modeli.

        Niedostępność infrastruktury nie jest zamieniana
        na sztuczny wynik poznawczy.
        """

        if not isinstance(perception, Perception):
            raise TypeError(
                "RealityCheck oczekuje obiektu Perception."
            )

        if not isinstance(hypothesis, IntentHypothesis):
            raise TypeError(
                "RealityCheck oczekuje obiektu IntentHypothesis."
            )

        context = conversation_context or []

        prompt = self._build_prompt(
            perception=perception,
            hypothesis=hypothesis,
            conversation_context=context,
        )

        self.attempt_count += 1

        self.last_model_used = None
        self.last_fallback_used = False
        self.last_primary_error = None
        self.last_fallback_error = None

        call = self.gateway.execute(
            primary_model=self.model,
            fallback_model=self.fallback_model,
            generate=lambda model: self._generate(
                model=model,
                prompt=prompt,
            ),
        )

        self.last_model_used = call.model_used
        self.last_fallback_used = call.fallback_used
        self.last_primary_error = call.primary_error
        self.last_fallback_error = call.fallback_error

        if call.state is ModelCallState.UNAVAILABLE:
            return RealityCheckExecution(
                state=RealityCheckExecutionState.UNAVAILABLE,
                result=None,
                model_used=None,
                fallback_used=call.fallback_used,
                primary_error=call.primary_error,
                fallback_error=call.fallback_error,
            )

        if call.state is not ModelCallState.SUCCESS:
            raise RuntimeError(
                "ModelGateway zwrócił nieobsługiwany stan "
                "wykonania."
            )

        if call.text is None:
            raise RuntimeError(
                "ModelGateway zgłosił sukces bez treści "
                "odpowiedzi."
            )

        analysis = RealityCheckAnalysis.model_validate_json(
            call.text
        )

        checked = tuple(
            CheckedEvidence(
                evidence=item.evidence,
                status=EvidenceStatus(item.status),
                explanation=item.explanation,
                confidence=item.confidence,
            )
            for item in analysis.assessments
        )

        result = RealityCheckResult(
            hypothesis=hypothesis,
            evidence=checked,
        )

        # Dopiero tutaj kontrola została rzeczywiście
        # wykonana i jej wynik poprawnie zwalidowany.
        self.check_count += 1

        return RealityCheckExecution(
            state=RealityCheckExecutionState.CHECKED,
            result=result,
            model_used=call.model_used,
            fallback_used=call.fallback_used,
            primary_error=call.primary_error,
            fallback_error=call.fallback_error,
        )

    def _generate(
        self,
        model: str,
        prompt: str,
    ) -> str:
        """
        Wykonuje pojedyncze wywołanie konkretnego modelu.

        Ta metoda nie realizuje polityki fallback.
        Za wybór modelu i obsługę chwilowej niedostępności
        odpowiada ModelGateway.
        """

        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RealityCheckAnalysis,
                temperature=0.1,
            ),
        )

        if not response.text:
            raise RuntimeError(
                f"Gemini ({model}) nie zwróciło "
                "kontroli rzeczywistości."
            )

        return response.text

    def _build_prompt(
        self,
        perception: Perception,
        hypothesis: IntentHypothesis,
        conversation_context: list[str],
    ) -> str:
        """
        Buduje dane wejściowe dla kontroli rzeczywistości.

        Kontekst rozmowy jest materiałem wejściowym,
        a nie automatycznym dowodem prawdziwości
        hipotezy intencji.
        """

        context_text = (
            "\n".join(
                f"- {item}"
                for item in conversation_context
            )
            if conversation_context
            else "- BRAK DODATKOWEGO KONTEKSTU"
        )

        evidence_text = (
            "\n".join(
                f"- {item}"
                for item in hypothesis.evidence
            )
            if hypothesis.evidence
            else "- BRAK PRZESŁANEK DO OCENY"
        )

        return f"""
SUROWA WYPOWIEDŹ:
{perception.raw_content}

KONTEKST:
{context_text}

HIPOTEZA INTENCJI:
{hypothesis.interpretation}

PRZESŁANKI DO SPRAWDZENIA:
{evidence_text}

Sprawdź każdą przesłankę oddzielnie.

Nie oceniaj, czy hipoteza intencji jest prawdziwa.
Nie dodawaj nowych przesłanek.
Nie poprawiaj istniejących.

Dla każdej użyj dokładnie jednego statusu:

UGRUNTOWANE
WNIOSKOWANIE
NIEUZASADNIONE
"""

    def stats(self) -> dict:
        """
        Zwraca jawny stan RealityCheck do samoobserwacji.

        Rozróżnia liczbę prób od liczby rzeczywiście
        wykonanych kontroli.
        """

        return {
            "modul_gotowy": True,
            "liczba_prob": self.attempt_count,
            "liczba_kontroli": self.check_count,
            "ostatni_model": self.last_model_used,
            "ostatni_fallback": self.last_fallback_used,
            "ostatni_blad_primary": self.last_primary_error,
            "ostatni_blad_fallback": self.last_fallback_error,
            "gateway": self.gateway.stats(),
        }