from enum import Enum
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import ServerError
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

    Model jĂ„â„˘zykowy interpretuje dane,
    ale nie moÄąÄ˝e ich zmieniaĂ„â€ˇ.
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
    Interpretuje wyniki eksperymentÄ‚Ĺ‚w FENIKSA
    przy pomocy Gemini.

    WAÄąÂ»NE:

    Gemini nie wykonuje eksperymentu.
    Gemini nie tworzy obserwacji.
    Gemini nie moÄąÄ˝e zmieniaĂ„â€ˇ wynikÄ‚Ĺ‚w.

    Otrzymuje wyÄąâ€šĂ„â€¦cznie dane zmierzone
    przez ExperimentRunner i prÄ‚Ĺ‚buje
    wyciĂ„â€¦gnĂ„â€¦Ă„â€ˇ z nich ostroÄąÄ˝ne wnioski.
    """

    MODEL = "gemini-3.5-flash"
    FALLBACK_MODEL = "gemini-3.6-flash"
    supports_prior_knowledge_context = True

    SYSTEM_INSTRUCTION = """
JesteÄąâ€ş zewnĂ„â„˘trznĂ„â€¦ warstwĂ„â€¦ interpretacji eksperymentÄ‚Ĺ‚w
systemu FENIKS.

Otrzymujesz:

1. hipotezĂ„â„˘ postawionĂ„â€¦ PRZED eksperymentem,
2. rzeczywiste obserwacje wygenerowane przez program,
3. dodatkowe ustalenia obliczone przez program.

Twoim zadaniem jest interpretacja tych danych.

Hierarchia wiarygodnoÄąâ€şci:

RZECZYWISTE OBSERWACJE PROGRAMU
majĂ„â€¦ pierwszeÄąâ€žstwo przed
HIPOTEZĂ„â€ž MODELU.

Nie wolno ci:

- zmieniaĂ„â€ˇ wartoÄąâ€şci obserwacji,
- wymyÄąâ€şlaĂ„â€ˇ brakujĂ„â€¦cych wynikÄ‚Ĺ‚w,
- twierdziĂ„â€ˇ, ÄąÄ˝e wykonano test, ktÄ‚Ĺ‚rego nie wykonano,
- dopasowywaĂ„â€ˇ danych do wczeÄąâ€şniejszej hipotezy,
- przedstawiaĂ„â€ˇ hipotezy jako faktu,
- proponowaĂ„â€ˇ naprawy przed ustaleniem natury problemu,
- wymyÄąâ€şlaĂ„â€ˇ arbitralnych progÄ‚Ĺ‚w liczbowych.

JeÄąÄ˝eli dane przeczĂ„â€¦ hipotezie, masz to jawnie powiedzieĂ„â€ˇ.

JeÄąÄ˝eli eksperyment nie wystarcza do rozstrzygniĂ„â„˘cia hipotezy,
oznacz jĂ„â€¦ jako NIEROZSTRZYGNIĂ„ÂTĂ„â€ž.

JeÄąÄ˝eli eksperyment ujawnia inne zjawisko niÄąÄ˝ to,
ktÄ‚Ĺ‚rego oczekiwano, oddziel:

- wynik dotyczĂ„â€¦cy pierwotnej hipotezy,
- nowe nieoczekiwane ustalenie.

NastĂ„â„˘pny eksperyment powinien sÄąâ€šuÄąÄ˝yĂ„â€ˇ poznaniu przyczyny
zaobserwowanego zachowania.

Nie projektuj jeszcze naprawy systemu.

