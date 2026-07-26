from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ReasoningState(Enum):
    """
    Stan elementu rozumowania.

    Silnik nie powinien zgadywać informacji,
    których nie potrafi ustalić.
    """

    ESTABLISHED = "USTALONO"
    PARTIAL = "CZĘŚCIOWO USTALONO"
    UNKNOWN = "NIEUSTALONE"


@dataclass
class ReasoningProblem:
    """
    Ustrukturyzowane wejście dla Silnika Rozumowania.

    Problem nie jest jeszcze rozwiązaniem.
    Zawiera wyłącznie informacje dostępne
    przed rozpoczęciem analizy.
    """

    title: str
    description: str

    evidence: List[str] = field(
        default_factory=list
    )

    unknowns: List[str] = field(
        default_factory=list
    )

    history: List[str] = field(
        default_factory=list
    )


@dataclass
class ReasoningResult:
    """
    Wynik pracy Silnika Rozumowania.

    Poszczególne pola mogą pozostać NIEUSTALONE.
    Jest to poprawny wynik, jeśli dostępne dane
    nie pozwalają na uczciwe wnioskowanie.
    """

    subject: Optional[str] = None

    variable_under_test: Optional[str] = None

    known_facts: List[str] = field(
        default_factory=list
    )

    unknowns: List[str] = field(
        default_factory=list
    )

    hypotheses: List[str] = field(
        default_factory=list
    )

    controls: List[str] = field(
        default_factory=list
    )

    experiment: Optional[str] = None

    expected_observation: Optional[str] = None

    limitations: List[str] = field(
        default_factory=list
    )

    subject_state: ReasoningState = (
        ReasoningState.UNKNOWN
    )

    variable_state: ReasoningState = (
        ReasoningState.UNKNOWN
    )

    experiment_state: ReasoningState = (
        ReasoningState.UNKNOWN
    )

    @property
    def ready_for_experiment(self) -> bool:
        """
        Eksperyment można uznać za przygotowany
        tylko wtedy, gdy ustalono przedmiot badania,
        badaną zmienną oraz sam eksperyment.
        """

        return (
            self.subject_state
            == ReasoningState.ESTABLISHED
            and self.variable_state
            == ReasoningState.ESTABLISHED
            and self.experiment_state
            == ReasoningState.ESTABLISHED
        )


class ReasoningEngine:
    """
    Silnik Rozumowania FENIKS OS.

    Pierwsza wersja tego modułu NIE udaje,
    że rozumie dowolny język naturalny.

    Jego zadaniem jest:

    1. przyjąć ustrukturyzowany problem,
    2. oddzielić wiedzę od niewiedzy,
    3. nie zgadywać brakujących informacji,
    4. przygotować strukturę dalszego rozumowania,
    5. jawnie wskazać ograniczenia analizy.

    Interpretacja semantyczna problemu zostanie
    dodana jako oddzielna warstwa.
    """

    def __init__(self):
        self.analysis_count = 0

    def analyze(
        self,
        problem: ReasoningProblem,
    ) -> ReasoningResult:
        """
        Wykonuje bezpieczną analizę strukturalną.

        Na tym etapie Silnik Rozumowania nie próbuje
        samodzielnie zgadywać znaczenia tekstu.
        """

        self._validate_problem(
            problem
        )

        self.analysis_count += 1

        result = ReasoningResult()

        # Fakty dostępne przed analizą.
        result.known_facts = list(
            problem.evidence
        )

        # Jawnie zapisane niewiadome.
        result.unknowns = list(
            problem.unknowns
        )

        # Historia stanowi kontekst,
        # ale nie jest automatycznie rozwiązaniem.
        if problem.history:
            result.known_facts.extend(
                [
                    f"Historia: {item}"
                    for item in problem.history
                ]
            )

        # Bez warstwy semantycznej nie wolno
        # zgadywać przedmiotu ani zmiennej badania.
        result.limitations.append(
            "Brak warstwy interpretacji semantycznej. "
            "Silnik nie ustala jeszcze samodzielnie "
            "znaczenia dowolnego opisu problemu."
        )

        result.limitations.append(
            "Nie zaprojektowano eksperymentu, ponieważ "
            "nie ustalono jeszcze przedmiotu badania "
            "i zmiennej, której wpływ należy sprawdzić."
        )

        return result

    def _validate_problem(
        self,
        problem: ReasoningProblem,
    ) -> None:
        """
        Sprawdza minimalną poprawność danych wejściowych.
        """

        if not isinstance(
            problem,
            ReasoningProblem,
        ):
            raise TypeError(
                "ReasoningEngine oczekuje obiektu "
                "ReasoningProblem."
            )

        if not problem.title.strip():
            raise ValueError(
                "Tytuł problemu nie może być pusty."
            )

        if not problem.description.strip():
            raise ValueError(
                "Opis problemu nie może być pusty."
            )

    def stats(self) -> dict:
        """
        Zwraca podstawowy stan Silnika Rozumowania.
        """

        return {
            "modul_gotowy": True,
            "liczba_analiz": self.analysis_count,
            "interpretacja_semantyczna": False,
        }