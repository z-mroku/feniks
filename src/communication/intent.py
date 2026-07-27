import os
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import ServerError
from pydantic import BaseModel, Field

from perception.perception import Perception
from model_of_others.intent_hypothesis import IntentHypothesis


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


class IntentInterpreter:
    """
    Interpreter intencji FENIKSA.

    Jego zadaniem jest zaproponowanie możliwej interpretacji
    tego, czego człowiek chce lub do czego zmierza.

    Wynik ZAWSZE pozostaje IntentHypothesis.

    Interpreter:
    - nie ogłasza intencji człowieka faktem,
    - nie odpowiada użytkownikowi,
    - nie rozwiązuje problemu,
    - nie zapisuje interpretacji jako wiedzy,
    - nie zmienia surowej wypowiedzi.
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
6. Jeśli istnieją rozsądne alternatywne interpretacje, wskaż je.
7. Jeśli czegoś nie można ustalić, zachowaj tę niepewność.
8. Nie wymyślaj kontekstu, którego nie otrzymałeś.
9. Nie rozwiązuj problemu użytkownika.
10. Nie twórz odpowiedzi dla użytkownika.

Wulgaryzm, potoczność, błąd językowy lub emocjonalny sposób
wypowiedzi nie są same w sobie dowodem konkretnej intencji.

Nie poprawiaj człowieka.
Najpierw próbuj zrozumieć, co jego wypowiedź może znaczyć.
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

        self.last_model_used: Optional[str] = None
        self.last_fallback_used = False
        self.last_primary_error: Optional[str] = None
        self.analysis_count = 0

    def interpret(
        self,
        perception: Perception,
        conversation_context: Optional[list[str]] = None,
    ) -> IntentHypothesis:

        if not isinstance(perception, Perception):
            raise TypeError(
                "IntentInterpreter oczekuje obiektu Perception."
            )

        context = conversation_context or []

        prompt = self._build_prompt(
            perception=perception,
            conversation_context=context,
        )

        self.last_model_used = None
        self.last_fallback_used = False
        self.last_primary_error = None

        try:
            text = self._generate(
                self.model,
                prompt,
            )
            self.last_model_used = self.model

        except ServerError as exc:
            if getattr(exc, "code", None) != 503:
                raise

            self.last_primary_error = str(exc)

            text = self._generate(
                self.fallback_model,
                prompt,
            )

            self.last_model_used = self.fallback_model
            self.last_fallback_used = True

        analysis = IntentAnalysis.model_validate_json(text)

        self.analysis_count += 1

        return IntentHypothesis(
            interpretation=analysis.interpretation,
            confidence=analysis.confidence,
            evidence=tuple(analysis.evidence),
            alternatives=tuple(analysis.alternatives),
            uncertainty=analysis.uncertainty,
        )

    def _generate(
        self,
        model: str,
        prompt: str,
    ) -> str:

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
                f"Gemini ({model}) nie zwróciło analizy intencji."
            )

        return response.text

    def _build_prompt(
        self,
        perception: Perception,
        conversation_context: list[str],
    ) -> str:

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

W polu evidence podaj wyłącznie przesłanki,
które rzeczywiście wynikają z wypowiedzi
lub dostarczonego kontekstu.

W alternatives zachowaj inne rozsądne możliwości.

W uncertainty zapisz istotną granicę interpretacji,
jeżeli taka istnieje.

Nie odpowiadaj człowiekowi.
Nie rozwiązuj jego problemu.
Nie przedstawiaj swojej interpretacji jako faktu.
"""

    def stats(self) -> dict:
        return {
            "modul_gotowy": True,
            "liczba_analiz_intencji": self.analysis_count,
            "ostatni_model": self.last_model_used,
            "ostatni_fallback": self.last_fallback_used,
        }