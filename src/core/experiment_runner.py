from dataclasses import dataclass
from typing import List, Optional

from core.truth_engine import (
    Claim,
    Evidence,
    KnowledgeType,
    SourceType,
    TruthEngine,
)


@dataclass
class ExperimentObservation:
    """
    Pojedyncza obserwacja wykonana
    podczas eksperymentu Silnika Prawdy.
    """

    n_opposing: int

    classification: KnowledgeType

    support_strength: float
    opposition_strength: float
    classification_confidence: float

    supporting_evidence: int
    opposing_evidence: int

    contradiction_detected: bool


@dataclass
class ExperimentResult:
    """
    Pełny wynik kontrolowanego eksperymentu.
    """

    name: str

    observations: List[ExperimentObservation]

    first_contradiction_at: Optional[int]

    first_opposition_stronger_at: Optional[int]

    maximum_n_tested: int


class ExperimentRunner:
    """
    Wykonuje kontrolowane eksperymenty
    na rzeczywistym TruthEngine.

    Nie przewiduje wyniku.

    Nie pyta modelu językowego,
    jaki powinien być wynik.

    Tworzy dane wejściowe, uruchamia
    TruthEngine i zapisuje to,
    co rzeczywiście zwrócił system.
    """

    def __init__(self):
        self.experiments: List[ExperimentResult] = []

    def run_quantity_vs_quality(
        self,
        strong_support_reliability: float = 0.95,
        opposing_reliability: float = 0.50,
        max_opposing: int = 20,
    ) -> ExperimentResult:
        """
        Bada wpływ rosnącej liczby przeciętnych
        dowodów przeciwnych na jeden mocny
        dowód wspierający.

        Dla każdego N tworzy NOWY TruthEngine
        i NOWE twierdzenie.

        Dzięki temu kolejne próby są od siebie
        odseparowane.
        """

        self._validate_reliability(
            strong_support_reliability
        )

        self._validate_reliability(
            opposing_reliability
        )

        if max_opposing < 0:
            raise ValueError(
                "max_opposing nie może być mniejsze od 0."
            )

        observations: List[
            ExperimentObservation
        ] = []

        for n_opposing in range(
            0,
            max_opposing + 1,
        ):
            engine = TruthEngine()

            claim = Claim(
                content=(
                    "Eksperymentalne twierdzenie "
                    "quantity_vs_quality."
                ),
                knowledge_type=KnowledgeType.HYPOTHESIS,
                source="ExperimentRunner",
                source_type=SourceType.SYSTEM,
            )

            engine.register_claim(
                claim
            )

            strong_evidence = Evidence(
                description=(
                    "Pojedynczy kontrolowany "
                    "dowód wspierający."
                ),
                source="experiment_support",
                source_type=SourceType.SYSTEM,
                reliability=strong_support_reliability,
                supports_claim=True,
            )

            engine.add_evidence(
                claim,
                strong_evidence,
            )

            for index in range(
                n_opposing
            ):
                opposing_evidence = Evidence(
                    description=(
                        "Kontrolowany przeciętny "
                        f"dowód przeciwny nr {index + 1}."
                    ),
                    source=(
                        f"experiment_opposition_"
                        f"{index + 1}"
                    ),
                    source_type=SourceType.SYSTEM,
                    reliability=opposing_reliability,
                    supports_claim=False,
                )

                engine.add_evidence(
                    claim,
                    opposing_evidence,
                )

            assessment = engine.assess(
                claim
            )

            observation = ExperimentObservation(
                n_opposing=n_opposing,

                classification=(
                    assessment.classification
                ),

                support_strength=(
                    assessment.support_strength
                ),

                opposition_strength=(
                    assessment.opposition_strength
                ),

                classification_confidence=(
                    assessment.classification_confidence
                ),

                supporting_evidence=(
                    assessment.supporting_evidence
                ),

                opposing_evidence=(
                    assessment.opposing_evidence
                ),

                contradiction_detected=(
                    assessment.contradiction_detected
                ),
            )

            observations.append(
                observation
            )

        first_contradiction_at = self._first_n(
            observations,
            lambda observation: (
                observation.contradiction_detected
            ),
        )

        first_opposition_stronger_at = self._first_n(
            observations,
            lambda observation: (
                observation.opposition_strength
                >
                observation.support_strength
            ),
        )

        result = ExperimentResult(
            name="quantity_vs_quality",

            observations=observations,

            first_contradiction_at=(
                first_contradiction_at
            ),

            first_opposition_stronger_at=(
                first_opposition_stronger_at
            ),

            maximum_n_tested=max_opposing,
        )

        self.experiments.append(
            result
        )

        return result

    def _first_n(
        self,
        observations: List[ExperimentObservation],
        condition,
    ) -> Optional[int]:
        """
        Zwraca pierwszą wartość N,
        dla której warunek został spełniony.
        """

        for observation in observations:
            if condition(
                observation
            ):
                return observation.n_opposing

        return None

    def _validate_reliability(
        self,
        value: float,
    ) -> None:
        """
        Kontroluje zakres wiarygodności dowodu.
        """

        if not 0.0 <= value <= 1.0:
            raise ValueError(
                "Wiarygodność musi mieścić się "
                "w zakresie od 0.0 do 1.0."
            )