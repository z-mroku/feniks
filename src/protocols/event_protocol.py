from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class InputEvent:
    """
    Surowe zdarzenie wejściowe FENIKSA.

    InputEvent opisuje to, co rzeczywiście dotarło
    do systemu, zanim rozpocznie się interpretacja.

    Nie zawiera:
    - rozpoznanej intencji,
    - emocji,
    - znaczenia,
    - hipotez,
    - odpowiedzi,
    - wniosków.

    Jest zapisem obserwacji wejściowej.
    """

    source: str
    modality: str
    content: str
    timestamp: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.source, str):
            raise TypeError("source musi być tekstem.")

        if not self.source.strip():
            raise ValueError("source nie może być pusty.")

        if not isinstance(self.modality, str):
            raise TypeError("modality musi być tekstem.")

        if not self.modality.strip():
            raise ValueError("modality nie może być puste.")

        if not isinstance(self.content, str):
            raise TypeError("content musi być tekstem.")

        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp musi być obiektem datetime.")

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "timestamp musi zawierać informację o strefie czasowej."
            )


def utc_now() -> datetime:
    """
    Zwraca aktualny czas jako świadomy strefy czasowej UTC.

    Funkcja istnieje po to, aby moduły tworzące zdarzenia
    korzystały ze wspólnego sposobu oznaczania czasu.
    """
    return datetime.now(timezone.utc)