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
    INCONCLUSIVE = "NIEROZSTRZYGNIĘTA"


class ExperimentInterpretation(BaseModel):
    """
    Interpretacja rzeczywistego eksperymentu.

    Model językowy interpretuje dane,
    ale nie może ich zmieniać.
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
    Interpretuje wyniki eksperymentów FENIKSA
    przy pomocy Gemini.

    WAŻNE:

    Gemini nie wykonuje eksperymentu.
    Gemini nie tworzy obserwacji.
    Gemini nie może zmieniać wyników.

    Otrzymuje wyłącznie dane zmierzone
    przez ExperimentRunner i próbuje
    wyciągnąć z nich ostrożne wnioski.
    """

    MODEL = "gemini-3.5-flash"

    SYSTEM_INSTRUCTION = """
Jesteś zewnętrzną warstwą interpretacji eksperymentów
systemu FENIKS.

Otrzymujesz:

1. hipotezę postawioną PRZED eksperymentem,
2. rzeczywiste obserwacje wygenerowane przez program,
3. dodatkowe ustalenia obliczone przez program.

Twoim zadaniem jest interpretacja tych danych.

Hierarchia wiarygodności:

RZECZYWISTE OBSERWACJE PROGRAMU
mają pierwszeństwo przed
HIPOTEZĄ MODELU.

Nie wolno ci:

- zmieniać wartości obserwacji,
- wymyślać brakujących wyników,
- twierdzić, że wykonano test, którego nie wykonano,
- dopasowywać danych do wcześniejszej hipotezy,
- przedstawiać hipotezy jako faktu,
- proponować naprawy przed ustaleniem natury problemu,
- wymyślać arbitralnych progów liczbowych.

Jeżeli dane przeczą hipotezie, masz to jawnie powiedzieć.

Jeżeli eksperyment nie wystarcza do rozstrzygnięcia hipotezy,
oznacz ją jako NIEROZSTRZYGNIĘTĄ.

Jeżeli eksperyment ujawnia inne zjawisko niż to,
którego oczekiwano, oddziel:

- wynik dotyczący pierwotnej hipotezy,
- nowe nieoczekiwane ustalenie.

Następny eksperyment powinien służyć poznaniu przyczyny
zaobserwowanego zachowania.

Nie projektuj jeszcze naprawy systemu.

Najpierw diagnoza.
Potem przyczyna.
Dopiero później rozwiązanie.
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
    ) -> ExperimentInterpretation:
        """
        Interpretuje wykonany eksperyment.
        """

        prompt = self._build_prompt(
            hypothesis=hypothesis,
            result=result,
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
                "Gemini nie zwróciło interpretacji eksperymentu."
            )

        return ExperimentInterpretation.model_validate_json(
            response.text
        )

    def _build_prompt(
        self,
        hypothesis: str,
        result: ExperimentResult,
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
            else "NIE WYSTĄPIŁA"
        )

        first_opposition_stronger = (
            str(result.first_opposition_stronger_at)
            if result.first_opposition_stronger_at is not None
            else "NIE WYSTĄPIŁ"
        )

        return f"""
HIPOTEZA POSTAWIONA PRZED EKSPERYMENTEM:

{hypothesis}


NAZWA EKSPERYMENTU:

{result.name}


RZECZYWISTE OBSERWACJE PROGRAMU:

{observations_text}


USTALENIA OBLICZONE PRZEZ PROGRAM:

Pierwsza wykryta sprzeczność:
N={first_contradiction}

Pierwszy moment, gdy siła sprzeciwu
przewyższyła siłę poparcia:
N={first_opposition_stronger}

Maksymalne przebadane N:
{result.maximum_n_tested}


ZADANIE:

1. Oceń status pierwotnej hipotezy.

2. Wyjaśnij ocenę WYŁĄCZNIE na podstawie
   dostarczonych wyników.

3. Wskaż nowe ustalenia wynikające
   bezpośrednio z obserwacji.

4. Oddziel niewiadome od faktów.

5. Jeżeli istnieją różne możliwe wyjaśnienia
   zachowania systemu, wymień je jako
   alternatywne wyjaśnienia, a nie fakty.

6. Zaproponuj następne pytanie eksperymentalne.

7. Zaproponuj następny eksperyment,
   który pomoże ustalić PRZYCZYNĘ zachowania.

8. NIE PROPONUJ JESZCZE NAPRAWY ALGORYTMU.
"""