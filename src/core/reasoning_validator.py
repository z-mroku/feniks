from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)
from core.experiment_runner import ExperimentResult
from core.system_knowledge import SystemKnowledge


class ValidationLevel(Enum):
    """
    Poziom epistemiczny ocenianej informacji.
    """

    OBSERVATION = "OBSERWACJA"
    SUPPORTED = "WSPARTE DANYMI"
    HYPOTHESIS = "HIPOTEZA"
    CONFLICT = "SPRZECZNE Z WIEDZĄ"
    UNVERIFIABLE = "NIEWERYFIKOWALNE"
    FALSE_UNKNOWN = "FAŁSZYWA NIEWIADOMA"


@dataclass
class HardFact:
    """
    Fakt wyliczony bezpośrednio przez FENIKSA.
    """

    name: str
    value: object
    description: str
    source: str


@dataclass
class ValidationIssue:
    """
    Ocena pojedynczego twierdzenia modelu.
    """

    source: str
    statement: str
    level: ValidationLevel
    reason: str
    related_fact: Optional[str] = None


@dataclass
class ValidationReport:
    """
    Pełny raport walidacji interpretacji.
    """

    hard_facts: List[HardFact] = field(
        default_factory=list
    )

    issues: List[ValidationIssue] = field(
        default_factory=list
    )

    hypothesis_status_consistent: bool = True
    safe_for_memory: bool = False

    @property
    def conflicts(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.level == ValidationLevel.CONFLICT
        ]

    @property
    def false_unknowns(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.level == ValidationLevel.FALSE_UNKNOWN
        ]

    @property
    def hypotheses(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.level == ValidationLevel.HYPOTHESIS
        ]

    @property
    def unverifiable(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.level == ValidationLevel.UNVERIFIABLE
        ]