Najpierw diagnoza.
Potem przyczyna.
Dopiero pÄ‚Ĺ‚ÄąĹźniej rozwiĂ„â€¦zanie.
"""

    def __init__(
        self,
        model: Optional[str] = None,
        fallback_model: Optional[str] = None,
    ):
        self.model = model or self.MODEL
        self.fallback_model = fallback_model or self.FALLBACK_MODEL
        self.client = genai.Client()

        # Jawny stan ostatniego wywołania — do audytu i samoobserwacji.
        self.last_model_used: Optional[str] = None
        self.last_fallback_used: bool = False
        self.last_primary_error: Optional[str] = None

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

        config = types.GenerateContentConfig(
            system_instruction=self.SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ExperimentInterpretation,
            temperature=0.1,
        )

        self.last_model_used = None
        self.last_fallback_used = False
        self.last_primary_error = None

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            self.last_model_used = self.model

        except ServerError as error:
            status_code = getattr(error, "code", None)
            if status_code is None:
                status_code = getattr(error, "status_code", None)

            # Fallback tylko przy chwilowej niedostępności infrastruktury.
            # Nie wolno wybierać innego modelu dlatego, że odpowiedź
            # podstawowego modelu jest niewygodna lub niezgodna z oczekiwaniem.
            if status_code != 503:
                raise

            if (
                not self.fallback_model
                or self.fallback_model == self.model
            ):
                raise

            self.last_primary_error = str(error)

            response = self.client.models.generate_content(
                model=self.fallback_model,
                contents=prompt,
                config=config,
            )
            self.last_model_used = self.fallback_model
            self.last_fallback_used = True

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
            else "NIE WYSTĂ„â€žPIÄąÂA"
        )

        first_opposition_stronger = (
            str(result.first_opposition_stronger_at)
            if result.first_opposition_stronger_at is not None
            else "NIE WYSTĂ„â€žPIÄąÂ"
        )

        prior_knowledge_context = prior_knowledge_context.strip()

        if prior_knowledge_context:
            prior_knowledge_section = f"""
WCZEĹšNIEJSZA ZWERYFIKOWANA WIEDZA FENIKSA
(KONTEKST POMOCNICZY â€” NIE WYNIK BIEĹ»Ä„CEGO EKSPERYMENTU):

{prior_knowledge_context}

WAĹ»NE:
- ta sekcja nie jest nowÄ… obserwacjÄ…,
- nie moĹĽe automatycznie rozstrzygaÄ‡ hipotezy,
- przy sprzecznoĹ›ci pierwszeĹ„stwo majÄ… bieĹĽÄ…ce obserwacje programu.
"""
        else:
            prior_knowledge_section = """
WCZEĹšNIEJSZA ZWERYFIKOWANA WIEDZA FENIKSA:

Brak wczeĹ›niejszej wiedzy dobranej do tego problemu.
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

Pierwsza wykryta sprzecznoÄąâ€şĂ„â€ˇ:
N={first_contradiction}

Pierwszy moment, gdy siÄąâ€ša sprzeciwu
przewyÄąÄ˝szyÄąâ€ša siÄąâ€šĂ„â„˘ poparcia:
N={first_opposition_stronger}

Maksymalne przebadane N:
{result.maximum_n_tested}


ZADANIE:

1. OceÄąâ€ž status pierwotnej hipotezy.

2. WyjaÄąâ€şnij ocenĂ„â„˘ WYÄąÂĂ„â€žCZNIE na podstawie
   dostarczonych wynikÄ‚Ĺ‚w.

3. WskaÄąÄ˝ nowe ustalenia wynikajĂ„â€¦ce
   bezpoÄąâ€şrednio z obserwacji.

4. Oddziel niewiadome od faktÄ‚Ĺ‚w.

5. JeÄąÄ˝eli istniejĂ„â€¦ rÄ‚Ĺ‚ÄąÄ˝ne moÄąÄ˝liwe wyjaÄąâ€şnienia
   zachowania systemu, wymieÄąâ€ž je jako
   alternatywne wyjaÄąâ€şnienia, a nie fakty.

6. Zaproponuj nastĂ„â„˘pne pytanie eksperymentalne.

7. Zaproponuj nastĂ„â„˘pny eksperyment,
   ktÄ‚Ĺ‚ry pomoÄąÄ˝e ustaliĂ„â€ˇ PRZYCZYNĂ„Â zachowania.

8. NIE PROPONUJ JESZCZE NAPRAWY ALGORYTMU.
"""

