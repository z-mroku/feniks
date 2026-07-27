from dataclasses import dataclass
from typing import Any

from protocols.event_protocol import InputEvent


@dataclass(frozen=True)
class Perception:
    """
    Wynik pierwszego etapu percepcji FENIKSA.

    Zachowuje surowe zdarzenie wejściowe i opisuje,
    co percepcja rzeczywiście może stwierdzić
    bez zgadywania znaczenia, intencji lub emocji.

    To NIE jest jeszcze:
    - rozpoznanie intencji,
    - analiza emocji,
    - Thought,
    - wnioskowanie,
    - odpowiedź.
    """

    event: InputEvent
    perceived_content: Any
    source: str
    modality: str

    @property
    def raw_content(self) -> str:
        """
        Udostępnia oryginalną treść bez jej modyfikacji.
        """
        return self.event.content


class PerceptionEngine:
    """
    Główny koordynator percepcji FENIKSA.

    Przyjmuje surowy InputEvent pochodzący ze zmysłu
    i tworzy jego pierwszy reprezentowany obraz
    dla dalszych warstw systemu.

    Na obecnym etapie dla tekstu zachowuje treść 1:1.

    Nie rozpoznaje intencji.
    Nie zgaduje emocji.
    Nie poprawia tekstu.
    Nie tworzy hipotez.
    Nie podejmuje decyzji.
    """

    def __init__(self) -> None:
        self.perception_count = 0

    def perceive(self, event: InputEvent) -> Perception:
        if not isinstance(event, InputEvent):
            raise TypeError(
                "PerceptionEngine oczekuje obiektu InputEvent."
            )

        self.perception_count += 1

        return Perception(
            event=event,
            perceived_content=event.content,
            source=event.source,
            modality=event.modality,
        )

    def stats(self) -> dict:
        return {
            "modul_gotowy": True,
            "liczba_percepcji": self.perception_count,
        }