class ReasoningValidator:
    """
    Deterministyczny kontroler interpretacji modelu.

    Źródła wiedzy:

    1. rzeczywiste wyniki eksperymentu,
    2. samowiedza uzyskana przez wykonanie
       rzeczywistego kodu FENIKSA.

    Model językowy nie jest źródłem faktów
    o działaniu systemu.
    """

    def __init__(
        self,
        system_knowledge: Optional[SystemKnowledge] = None,
    ):
        self.system_knowledge = (
            system_knowledge or SystemKnowledge()
        )

        self.system_knowledge.inspect_truth_engine()

    def validate_experiment_interpretation(
        self,
        interpretation: ExperimentInterpretation,
        result: ExperimentResult,
    ) -> ValidationReport:

        hard_facts = self._build_hard_facts(
            result
        )

        issues: List[ValidationIssue] = []

        hypothesis_status_consistent = (
            self._validate_hypothesis_status(
                interpretation=interpretation,
                result=result,
                issues=issues,
            )
        )

        self._validate_new_findings(
            interpretation=interpretation,
            result=result,
            issues=issues,
        )

        self._validate_unknowns(
            interpretation=interpretation,
            issues=issues,
        )

        self._validate_alternative_explanations(
            interpretation=interpretation,
            issues=issues,
        )

        unsafe_levels = {
            ValidationLevel.CONFLICT,
            ValidationLevel.FALSE_UNKNOWN,
        }

        safe_for_memory = (
            hypothesis_status_consistent
            and not any(
                issue.level in unsafe_levels
                for issue in issues
            )
        )

        return ValidationReport(
            hard_facts=hard_facts,
            issues=issues,
            hypothesis_status_consistent=(
                hypothesis_status_consistent
            ),
            safe_for_memory=safe_for_memory,
        )

    def _build_hard_facts(
        self,
        result: ExperimentResult,
    ) -> List[HardFact]:

        facts: List[HardFact] = []

        observations = result.observations

        if observations:
            last = observations[-1]

            facts.extend(
                [
                    HardFact(
                        name="first_contradiction_at",
                        value=result.first_contradiction_at,
                        description=(
                            "Pierwsza wartość N, przy której "
                            "wykryto sprzeczność."
                        ),
                        source="ExperimentRunner",
                    ),
                    HardFact(
                        name="first_opposition_stronger_at",
                        value=(
                            result.first_opposition_stronger_at
                        ),
                        description=(
                            "Pierwsza wartość N, przy której "
                            "sprzeciw przewyższył poparcie."
                        ),
                        source="ExperimentRunner",
                    ),
                    HardFact(
                        name="final_support",
                        value=last.support_strength,
                        description=(
                            "Końcowa zmierzona siła poparcia."
                        ),
                        source="ExperimentRunner",
                    ),
                    HardFact(
                        name="final_opposition",
                        value=last.opposition_strength,
                        description=(
                            "Końcowa zmierzona siła sprzeciwu."
                        ),
                        source="ExperimentRunner",
                    ),
                ]
            )

        for system_fact in (
            self.system_knowledge.all_facts()
        ):
            facts.append(
                HardFact(
                    name=system_fact.key,
                    value=system_fact.value,
                    description=system_fact.description,
                    source=system_fact.source,
                )
            )

        return facts

    def _validate_hypothesis_status(
        self,
        interpretation: ExperimentInterpretation,
        result: ExperimentResult,
        issues: List[ValidationIssue],
    ) -> bool:

        if (
            result.first_opposition_stronger_at is None
            and interpretation.hypothesis_status
            == HypothesisStatus.CONFIRMED
        ):
            issues.append(
                ValidationIssue(
                    source="hypothesis_status",
                    statement=(
                        interpretation
                        .hypothesis_status
                        .value
                    ),
                    level=ValidationLevel.CONFLICT,
                    reason=(
                        "Hipoteza wymagała przewagi sprzeciwu, "
                        "ale w eksperymencie taka przewaga "
                        "nie wystąpiła."
                    ),
                    related_fact=(
                        "first_opposition_stronger_at"
                    ),
                )
            )

            return False

        issues.append(
            ValidationIssue(
                source="hypothesis_status",
                statement=(
                    interpretation
                    .hypothesis_status
                    .value
                ),
                level=ValidationLevel.SUPPORTED,
                reason=(
                    "Status hipotezy nie przeczy "
                    "wynikom eksperymentu."
                ),
            )
        )

        return True

    def _validate_new_findings(
        self,
        interpretation: ExperimentInterpretation,
        result: ExperimentResult,
        issues: List[ValidationIssue],
    ) -> None:

        observations = result.observations

        for statement in interpretation.new_findings:
            normalized = statement.casefold()

            if (
                result.first_contradiction_at is not None
                and "sprzeczno" in normalized
                and (
                    f"n={result.first_contradiction_at}"
                    in normalized
                    or
                    f"n = {result.first_contradiction_at}"
                    in normalized
                )
            ):
                issues.append(
                    ValidationIssue(
                        source="new_findings",
                        statement=statement,
                        level=ValidationLevel.OBSERVATION,
                        reason=(
                            "Twierdzenie jest zgodne "
                            "z wynikiem ExperimentRunner."
                        ),
                        related_fact=(
                            "first_contradiction_at"
                        ),
                    )
                )

                continue

            if (
                observations
                and self._statement_mentions_saturation(
                    normalized
                )
            ):
                saturation_fact = (
                    self.system_knowledge.get(
                        "truth.quantity_saturation"
                    )
                )

                if (
                    saturation_fact is not None
                    and saturation_fact.value[
                        "saturation_at"
                    ] == 3
                ):
                    issues.append(
                        ValidationIssue(
                            source="new_findings",
                            statement=statement,
                            level=(
                                ValidationLevel.SUPPORTED
                            ),
                            reason=(
                                "Zjawisko saturacji zostało "
                                "niezależnie potwierdzone przez "
                                "kontrolne wykonanie TruthEngine."
                            ),
                            related_fact=(
                                "truth.quantity_saturation"
                            ),
                        )
                    )

                    continue

            issues.append(
                ValidationIssue(
                    source="new_findings",
                    statement=statement,
                    level=ValidationLevel.UNVERIFIABLE,
                    reason=(
                        "FENIKS nie posiada jeszcze "
                        "deterministycznego dowodu "
                        "pozwalającego sklasyfikować "
                        "to zdanie jako fakt."
                    ),
                )
            )

    def _validate_unknowns(
        self,
        interpretation: ExperimentInterpretation,
        issues: List[ValidationIssue],
    ) -> None:

        two_sided_fact = self.system_knowledge.get(
            "truth.any_two_sided_evidence_test"
        )

        quantity_fact = self.system_knowledge.get(
            "truth.quantity_saturation"
        )

        for statement in interpretation.remaining_unknowns:
            normalized = statement.casefold()

            if self._asks_about_contradiction_threshold(
                normalized
            ):
                if (
                    two_sided_fact is not None
                    and two_sided_fact.value[
                        "contradiction_detected"
                    ]
                    is True
                ):
                    issues.append(
                        ValidationIssue(
                            source="remaining_unknowns",
                            statement=statement,
                            level=(
                                ValidationLevel.FALSE_UNKNOWN
                            ),
                            reason=(
                                "Model oznaczył jako niewiadomą "
                                "zachowanie, które FENIKS "
                                "sprawdził kontrolnym wykonaniem "
                                "własnego TruthEngine. "
                                "Dowód przeciwny o bardzo małej "
                                "sile nadal wywołał stan "
                                "SPRZECZNOŚĆ."
                            ),
                            related_fact=(
                                "truth.any_two_sided_evidence_test"
                            ),
                        )
                    )

                    continue

            if self._asks_about_saturation(
                normalized
            ):
                if (
                    quantity_fact is not None
                    and quantity_fact.value[
                        "saturation_at"
                    ] is not None
                ):
                    issues.append(
                        ValidationIssue(
                            source="remaining_unknowns",
                            statement=statement,
                            level=(
                                ValidationLevel.FALSE_UNKNOWN
                            ),
                            reason=(
                                "Wpływ liczby identycznych "
                                "dowodów został już zmierzony "
                                "przez SystemKnowledge."
                            ),
                            related_fact=(
                                "truth.quantity_saturation"
                            ),
                        )
                    )

                    continue

            issues.append(
                ValidationIssue(
                    source="remaining_unknowns",
                    statement=statement,
                    level=ValidationLevel.UNVERIFIABLE,
                    reason=(
                        "Obecna wiedza systemowa nie "
                        "rozstrzyga jeszcze tej kwestii."
                    ),
                )
            )

    def _validate_alternative_explanations(
        self,
        interpretation: ExperimentInterpretation,
        issues: List[ValidationIssue],
    ) -> None:

        two_sided_fact = self.system_knowledge.get(
            "truth.any_two_sided_evidence_test"
        )

        for statement in (
            interpretation.alternative_explanations
        ):
            normalized = statement.casefold()

            if (
                self._claims_numeric_contradiction_threshold(
                    normalized
                )
                and two_sided_fact is not None
                and two_sided_fact.value[
                    "contradiction_detected"
                ]
                is True
            ):
                issues.append(
                    ValidationIssue(
                        source="alternative_explanations",
                        statement=statement,
                        level=ValidationLevel.CONFLICT,
                        reason=(
                            "Hipoteza o wymaganym znaczącym "
                            "progu siły sprzeciwu jest "
                            "sprzeczna z testem kontrolnym: "
                            "sprzeczność wystąpiła już przy "
                            "bardzo słabym dowodzie przeciwnym."
                        ),
                        related_fact=(
                            "truth.any_two_sided_evidence_test"
                        ),
                    )
                )

                continue

            issues.append(
                ValidationIssue(
                    source="alternative_explanations",
                    statement=statement,
                    level=ValidationLevel.HYPOTHESIS,
                    reason=(
                        "Wyjaśnienie nie zostało jeszcze "
                        "potwierdzone przez deterministyczny "
                        "test FENIKSA."
                    ),
                )
            )

    def _statement_mentions_saturation(
        self,
        text: str,
    ) -> bool:
        return any(
            word in text
            for word in (
                "saturac",
                "zatrzym",
                "nie rośnie",
                "nie rosnie",
                "stała",
                "stala",
            )
        )

    def _asks_about_contradiction_threshold(
        self,
        text: str,
    ) -> bool:
        contradiction = (
            "sprzeczno" in text
            or "klasyfikac" in text
        )

        threshold = any(
            word in text
            for word in (
                "próg",
                "prog",
                "minimal",
                "warunek",
                "wymagan",
            )
        )

        return contradiction and threshold

    def _asks_about_saturation(
        self,
        text: str,
    ) -> bool:
        return (
            self._statement_mentions_saturation(text)
            and (
                "dlaczego" in text
                or "przyczyn" in text
                or "limit" in text
            )
        )

    def _claims_numeric_contradiction_threshold(
        self,
        text: str,
    ) -> bool:
        contradiction = (
            "sprzeczno" in text
            or "klasyfikac" in text
        )

        threshold = any(
            word in text
            for word in (
                "próg",
                "prog",
                "threshold",
            )
        )

        return contradiction and threshold