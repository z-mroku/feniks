from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class IntentHypothesis:
    """
    Hipoteza FENIKSA dotycząca intencji człowieka.

    Ten obiekt NIE opisuje faktu o użytkowniku.
    Reprezentuje interpretację, która może być:
    - trafna,
    - częściowo trafna,
    - błędna,
    - niemożliwa obecnie do rozstrzygnięcia.

    Pewność oznacza pewność interpretacji,
    a nie prawdopodobieństwo obiektywnej prawdy.
    """

    interpretation: str
    confidence: float
    evidence: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    uncertainty: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.interpretation, str):
            raise TypeError("interpretation musi być tekstem.")

        if not self.interpretation.strip():
            raise ValueError("interpretation nie może być puste.")

        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence musi być liczbą.")

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError(
                "confidence musi mieścić się w zakresie 0.0-1.0."
            )

        if not isinstance(self.evidence, tuple):
            raise TypeError("evidence musi być tuple.")

        if not isinstance(self.alternatives, tuple):
            raise TypeError("alternatives musi być tuple.")

        if self.uncertainty is not None:
            if not isinstance(self.uncertainty, str):
                raise TypeError(
                    "uncertainty musi być tekstem albo None."
                )

    @property
    def is_hypothesis(self) -> bool:
        """
        Intencja człowieka pozostaje hipotezą
        niezależnie od poziomu pewności interpretacji.
        """
        return True