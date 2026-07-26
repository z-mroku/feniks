from dataclasses import dataclass
from typing import Any, Dict, List

from core.truth_engine import (
    Claim,
    Evidence,
    KnowledgeType,
    SourceType,
    TruthEngine,
)


@dataclass(frozen=True)
class SystemFact:
    """
    Fakt o działaniu FENIKSA potwierdzony
    bezpośrednio przez wykonanie jego kodu.
    """

    key: str
    value: Any
    description: str
    source: str = "TruthEngine"


class SystemKnowledge:
    """
    Warstwa jawnej samowiedzy FENIKSA.

    Nie pyta modelu językowego o to,
    jak działa FENIKS.

    Uruchamia rzeczywisty kod systemu
    na kontrolowanych danych i zapisuje
    wynik jako fakt systemowy.
    """

    def __init__(self):
        self.facts: Dict[str, SystemFact] = {}

    def inspect_truth_engine(self) -> List[SystemFact]:
        """
        Bada podstawowe reguły obecnego TruthEngine.
        """

        discovered = [
            self._inspect_no_evidence(),
            self._inspect_support_only(0.95),
            self._inspect_support_only(0.75),
            self._inspect_support_only(0.50),
            self._inspect_opposition_only(),
            self._inspect_two_sided_evidence(),
            self._inspect_quantity_saturation(),
        ]

        for fact in discovered:
            self.facts[fact.key] = fact

        return discovered

    def get(self, key: str) -> SystemFact | None:
        return self.facts.get(key)

    def all_facts(self) -> List[SystemFact]:
        return list(self.facts.values())

    def _new_claim(self) -> Claim:
        return Claim(
            content="Kontrolne twierdzenie samowiedzy FENIKSA",
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

    def _inspect_no_evidence(self) -> SystemFact:
        engine = TruthEngine()
        claim = self._new_claim()

        result = engine.assess(claim)

        return SystemFact(
            key="truth.no_evidence_classification",
            value=result.classification.value,
            description=(
                "Klasyfikacja twierdzenia bez żadnych dowodów."
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

        key_reliability = str(reliability).replace(".", "_")

        return SystemFact(
            key=(
                f"truth.single_support_{key_reliability}"
                "_classification"
            ),
            value={
                "classification": result.classification.value,
                "support_strength": result.support_strength,
            },
            description=(
                "Zachowanie TruthEngine dla jednego "
                f"dowodu wspierającego o wiarygodności "
                f"{reliability:.2f}."
            ),
        )

    def _inspect_opposition_only(self) -> SystemFact:
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
            value=result.classification.value,
            description=(
                "Klasyfikacja przy istnieniu wyłącznie "
                "dowodu przeciwnego."
            ),
        )

    def _inspect_two_sided_evidence(self) -> SystemFact:
        """
        Najważniejszy obecnie test samowiedzy.

        Sprawdza, czy bardzo słaby dowód przeciwny
        wystarcza do przejścia w SPRZECZNOŚĆ.
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
                "classification": result.classification.value,
                "contradiction_detected": (
                    result.contradiction_detected
                ),
                "support_strength": result.support_strength,
                "opposition_strength": result.opposition_strength,
            },
            description=(
                "Kontrolny test jednego mocnego dowodu ZA "
                "i jednego bardzo słabego dowodu PRZECIW."
            ),
        )

    def _inspect_quantity_saturation(self) -> SystemFact:
        """
        Sprawdza rzeczywisty wpływ liczby identycznych
        dowodów na siłę strony.
        """

        strengths = {}

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

            strengths[count] = result.support_strength

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
        )