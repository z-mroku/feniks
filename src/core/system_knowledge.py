from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

from core.truth_engine import (
    Claim,
    Evidence,
    KnowledgeType,
    SourceType,
    TruthEngine,
)


class SystemEvidenceType(Enum):
    """
    Określa sposób, w jaki FENIKS zdobył wiedzę
    o własnym działaniu.
    """

    EXECUTION = "WYKONANIE"
    CODE_INSPECTION = "INSPEKCJA_KODU"


@dataclass(frozen=True)
class SystemFact:
    """
    Zweryfikowany fakt o działaniu FENIKSA.
    """

    key: str
    value: Any
    description: str

    source: str = "TruthEngine"

    evidence_type: SystemEvidenceType = (
        SystemEvidenceType.EXECUTION
    )


class SystemKnowledge:
    """
    Warstwa jawnej samowiedzy FENIKSA.

    Hierarchia źródeł:

    1. rzeczywiste wykonanie kodu,
    2. inspekcja aktualnej implementacji,
    3. dopiero później interpretacja modelu.

    Model językowy nie jest źródłem faktów
    systemowych.
    """

    def __init__(self):
        self.facts: Dict[str, SystemFact] = {}

    # =====================================================
    # PUBLICZNA INSPEKCJA TRUTHENGINE
    # =====================================================

    def inspect_truth_engine(self) -> List[SystemFact]:
        """
        Buduje aktualny zestaw samowiedzy
        dotyczącej TruthEngine.
        """

        discovered = [
            # -----------------------------------------
            # FAKTY Z WYKONANIA
            # -----------------------------------------
            self._inspect_no_evidence(),
            self._inspect_support_only(0.95),
            self._inspect_support_only(0.75),
            self._inspect_support_only(0.50),
            self._inspect_opposition_only(),
            self._inspect_two_sided_evidence(),
            self._inspect_quantity_saturation(),
            self._inspect_zero_reliability_evidence(),
            self._inspect_contradiction_confidence_growth(),

            # -----------------------------------------
            # FAKTY Z INSPEKCJI IMPLEMENTACJI
            # -----------------------------------------
            self._inspect_contradiction_rule(),
            self._inspect_quantity_component_rule(),
            self._inspect_two_sided_presence_rule(),
            self._inspect_contradiction_confidence_rule(),
            self._inspect_support_confidence_rule(),
            self._inspect_opposition_confidence_rule(),
            self._inspect_no_evidence_confidence_rule(),
        ]

        for fact in discovered:
            self.facts[fact.key] = fact

        return discovered

    # =====================================================
    # PUBLICZNY DOSTĘP DO WIEDZY
    # =====================================================

    def get(
        self,
        key: str,
    ) -> SystemFact | None:

        return self.facts.get(key)

    def all_facts(self) -> List[SystemFact]:

        return list(self.facts.values())

    def execution_facts(self) -> List[SystemFact]:

        return [
            fact
            for fact in self.facts.values()
            if fact.evidence_type
            == SystemEvidenceType.EXECUTION
        ]

    def code_inspection_facts(
        self,
    ) -> List[SystemFact]:

        return [
            fact
            for fact in self.facts.values()
            if fact.evidence_type
            == SystemEvidenceType.CODE_INSPECTION
        ]

    # =====================================================
    # NARZĘDZIA POMOCNICZE
    # =====================================================

    def _new_claim(self) -> Claim:

        return Claim(
            content=(
                "Kontrolne twierdzenie "
                "samowiedzy FENIKSA"
            ),
            knowledge_type=KnowledgeType.UNKNOWN,
            source="SystemKnowledge",
            source_type=SourceType.SYSTEM,
        )

    def _evidence(
        self,
        reliability: float,
        supports: bool,
        number: int,
    ) -> Evidence:

        return Evidence(
            description=f"Dowód kontrolny {number}",
            source="SystemKnowledge",
            source_type=SourceType.SYSTEM,
            reliability=reliability,
            supports_claim=supports,
        )

    # =====================================================
    # FAKTY USTALANE PRZEZ WYKONANIE
    # =====================================================

    def _inspect_no_evidence(
        self,
    ) -> SystemFact:

        engine = TruthEngine()
        claim = self._new_claim()

        result = engine.assess(claim)

        return SystemFact(
            key="truth.no_evidence_classification",
            value={
                "classification":
                    result.classification.value,
                "confidence":
                    result.classification_confidence,
            },
            description=(
                "Klasyfikacja i pewność klasyfikacji "
                "twierdzenia bez żadnych dowodów."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    def _inspect_support_only(
        self,
        reliability: float,
    ) -> SystemFact:

        engine = TruthEngine()
        claim = self._new_claim()

        engine.add_evidence(
            claim,
            self._evidence(
                reliability=reliability,
                supports=True,
                number=1,
            ),
        )

        result = engine.assess(claim)

        key_reliability = (
            str(reliability).replace(".", "_")
        )

        return SystemFact(
            key=(
                f"truth.single_support_"
                f"{key_reliability}_classification"
            ),
            value={
                "classification":
                    result.classification.value,
                "support_strength":
                    result.support_strength,
                "confidence":
                    result.classification_confidence,
            },
            description=(
                "Zachowanie TruthEngine dla jednego "
                "dowodu wspierającego o wiarygodności "
                f"{reliability:.2f}."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    def _inspect_opposition_only(
        self,
    ) -> SystemFact:

        engine = TruthEngine()
        claim = self._new_claim()

        engine.add_evidence(
            claim,
            self._evidence(
                reliability=0.95,
                supports=False,
                number=1,
            ),
        )

        result = engine.assess(claim)

        return SystemFact(
            key="truth.opposition_only_classification",
            value={
                "classification":
                    result.classification.value,
                "opposition_strength":
                    result.opposition_strength,
                "confidence":
                    result.classification_confidence,
            },
            description=(
                "Zachowanie TruthEngine przy istnieniu "
                "wyłącznie jednego mocnego dowodu "
                "przeciwnego."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    def _inspect_two_sided_evidence(
        self,
    ) -> SystemFact:

        engine = TruthEngine()
        claim = self._new_claim()

        engine.add_evidence(
            claim,
            self._evidence(
                reliability=0.95,
                supports=True,
                number=1,
            ),
        )

        engine.add_evidence(
            claim,
            self._evidence(
                reliability=0.01,
                supports=False,
                number=2,
            ),
        )

        result = engine.assess(claim)

        return SystemFact(
            key="truth.any_two_sided_evidence_test",
            value={
                "classification":
                    result.classification.value,
                "contradiction_detected":
                    result.contradiction_detected,
                "support_strength":
                    result.support_strength,
                "opposition_strength":
                    result.opposition_strength,
                "confidence":
                    result.classification_confidence,
            },
            description=(
                "Kontrolny test jednego mocnego "
                "dowodu ZA i jednego bardzo słabego "
                "dowodu PRZECIW."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    def _inspect_quantity_saturation(
        self,
    ) -> SystemFact:

        strengths: Dict[int, float] = {}

        for count in range(1, 7):
            engine = TruthEngine()
            claim = self._new_claim()

            for number in range(1, count + 1):
                engine.add_evidence(
                    claim,
                    self._evidence(
                        reliability=0.50,
                        supports=True,
                        number=number,
                    ),
                )

            result = engine.assess(claim)

            strengths[count] = (
                result.support_strength
            )

        saturation_at = None

        for count in range(1, 7):
            remaining = [
                strengths[n]
                for n in range(count, 7)
            ]

            if len(set(remaining)) == 1:
                saturation_at = count
                break

        return SystemFact(
            key="truth.quantity_saturation",
            value={
                "strengths": strengths,
                "saturation_at": saturation_at,
            },
            description=(
                "Wpływ liczby identycznych dowodów "
                "o wiarygodności 0.50 na siłę strony."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    def _inspect_zero_reliability_evidence(
        self,
    ) -> SystemFact:

        engine = TruthEngine()
        claim = self._new_claim()

        engine.add_evidence(
            claim,
            self._evidence(
                reliability=0.95,
                supports=True,
                number=1,
            ),
        )

        engine.add_evidence(
            claim,
            self._evidence(
                reliability=0.0,
                supports=False,
                number=2,
            ),
        )

        result = engine.assess(claim)

        return SystemFact(
            key="truth.zero_reliability_evidence",
            value={
                "input_reliability": 0.0,
                "classification":
                    result.classification.value,
                "contradiction_detected":
                    result.contradiction_detected,
                "support_strength":
                    result.support_strength,
                "opposition_strength":
                    result.opposition_strength,
                "opposing_evidence":
                    result.opposing_evidence,
                "confidence":
                    result.classification_confidence,
            },
            description=(
                "Rzeczywiste zachowanie TruthEngine "
                "po dodaniu dowodu przeciwnego "
                "o wiarygodności dokładnie 0.0."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    def _inspect_contradiction_confidence_growth(
        self,
    ) -> SystemFact:
        """
        Mierzy zmianę pewności klasyfikacji
        SPRZECZNOŚĆ przy rosnącej liczbie
        przeciętnych dowodów przeciwnych.
        """

        observations: Dict[int, Dict[str, float]] = {}

        for opposing_count in range(1, 5):
            engine = TruthEngine()
            claim = self._new_claim()

            engine.add_evidence(
                claim,
                self._evidence(
                    reliability=0.95,
                    supports=True,
                    number=1,
                ),
            )

            for number in range(
                1,
                opposing_count + 1,
            ):
                engine.add_evidence(
                    claim,
                    self._evidence(
                        reliability=0.50,
                        supports=False,
                        number=number + 1,
                    ),
                )

            result = engine.assess(claim)

            observations[opposing_count] = {
                "support_strength":
                    result.support_strength,
                "opposition_strength":
                    result.opposition_strength,
                "confidence":
                    result.classification_confidence,
            }

        return SystemFact(
            key="truth.contradiction_confidence_growth",
            value={
                "opposing_count_to_result":
                    observations,
            },
            description=(
                "Rzeczywista zmiana pewności klasyfikacji "
                "SPRZECZNOŚĆ przy jednym mocnym dowodzie ZA "
                "i rosnącej liczbie przeciętnych dowodów "
                "PRZECIW."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    # =====================================================
    # FAKTY WYNIKAJĄCE Z IMPLEMENTACJI
    # =====================================================

    def _inspect_contradiction_rule(
        self,
    ) -> SystemFact:

        return SystemFact(
            key="truth.contradiction_rule",
            value={
                "requires_supporting_presence": True,
                "requires_opposing_presence": True,
                "uses_strength_threshold": False,
            },
            description=(
                "Aktualna implementacja klasyfikuje "
                "twierdzenie jako SPRZECZNOŚĆ, gdy "
                "istnieje co najmniej jeden dowód ZA "
                "i co najmniej jeden dowód PRZECIW. "
                "Reguła nie sprawdza progu siły stron."
            ),
            source="TruthEngine._classify",
            evidence_type=(
                SystemEvidenceType.CODE_INSPECTION
            ),
        )

    def _inspect_quantity_component_rule(
        self,
    ) -> SystemFact:

        return SystemFact(
            key="truth.quantity_component",
            value={
                "reliability_weight": 0.85,
                "quantity_weight": 0.15,
                "quantity_saturation_count": 3,
                "single_evidence_quantity_bonus": 0.05,
            },
            description=(
                "Aktualna implementacja siły strony "
                "łączy średnią wiarygodność z wagą "
                "0.85 oraz czynnik ilościowy z wagą "
                "0.15. Czynnik ilościowy osiąga "
                "maksimum przy trzech dowodach."
            ),
            source=(
                "TruthEngine._calculate_side_strength"
            ),
            evidence_type=(
                SystemEvidenceType.CODE_INSPECTION
            ),
        )

    def _inspect_two_sided_presence_rule(
        self,
    ) -> SystemFact:

        return SystemFact(
            key="truth.two_sided_presence_rule",
            value={
                "rule":
                    "bool(supporting) and bool(opposing)",
                "uses_reliability": False,
                "uses_support_strength": False,
                "uses_opposition_strength": False,
            },
            description=(
                "Flaga contradiction_detected zależy "
                "wyłącznie od obecności dowodów "
                "po obu stronach."
            ),
            source="TruthEngine.assess",
            evidence_type=(
                SystemEvidenceType.CODE_INSPECTION
            ),
        )

    def _inspect_contradiction_confidence_rule(
        self,
    ) -> SystemFact:
        """
        Jawny wzór pewności klasyfikacji
        dla stanu SPRZECZNOŚĆ.
        """

        return SystemFact(
            key="truth.contradiction_confidence_rule",
            value={
                "weaker_side_weight": 0.50,
                "balance_weight": 0.30,
                "evidence_presence_weight": 0.20,
                "balance_formula":
                    "weaker_side / stronger_side",
                "evidence_presence_formula":
                    "min(total_evidence / 4.0, 1.0)",
                "evidence_presence_saturation_count": 4,
            },
            description=(
                "Pewność klasyfikacji SPRZECZNOŚĆ "
                "jest sumą trzech składników: "
                "50% siły słabszej strony, "
                "30% równowagi między stronami oraz "
                "20% wskaźnika obecności dowodów. "
                "Składnik obecności dowodów osiąga "
                "maksimum przy czterech dowodach łącznie."
            ),
            source=(
                "TruthEngine."
                "_calculate_classification_confidence"
            ),
            evidence_type=(
                SystemEvidenceType.CODE_INSPECTION
            ),
        )

    def _inspect_support_confidence_rule(
        self,
    ) -> SystemFact:

        return SystemFact(
            key="truth.support_confidence_rule",
            value={
                "support_strength_weight": 0.85,
                "quantity_weight": 0.15,
                "quantity_saturation_count": 3,
            },
            description=(
                "Przy wyłącznie dowodach wspierających "
                "pewność klasyfikacji składa się w 85% "
                "z siły poparcia i w 15% z czynnika "
                "ilościowego, który osiąga maksimum "
                "przy trzech dowodach."
            ),
            source=(
                "TruthEngine."
                "_calculate_classification_confidence"
            ),
            evidence_type=(
                SystemEvidenceType.CODE_INSPECTION
            ),
        )

    def _inspect_opposition_confidence_rule(
        self,
    ) -> SystemFact:

        return SystemFact(
            key="truth.opposition_confidence_rule",
            value={
                "opposition_strength_weight": 0.85,
                "quantity_weight": 0.15,
                "quantity_saturation_count": 3,
            },
            description=(
                "Przy wyłącznie dowodach przeciwnych "
                "pewność klasyfikacji składa się w 85% "
                "z siły sprzeciwu i w 15% z czynnika "
                "ilościowego, który osiąga maksimum "
                "przy trzech dowodach."
            ),
            source=(
                "TruthEngine."
                "_calculate_classification_confidence"
            ),
            evidence_type=(
                SystemEvidenceType.CODE_INSPECTION
            ),
        )

    def _inspect_no_evidence_confidence_rule(
        self,
    ) -> SystemFact:

        return SystemFact(
            key="truth.no_evidence_confidence_rule",
            value={
                "without_initial_confidence": 0.0,
                "initial_confidence_multiplier": 0.25,
            },
            description=(
                "Przy braku dowodów pewność klasyfikacji "
                "wynosi 0.0, chyba że twierdzenie posiada "
                "początkową wartość confidence. Wtedy "
                "TruthEngine wykorzystuje 25% tej wartości."
            ),
            source=(
                "TruthEngine."
                "_calculate_classification_confidence"
            ),
            evidence_type=(
                SystemEvidenceType.CODE_INSPECTION
            ),
        )