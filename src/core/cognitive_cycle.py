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
    Decyzja koĹ„czÄ…ca pojedynczy cykl poznawczy.

    REJECTED:
        Interpretacja nie przeszĹ‚a walidacji.

    CANDIDATE_FOR_KNOWLEDGE:
        Interpretacja przeszĹ‚a walidacjÄ™, ale nie staje
        siÄ™ przez to automatycznie trwaĹ‚Ä… wiedzÄ….
    """

    REJECTED = "ODRZUCONO"

    CANDIDATE_FOR_KNOWLEDGE = (
        "KANDYDAT_DO_WIEDZY"
    )


class ExperimentInterpreter(Protocol):
    """
    Minimalny interfejs wymagany od warstwy
    interpretujÄ…cej eksperyment.

    CognitiveCycle nie musi wiedzieÄ‡,
    czy interpretacjÄ™ przygotowaĹ‚ Gemini,
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
    PeĹ‚ny zapis jednego cyklu poznawczego.

    Zachowujemy osobno:
    - hipotezÄ™,
    - rzeczywisty wynik eksperymentu,
    - interpretacjÄ™,
    - raport walidacji,
    - koĹ„cowÄ… decyzjÄ™.

    DziÄ™ki temu ĹĽadna warstwa nie zastÄ™puje
    danych pochodzÄ…cych z wczeĹ›niejszej warstwy.
    """

    hypothesis: str

    experiment_result: ExperimentResult

    interpretation: ExperimentInterpretation

    validation_report: ValidationReport

    decision: CognitiveCycleDecision

    admitted_to_memory: bool = False

    # Audytowalny zapis wcześniejszej wiedzy użytej jako kontekst.
    prior_knowledge_context: str = ""

    @property
    def safe_for_knowledge_candidate(self) -> bool:
        """
        Informuje, czy wynik moĹĽe byÄ‡ traktowany
        jako kandydat do dalszego procesu wiedzy.
        """

        return (
            self.decision
            == CognitiveCycleDecision.CANDIDATE_FOR_KNOWLEDGE
        )


class CognitiveCycle:
    """
    Kontroluje peĹ‚ny cykl poznawczy FENIKSA:

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

    Model jÄ™zykowy nie kontroluje eksperymentu,
    walidatora ani koĹ„cowej decyzji.

    CognitiveCycle nie zapisuje automatycznie
    interpretacji do trwaĹ‚ej pamiÄ™ci.
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
        prior_knowledge_context: str = "",
    ) -> CognitiveCycleResult:
        """
        Wykonuje peĹ‚ny cykl poznawczy dla eksperymentu
        quantity_vs_quality.
        """

        if not hypothesis.strip():
            raise ValueError(
                "Hipoteza nie moĹĽe byÄ‡ pusta."
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

        if getattr(self.interpreter, "supports_prior_knowledge_context", False):
            interpretation = self.interpreter.interpret(
                hypothesis=hypothesis,
                result=experiment_result,
                prior_knowledge_context=prior_knowledge_context,
            )
        else:
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
            prior_knowledge_context=prior_knowledge_context,
        )

        self.cycles.append(
            cycle_result
        )

        return cycle_result

    def history(self) -> list[CognitiveCycleResult]:
        """
        Zwraca historiÄ™ cykli bieĹĽÄ…cej sesji.
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
        Przed walidacjÄ… upewnia siÄ™, ĹĽe system
        posiada aktualnÄ… samowiedzÄ™ TruthEngine.

        Nie korzystamy tutaj z modelu jÄ™zykowego.
        """

        if not self.system_knowledge.all_facts():
            self.system_knowledge.inspect_truth_engine()

    def _make_decision(
        self,
        report: ValidationReport,
    ) -> CognitiveCycleDecision:
        """
        Podejmuje deterministycznÄ… decyzjÄ™
        na podstawie raportu walidatora.

        Model interpretujÄ…cy nie podejmuje
        tej decyzji.
        """

        if report.safe_for_memory:
            return (
                CognitiveCycleDecision
                .CANDIDATE_FOR_KNOWLEDGE
            )

        return CognitiveCycleDecision.REJECTED
