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

    EXECUTION:
        Fakt został ustalony przez rzeczywiste
        wykonanie kodu systemu.

    CODE_INSPECTION:
        Fakt wynika bezpośrednio z jawnej reguły
        zapisanej w implementacji systemu.
    """

    EXECUTION = "WYKONANIE"
    CODE_INSPECTION = "INSPEKCJA_KODU"


@dataclass(frozen=True)
class SystemFact:
    """
    Zweryfikowany fakt o działaniu FENIKSA.

    Fakt przechowuje nie tylko wartość,
    ale również pochodzenie wiedzy.
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

    Rozdziela dwa sposoby zdobywania wiedzy:

    1. WYKONANIE
       FENIKS uruchamia własny kod na
       kontrolowanych danych i obserwuje wynik.

    2. INSPEKCJA KODU
       FENIKS zapisuje jawne reguły wynikające
       bezpośrednio z aktualnej implementacji.

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

            # -----------------------------------------
            # FAKTY Z INSPEKCJI IMPLEMENTACJI
            # -----------------------------------------
            self._inspect_contradiction_rule(),
            self._inspect_quantity_component_rule(),
            self._inspect_two_sided_presence_rule(),
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
        """
        Zwraca fakt systemowy o podanym kluczu.
        """

        return self.facts.get(key)

    def all_facts(self) -> List[SystemFact]:
        """
        Zwraca wszystkie aktualnie zapisane fakty.
        """

        return list(self.facts.values())

    def execution_facts(self) -> List[SystemFact]:
        """
        Zwraca fakty ustalone przez wykonanie kodu.
        """

        return [
            fact
            for fact in self.facts.values()
            if fact.evidence_type
            == SystemEvidenceType.EXECUTION
        ]

    def code_inspection_facts(
        self,
    ) -> List[SystemFact]:
        """
        Zwraca fakty wynikające z inspekcji
        aktualnej implementacji.
        """

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
        """
        Tworzy neutralne twierdzenie kontrolne.
        """

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
        """
        Tworzy kontrolowany dowód testowy.
        """

        return Evidence(
            description=(
                f"Dowód kontrolny {number}"
            ),
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
        """
        Sprawdza zachowanie bez dowodów.
        """

        engine = TruthEngine()
        claim = self._new_claim()

        result = engine.assess(claim)

        return SystemFact(
            key="truth.no_evidence_classification",
            value=result.classification.value,
            description=(
                "Klasyfikacja twierdzenia "
                "bez żadnych dowodów."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    def _inspect_support_only(
        self,
        reliability: float,
    ) -> SystemFact:
        """
        Sprawdza zachowanie pojedynczego
        dowodu wspierającego.
        """

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
        """
        Sprawdza zachowanie pojedynczego
        dowodu przeciwnego.
        """

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
                "Zachowanie TruthEngine przy "
                "istnieniu wyłącznie jednego "
                "mocnego dowodu przeciwnego."
            ),
            evidence_type=(
                SystemEvidenceType.EXECUTION
            ),
        )

    def _inspect_two_sided_evidence(
        self,
    ) -> SystemFact:
        """
        Sprawdza zachowanie przy mocnym dowodzie ZA
        i bardzo słabym dowodzie PRZECIW.
        """

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
        """
        Sprawdza wpływ liczby identycznych dowodów
        na siłę jednej strony.
        """

        strengths: Dict[int, float] = {}

        for count in range(1, 7):
            engine = TruthEngine()
            claim = self._new_claim()

            for number in range(
                1,
                count + 1,
            ):
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
                for n in range(
                    count,
                    7,
                )
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
        """
        Sprawdza szczególny przypadek:

        jeden mocny dowód ZA
        oraz jeden dowód PRZECIW
        o wiarygodności dokładnie 0.0.
        """

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

    # =====================================================
    # FAKTY WYNIKAJĄCE Z IMPLEMENTACJI
    # =====================================================

    def _inspect_contradiction_rule(
        self,
    ) -> SystemFact:
        """
        Jawna reguła obecnej implementacji _classify().

        Obecność co najmniej jednego dowodu
        po obu stronach powoduje klasyfikację
        SPRZECZNOŚĆ.
        """

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
        """
        Jawna reguła _calculate_side_strength().

        Siła strony zawiera składnik jakościowy
        oraz składnik ilościowy.
        """

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
                "maksimum przy trzech dowodach. "
                "Jeden zapisany dowód wnosi składnik "
                "ilościowy równy 0.05."
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
        """
        Jawna reguła contradiction_detected.

        Flaga zależy od obecności elementów
        w obu listach, a nie od ich siły.
        """

        return SystemFact(
            key="truth.two_sided_presence_rule",
            value={
                "rule": (
                    "bool(supporting) "
                    "and bool(opposing)"
                ),
                "uses_reliability": False,
                "uses_support_strength": False,
                "uses_opposition_strength": False,
            },
            description=(
                "Flaga contradiction_detected "
                "w aktualnej implementacji zależy "
                "wyłącznie od niepustości list "
                "supporting i opposing."
            ),
            source="TruthEngine.assess",
            evidence_type=(
                SystemEvidenceType.CODE_INSPECTION
            ),
        )