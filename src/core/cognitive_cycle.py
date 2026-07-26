from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from core.experiment_interpreter import ExperimentInterpretation
from core.experiment_runner import ExperimentResult, ExperimentRunner
from core.reasoning_validator import (
    ReasoningValidator,
    ValidationReport,
)
from core.system_knowledge import SystemKnowledge


class CognitiveCycleDecision(Enum):
    """
    Decyzja kończąca pojedynczy cykl poznawczy.

    REJECTED:
        Interpretacja nie przeszła walidacji.

    CANDIDATE_FOR_KNOWLEDGE:
        Interpretacja przeszła walidację, ale nie staje
        się przez to automatycznie trwałą wiedzą.
    """

    REJECTED = "ODRZUCONO"

    CANDIDATE_FOR_KNOWLEDGE = (
        "KANDYDAT_DO_WIEDZY"
    )


class ExperimentInterpreter(Protocol):
    """
    Minimalny interfejs wymagany od warstwy
    interpretującej eksperyment.

    CognitiveCycle nie musi wiedzieć,
    czy interpretację przygotował Gemini,
    inny model czy kontrolowany interpreter testowy.
    """

    def interpret(
        self,
        hypothesis: str,
        result: ExperimentResult,
    ) -> ExperimentInterpretation:
        ...


@dataclass
class CognitiveCycleResult:
    """
    Pełny zapis jednego cyklu poznawczego.

    Zachowujemy osobno:
    - hipotezę,
    - rzeczywisty wynik eksperymentu,
    - interpretację,
    - raport walidacji,
    - końcową decyzję.

    Dzięki temu żadna warstwa nie zastępuje
    danych pochodzących z wcześniejszej warstwy.
    """

    hypothesis: str

    experiment_result: ExperimentResult

    interpretation: ExperimentInterpretation

    validation_report: ValidationReport

    decision: CognitiveCycleDecision

    admitted_to_memory: bool = False

    @property
    def safe_for_knowledge_candidate(self) -> bool:
        """
        Informuje, czy wynik może być traktowany
        jako kandydat do dalszego procesu wiedzy.
        """

        return (
            self.decision
            == CognitiveCycleDecision.CANDIDATE_FOR_KNOWLEDGE
        )


class CognitiveCycle:
    """
    Kontroluje pełny cykl poznawczy FENIKSA:

    HIPOTEZA
        ->
    EKSPERYMENT
        ->
    RZECZYWISTE OBSERWACJE
        ->
    INTERPRETACJA
        ->
    WALIDACJA
        ->
    DECYZJA

    Model językowy nie kontroluje eksperymentu,
    walidatora ani końcowej decyzji.

    CognitiveCycle nie zapisuje automatycznie
    interpretacji do trwałej pamięci.
    """

    def __init__(
        self,
        interpreter: ExperimentInterpreter,
        system_knowledge: SystemKnowledge | None = None,
        experiment_runner: ExperimentRunner | None = None,
        reasoning_validator: ReasoningValidator | None = None,
    ):
        self.interpreter = interpreter

        self.system_knowledge = (
            system_knowledge
            if system_knowledge is not None
            else SystemKnowledge()
        )

        self.experiment_runner = (
            experiment_runner
            if experiment_runner is not None
            else ExperimentRunner()
        )

        self.reasoning_validator = (
            reasoning_validator
            if reasoning_validator is not None
            else ReasoningValidator(
                system_knowledge=self.system_knowledge
            )
        )

        self.cycles: list[CognitiveCycleResult] = []

    def run_quantity_vs_quality(
        self,
        hypothesis: str,
        strong_support_reliability: float = 0.95,
        opposing_reliability: float = 0.50,
        max_opposing: int = 20,
    ) -> CognitiveCycleResult:
        """
        Wykonuje pełny cykl poznawczy dla eksperymentu
        quantity_vs_quality.
        """

        if not hypothesis.strip():
            raise ValueError(
                "Hipoteza nie może być pusta."
            )

        self._ensure_system_knowledge()

        experiment_result = (
            self.experiment_runner
            .run_quantity_vs_quality(
                strong_support_reliability=(
                    strong_support_reliability
                ),
                opposing_reliability=(
                    opposing_reliability
                ),
                max_opposing=max_opposing,
            )
        )

        interpretation = self.interpreter.interpret(
            hypothesis=hypothesis,
            result=experiment_result,
        )

        validation_report = (
            self.reasoning_validator
            .validate_experiment_interpretation(
                interpretation=interpretation,
                result=experiment_result,
            )
        )

        decision = self._make_decision(
            validation_report
        )

        cycle_result = CognitiveCycleResult(
            hypothesis=hypothesis,
            experiment_result=experiment_result,
            interpretation=interpretation,
            validation_report=validation_report,
            decision=decision,
            admitted_to_memory=False,
        )

        self.cycles.append(
            cycle_result
        )

        return cycle_result

    def history(self) -> list[CognitiveCycleResult]:
        """
        Zwraca historię cykli bieżącej sesji.
        """

        return list(self.cycles)

    def last_result(
        self,
    ) -> CognitiveCycleResult | None:
        """
        Zwraca ostatni wykonany cykl.
        """

        if not self.cycles:
            return None

        return self.cycles[-1]

    def _ensure_system_knowledge(self) -> None:
        """
        Przed walidacją upewnia się, że system
        posiada aktualną samowiedzę TruthEngine.

        Nie korzystamy tutaj z modelu językowego.
        """

        if not self.system_knowledge.all_facts():
            self.system_knowledge.inspect_truth_engine()

    def _make_decision(
        self,
        report: ValidationReport,
    ) -> CognitiveCycleDecision:
        """
        Podejmuje deterministyczną decyzję
        na podstawie raportu walidatora.

        Model interpretujący nie podejmuje
        tej decyzji.
        """

        if report.safe_for_memory:
            return (
                CognitiveCycleDecision
                .CANDIDATE_FOR_KNOWLEDGE
            )

        return CognitiveCycleDecision.REJECTED