from enum import Enum
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from core.experiment_runner import ExperimentResult


class HypothesisStatus(Enum):
    """
    Status hipotezy po wykonaniu eksperymentu.
    """

    CONFIRMED = "POTWIERDZONA"
    REJECTED = "OBALONA"
    INCONCLUSIVE = "NIEROZSTRZYGNIÄTA"


class ExperimentInterpretation(BaseModel):
    """
    Interpretacja rzeczywistego eksperymentu.

    Model jÄ™zykowy interpretuje dane,
    ale nie moĹĽe ich zmieniaÄ‡.
    """

    hypothesis_status: HypothesisStatus

    reasoning: str

    new_findings: list[str]

    remaining_unknowns: list[str]

    alternative_explanations: list[str]

    next_experiment_question: str

    next_experiment: str

    cannot_conclude_yet: list[str]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class GeminiExperimentInterpreter:
    """
    Interpretuje wyniki eksperymentĂłw FENIKSA
    przy pomocy Gemini.

    WAĹ»NE:

    Gemini nie wykonuje eksperymentu.
    Gemini nie tworzy obserwacji.
    Gemini nie moĹĽe zmieniaÄ‡ wynikĂłw.

    Otrzymuje wyĹ‚Ä…cznie dane zmierzone
    przez ExperimentRunner i prĂłbuje
    wyciÄ…gnÄ…Ä‡ z nich ostroĹĽne wnioski.
    """

    MODEL = "gemini-3.5-flash"
    supports_prior_knowledge_context = True

    SYSTEM_INSTRUCTION = """
JesteĹ› zewnÄ™trznÄ… warstwÄ… interpretacji eksperymentĂłw
systemu FENIKS.

Otrzymujesz:

1. hipotezÄ™ postawionÄ… PRZED eksperymentem,
2. rzeczywiste obserwacje wygenerowane przez program,
3. dodatkowe ustalenia obliczone przez program.

Twoim zadaniem jest interpretacja tych danych.

Hierarchia wiarygodnoĹ›ci:

RZECZYWISTE OBSERWACJE PROGRAMU
majÄ… pierwszeĹ„stwo przed
HIPOTEZÄ„ MODELU.

Nie wolno ci:

- zmieniaÄ‡ wartoĹ›ci obserwacji,
- wymyĹ›laÄ‡ brakujÄ…cych wynikĂłw,
- twierdziÄ‡, ĹĽe wykonano test, ktĂłrego nie wykonano,
- dopasowywaÄ‡ danych do wczeĹ›niejszej hipotezy,
- przedstawiaÄ‡ hipotezy jako faktu,
- proponowaÄ‡ naprawy przed ustaleniem natury problemu,
- wymyĹ›laÄ‡ arbitralnych progĂłw liczbowych.

JeĹĽeli dane przeczÄ… hipotezie, masz to jawnie powiedzieÄ‡.

JeĹĽeli eksperyment nie wystarcza do rozstrzygniÄ™cia hipotezy,
oznacz jÄ… jako NIEROZSTRZYGNIÄTÄ„.

JeĹĽeli eksperyment ujawnia inne zjawisko niĹĽ to,
ktĂłrego oczekiwano, oddziel:

- wynik dotyczÄ…cy pierwotnej hipotezy,
- nowe nieoczekiwane ustalenie.

NastÄ™pny eksperyment powinien sĹ‚uĹĽyÄ‡ poznaniu przyczyny
zaobserwowanego zachowania.

Nie projektuj jeszcze naprawy systemu.

Najpierw diagnoza.
Potem przyczyna.
Dopiero pĂłĹşniej rozwiÄ…zanie.
"""

    def __init__(
        self,
        model: Optional[str] = None,
    ):
        self.model = model or self.MODEL
        self.client = genai.Client()

    def interpret(
        self,
        hypothesis: str,
        result: ExperimentResult,
        prior_knowledge_context: str = "",
    ) -> ExperimentInterpretation:
        """
        Interpretuje wykonany eksperyment.
        """

        prompt = self._build_prompt(
            hypothesis=hypothesis,
            result=result,
            prior_knowledge_context=prior_knowledge_context,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=ExperimentInterpretation,
                temperature=0.1,
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini nie zwrĂłciĹ‚o interpretacji eksperymentu."
            )

        return ExperimentInterpretation.model_validate_json(
            response.text
        )

    def _build_prompt(
        self,
        hypothesis: str,
        result: ExperimentResult,
        prior_knowledge_context: str = "",
    ) -> str:
        """
        Buduje zapis eksperymentu na podstawie
        rzeczywistych obserwacji programu.
        """

        observation_lines = []

        for observation in result.observations:
            observation_lines.append(
                (
                    f"N={observation.n_opposing}; "
                    f"klasyfikacja="
                    f"{observation.classification.value}; "
                    f"poparcie="
                    f"{observation.support_strength:.4f}; "
                    f"sprzeciw="
                    f"{observation.opposition_strength:.4f}; "
                    f"pewnosc="
                    f"{observation.classification_confidence:.4f}; "
                    f"sprzecznosc="
                    f"{observation.contradiction_detected}"
                )
            )

        observations_text = "\n".join(
            observation_lines
        )

        first_contradiction = (
            str(result.first_contradiction_at)
            if result.first_contradiction_at is not None
            else "NIE WYSTÄ„PIĹA"
        )

        first_opposition_stronger = (
            str(result.first_opposition_stronger_at)
            if result.first_opposition_stronger_at is not None
            else "NIE WYSTÄ„PIĹ"
        )

        prior_knowledge_context = prior_knowledge_context.strip()

        if prior_knowledge_context:
            prior_knowledge_section = f"""
WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA FENIKSA
(KONTEKST POMOCNICZY — NIE WYNIK BIEŻĄCEGO EKSPERYMENTU):

{prior_knowledge_context}

WAŻNE:
- ta sekcja nie jest nową obserwacją,
- nie może automatycznie rozstrzygać hipotezy,
- przy sprzeczności pierwszeństwo mają bieżące obserwacje programu.
"""
        else:
            prior_knowledge_section = """
WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA FENIKSA:

Brak wcześniejszej wiedzy dobranej do tego problemu.
"""

        return f"""
HIPOTEZA POSTAWIONA PRZED EKSPERYMENTEM:

{hypothesis}

{prior_knowledge_section}

NAZWA EKSPERYMENTU:

{result.name}


RZECZYWISTE OBSERWACJE PROGRAMU:

{observations_text}


USTALENIA OBLICZONE PRZEZ PROGRAM:

Pierwsza wykryta sprzecznoĹ›Ä‡:
N={first_contradiction}

Pierwszy moment, gdy siĹ‚a sprzeciwu
przewyĹĽszyĹ‚a siĹ‚Ä™ poparcia:
N={first_opposition_stronger}

Maksymalne przebadane N:
{result.maximum_n_tested}


ZADANIE:

1. OceĹ„ status pierwotnej hipotezy.

2. WyjaĹ›nij ocenÄ™ WYĹÄ„CZNIE na podstawie
   dostarczonych wynikĂłw.

3. WskaĹĽ nowe ustalenia wynikajÄ…ce
   bezpoĹ›rednio z obserwacji.

4. Oddziel niewiadome od faktĂłw.

5. JeĹĽeli istniejÄ… rĂłĹĽne moĹĽliwe wyjaĹ›nienia
   zachowania systemu, wymieĹ„ je jako
   alternatywne wyjaĹ›nienia, a nie fakty.

6. Zaproponuj nastÄ™pne pytanie eksperymentalne.

7. Zaproponuj nastÄ™pny eksperyment,
   ktĂłry pomoĹĽe ustaliÄ‡ PRZYCZYNÄ zachowania.

8. NIE PROPONUJ JESZCZE NAPRAWY ALGORYTMU.
"""
