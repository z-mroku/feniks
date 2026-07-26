from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)
from core.experiment_runner import ExperimentResult
from core.system_knowledge import (
    SystemEvidenceType,
    SystemKnowledge,
)


class ValidationLevel(Enum):
    """
    Poziom epistemiczny ocenianej informacji.
    """

    OBSERVATION = "OBSERWACJA"
    CODE_FACT = "FAKT Z KODU"
    SUPPORTED = "WSPARTE DANYMI"
    HYPOTHESIS = "HIPOTEZA"
    CONFLICT = "SPRZECZNE Z WIEDZĄ"
    UNVERIFIABLE = "NIEWERYFIKOWALNE"
    FALSE_UNKNOWN = "FAŁSZYWA NIEWIADOMA"


@dataclass
class HardFact:
    """
    Twardy fakt dostępny FENIKSOWI.

    origin rozróżnia:
    - rzeczywistą obserwację eksperymentu,
    - fakt z wykonania kodu,
    - fakt z inspekcji implementacji.
    """

    name: str
    value: object
    description: str
    source: str
    origin: str


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

    @property
    def code_facts(self) -> List[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.level == ValidationLevel.CODE_FACT
        ]


class ReasoningValidator:
    """
    Deterministyczny kontroler interpretacji modelu.

    Hierarchia wiedzy:

    1. rzeczywiste obserwacje ExperimentRunner,
    2. fakty uzyskane przez wykonanie kodu,
    3. fakty wynikające z inspekcji implementacji,
    4. interpretacja modelu językowego.

    Model językowy nie jest źródłem faktów
    o działaniu FENIKSA.
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

        hard_facts = self._build_hard_facts(result)

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
            ValidationLevel.UNVERIFIABLE,
        }

        safe_for_memory = (
            hypothesis_status_consistent
            and bool(issues)
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

    # =====================================================
    # TWARDE FAKTY
    # =====================================================

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
                        origin="EKSPERYMENT",
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
                        origin="EKSPERYMENT",
                    ),
                    HardFact(
                        name="final_support",
                        value=last.support_strength,
                        description=(
                            "Końcowa zmierzona siła poparcia."
                        ),
                        source="ExperimentRunner",
                        origin="EKSPERYMENT",
                    ),
                    HardFact(
                        name="final_opposition",
                        value=last.opposition_strength,
                        description=(
                            "Końcowa zmierzona siła sprzeciwu."
                        ),
                        source="ExperimentRunner",
                        origin="EKSPERYMENT",
                    ),
                ]
            )

        for system_fact in self.system_knowledge.all_facts():
            if (
                system_fact.evidence_type
                == SystemEvidenceType.EXECUTION
            ):
                origin = "WYKONANIE_KODU"
            else:
                origin = "INSPEKCJA_KODU"

            facts.append(
                HardFact(
                    name=system_fact.key,
                    value=system_fact.value,
                    description=system_fact.description,
                    source=system_fact.source,
                    origin=origin,
                )
            )

        return facts

    # =====================================================
    # STATUS HIPOTEZY
    # =====================================================

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
                        interpretation.hypothesis_status.value
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
                    interpretation.hypothesis_status.value
                ),
                level=ValidationLevel.SUPPORTED,
                reason=(
                    "Status hipotezy nie przeczy "
                    "wynikom eksperymentu."
                ),
            )
        )

        return True

    # =====================================================
    # NOWE USTALENIA MODELU
    # =====================================================

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
                            "Twierdzenie jest bezpośrednio "
                            "zgodne z obserwacją ExperimentRunner."
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
                            level=ValidationLevel.SUPPORTED,
                            reason=(
                                "Zjawisko saturacji zostało "
                                "niezależnie potwierdzone przez "
                                "kontrolowane wykonanie TruthEngine."
                            ),
                            related_fact=(
                                "truth.quantity_saturation"
                            ),
                        )
                    )
                    continue

            if self._statement_mentions_confidence(
                normalized
            ):
                confidence_growth = (
                    self.system_knowledge.get(
                        "truth.contradiction_confidence_growth"
                    )
                )

                if confidence_growth is not None:
                    issues.append(
                        ValidationIssue(
                            source="new_findings",
                            statement=statement,
                            level=ValidationLevel.SUPPORTED,
                            reason=(
                                "Zachowanie wskaźnika pewności "
                                "zostało bezpośrednio zmierzone "
                                "przez SystemKnowledge."
                            ),
                            related_fact=(
                                "truth.contradiction_confidence_growth"
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
                        "FENIKS nie posiada obecnie "
                        "wystarczającego deterministycznego "
                        "dowodu pozwalającego uznać "
                        "to twierdzenie za fakt."
                    ),
                )
            )

    # =====================================================
    # NIEWIADOME MODELU
    # =====================================================

    def _validate_unknowns(
        self,
        interpretation: ExperimentInterpretation,
        issues: List[ValidationIssue],
    ) -> None:

        contradiction_rule = (
            self.system_knowledge.get(
                "truth.contradiction_rule"
            )
        )

        zero_reliability_fact = (
            self.system_knowledge.get(
                "truth.zero_reliability_evidence"
            )
        )

        quantity_fact = (
            self.system_knowledge.get(
                "truth.quantity_saturation"
            )
        )

        quantity_component = (
            self.system_knowledge.get(
                "truth.quantity_component"
            )
        )

        contradiction_confidence_rule = (
            self.system_knowledge.get(
                "truth.contradiction_confidence_rule"
            )
        )

        confidence_growth = (
            self.system_knowledge.get(
                "truth.contradiction_confidence_growth"
            )
        )

        for statement in interpretation.remaining_unknowns:
            normalized = statement.casefold()

            # -----------------------------------------
            # PRÓG SPRZECZNOŚCI
            # -----------------------------------------

            if self._asks_about_contradiction_threshold(
                normalized
            ):
                if (
                    contradiction_rule is not None
                    and contradiction_rule.value.get(
                        "uses_strength_threshold"
                    )
                    is False
                ):
                    issues.append(
                        ValidationIssue(
                            source="remaining_unknowns",
                            statement=statement,
                            level=(
                                ValidationLevel.FALSE_UNKNOWN
                            ),
                            reason=(
                                "To nie jest już niewiadoma. "
                                "Inspekcja aktualnej implementacji "
                                "TruthEngine pokazuje, że reguła "
                                "SPRZECZNOŚCI nie używa progu "
                                "siły dowodów. Wymaga obecności "
                                "dowodu po obu stronach."
                            ),
                            related_fact=(
                                "truth.contradiction_rule"
                            ),
                        )
                    )
                    continue

                if (
                    zero_reliability_fact is not None
                    and zero_reliability_fact.value.get(
                        "contradiction_detected"
                    )
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
                                "Kontrolowane wykonanie TruthEngine "
                                "wykazało SPRZECZNOŚĆ nawet przy "
                                "dowodzie przeciwnym o wejściowej "
                                "wiarygodności 0.0."
                            ),
                            related_fact=(
                                "truth.zero_reliability_evidence"
                            ),
                        )
                    )
                    continue

            # -----------------------------------------
            # SATURACJA
            # -----------------------------------------

            if self._asks_about_saturation(
                normalized
            ):
                if (
                    quantity_component is not None
                    and quantity_component.value.get(
                        "quantity_saturation_count"
                    )
                    is not None
                ):
                    issues.append(
                        ValidationIssue(
                            source="remaining_unknowns",
                            statement=statement,
                            level=(
                                ValidationLevel.FALSE_UNKNOWN
                            ),
                            reason=(
                                "To nie jest już niewiadoma "
                                "dotycząca mechanizmu. Inspekcja "
                                "implementacji wykazała, że czynnik "
                                "ilościowy osiąga maksimum przy "
                                "trzech dowodach."
                            ),
                            related_fact=(
                                "truth.quantity_component"
                            ),
                        )
                    )
                    continue

                if (
                    quantity_fact is not None
                    and quantity_fact.value.get(
                        "saturation_at"
                    )
                    is not None
                ):
                    issues.append(
                        ValidationIssue(
                            source="remaining_unknowns",
                            statement=statement,
                            level=(
                                ValidationLevel.FALSE_UNKNOWN
                            ),
                            reason=(
                                "Wpływ liczby identycznych dowodów "
                                "został już zmierzony przez "
                                "SystemKnowledge."
                            ),
                            related_fact=(
                                "truth.quantity_saturation"
                            ),
                        )
                    )
                    continue

            # -----------------------------------------
            # MECHANIZM PEWNOŚCI KLASYFIKACJI
            # -----------------------------------------

            if self._asks_about_confidence_behavior(
                normalized
            ):
                if contradiction_confidence_rule is not None:
                    issues.append(
                        ValidationIssue(
                            source="remaining_unknowns",
                            statement=statement,
                            level=(
                                ValidationLevel.FALSE_UNKNOWN
                            ),
                            reason=(
                                "To nie jest już niewiadoma. "
                                "FENIKS zna aktualny wzór "
                                "obliczania pewności dla stanu "
                                "SPRZECZNOŚĆ. Pewność zależy od "
                                "siły słabszej strony, równowagi "
                                "między stronami oraz liczby "
                                "obecnych dowodów. W badanym "
                                "eksperymencie wzrost tych "
                                "składników wyjaśnia wzrost "
                                "classification_confidence."
                            ),
                            related_fact=(
                                "truth.contradiction_confidence_rule"
                            ),
                        )
                    )
                    continue

                if confidence_growth is not None:
                    issues.append(
                        ValidationIssue(
                            source="remaining_unknowns",
                            statement=statement,
                            level=(
                                ValidationLevel.FALSE_UNKNOWN
                            ),
                            reason=(
                                "Zachowanie wskaźnika pewności "
                                "zostało już bezpośrednio zmierzone "
                                "przez SystemKnowledge."
                            ),
                            related_fact=(
                                "truth.contradiction_confidence_growth"
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
                        "Obecna zweryfikowana wiedza FENIKSA "
                        "nie rozstrzyga jeszcze tej kwestii."
                    ),
                )
            )

    # =====================================================
    # ALTERNATYWNE WYJAŚNIENIA MODELU
    # =====================================================

    def _validate_alternative_explanations(
        self,
        interpretation: ExperimentInterpretation,
        issues: List[ValidationIssue],
    ) -> None:

        contradiction_rule = (
            self.system_knowledge.get(
                "truth.contradiction_rule"
            )
        )

        presence_rule = (
            self.system_knowledge.get(
                "truth.two_sided_presence_rule"
            )
        )

        quantity_component = (
            self.system_knowledge.get(
                "truth.quantity_component"
            )
        )

        contradiction_confidence_rule = (
            self.system_knowledge.get(
                "truth.contradiction_confidence_rule"
            )
        )

        for statement in (
            interpretation.alternative_explanations
        ):
            normalized = statement.casefold()

            # -----------------------------------------
            # HIPOTEZA O PROGU SPRZECZNOŚCI
            # -----------------------------------------

            if self._claims_numeric_contradiction_threshold(
                normalized
            ):
                if (
                    contradiction_rule is not None
                    and contradiction_rule.value.get(
                        "uses_strength_threshold"
                    )
                    is False
                ):
                    issues.append(
                        ValidationIssue(
                            source="alternative_explanations",
                            statement=statement,
                            level=ValidationLevel.CONFLICT,
                            reason=(
                                "Wyjaśnienie jest sprzeczne "
                                "z aktualną implementacją. "
                                "TruthEngine nie używa progu "
                                "siły do klasyfikacji "
                                "SPRZECZNOŚCI."
                            ),
                            related_fact=(
                                "truth.contradiction_rule"
                            ),
                        )
                    )
                    continue

            # -----------------------------------------
            # HIPOTEZA O SAMEJ OBECNOŚCI DOWODÓW
            # -----------------------------------------

            if self._claims_presence_based_contradiction(
                normalized
            ):
                if (
                    presence_rule is not None
                    and presence_rule.value.get(
                        "uses_reliability"
                    )
                    is False
                ):
                    issues.append(
                        ValidationIssue(
                            source="alternative_explanations",
                            statement=statement,
                            level=ValidationLevel.CODE_FACT,
                            reason=(
                                "To wyjaśnienie nie jest już "
                                "hipotezą. Aktualna implementacja "
                                "ustawia contradiction_detected "
                                "na podstawie obecności elementów "
                                "w obu listach dowodów."
                            ),
                            related_fact=(
                                "truth.two_sided_presence_rule"
                            ),
                        )
                    )
                    continue

            # -----------------------------------------
            # HIPOTEZA O SATURACJI ILOŚCIOWEJ
            # -----------------------------------------

            if self._statement_mentions_saturation(
                normalized
            ):
                if quantity_component is not None:
                    issues.append(
                        ValidationIssue(
                            source="alternative_explanations",
                            statement=statement,
                            level=ValidationLevel.CODE_FACT,
                            reason=(
                                "Mechanizm saturacji nie jest już "
                                "wyłącznie hipotezą. Aktualna "
                                "implementacja ogranicza czynnik "
                                "ilościowy do maksimum osiąganego "
                                "przy trzech dowodach."
                            ),
                            related_fact=(
                                "truth.quantity_component"
                            ),
                        )
                    )
                    continue

            # -----------------------------------------
            # HIPOTEZA O MECHANIZMIE PEWNOŚCI
            # -----------------------------------------

            if self._claims_confidence_mechanism(
                normalized
            ):
                if contradiction_confidence_rule is not None:
                    issues.append(
                        ValidationIssue(
                            source="alternative_explanations",
                            statement=statement,
                            level=ValidationLevel.CODE_FACT,
                            reason=(
                                "Mechanizm pewności dla stanu "
                                "SPRZECZNOŚĆ jest jawnie określony "
                                "w aktualnej implementacji "
                                "TruthEngine. Nie należy traktować "
                                "znanych składników tego wzoru "
                                "jako hipotezy."
                            ),
                            related_fact=(
                                "truth.contradiction_confidence_rule"
                            ),
                        )
                    )
                    continue

            # -----------------------------------------
            # TWIERDZENIE O NIEWIDOCZNEJ REGULE
            # -----------------------------------------

            if self._claims_hidden_aggregation_rule(
                normalized
            ):
                if (
                    quantity_component is not None
                    and contradiction_rule is not None
                ):
                    issues.append(
                        ValidationIssue(
                            source="alternative_explanations",
                            statement=statement,
                            level=ValidationLevel.CONFLICT,
                            reason=(
                                "FENIKS posiada już jawne fakty "
                                "o aktualnym mechanizmie agregacji "
                                "oraz regule SPRZECZNOŚCI. "
                                "Nie należy przedstawiać tej części "
                                "mechanizmu jako niewidocznej "
                                "w aktualnej samowiedzy systemu."
                            ),
                            related_fact=(
                                "truth.quantity_component"
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
                        "potwierdzone przez deterministyczną "
                        "wiedzę FENIKSA."
                    ),
                )
            )

    # =====================================================
    # DETEKCJA TREŚCI TWIERDZEŃ
    # =====================================================

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
                "limit",
                "maksimum",
            )
        )

    def _statement_mentions_confidence(
        self,
        text: str,
    ) -> bool:

        return any(
            phrase in text
            for phrase in (
                "pewność",
                "pewnosc",
                "wskaźnik pewności",
                "wskaznik pewnosci",
                "classification_confidence",
                "confidence",
            )
        )

    def _asks_about_confidence_behavior(
        self,
        text: str,
    ) -> bool:

        if not self._statement_mentions_confidence(text):
            return False

        uncertainty_or_cause = any(
            phrase in text
            for phrase in (
                "nie wiadomo",
                "dlaczego",
                "czemu",
                "przyczyn",
                "zachowuje",
                "zachowanie",
                "rośnie",
                "rosnie",
                "maleje",
                "zmienia",
            )
        )

        return uncertainty_or_cause

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
            and any(
                word in text
                for word in (
                    "dlaczego",
                    "przyczyn",
                    "limit",
                    "zatrzym",
                    "saturac",
                )
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

    def _claims_presence_based_contradiction(
        self,
        text: str,
    ) -> bool:

        contradiction = (
            "sprzeczno" in text
            or "klasyfikac" in text
        )

        presence = any(
            phrase in text
            for phrase in (
                "obecność",
                "obecnosc",
                "istnienie dowodu",
                "dowód po obu",
                "dowod po obu",
                "dowody po obu",
            )
        )

        return contradiction and presence

    def _claims_confidence_mechanism(
        self,
        text: str,
    ) -> bool:

        if not self._statement_mentions_confidence(text):
            return False

        mechanism = any(
            word in text
            for word in (
                "mechanizm",
                "wzór",
                "wzor",
                "reguł",
                "regul",
                "zależy",
                "zalezy",
                "oblicz",
                "składnik",
                "skladnik",
                "równowag",
                "rownowag",
                "słabsz",
                "slabsz",
            )
        )

        return mechanism

    def _claims_hidden_aggregation_rule(
        self,
        text: str,
    ) -> bool:

        aggregation = any(
            word in text
            for word in (
                "agregac",
                "mechanizm",
                "reguł",
                "regul",
            )
        )

        hidden = any(
            phrase in text
            for phrase in (
                "niewidoczn",
                "nieznan",
                "nie wiadomo",
                "ukryt",
            )
        )

        return aggregation and hidden