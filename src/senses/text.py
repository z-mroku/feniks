from protocols.event_protocol import InputEvent, utc_now


class TextSense:
    """
    Tekstowy zmysł wejściowy FENIKSA.

    Jego jedynym zadaniem jest odebranie surowego tekstu
    i zamiana go na InputEvent.

    TextSense NIE interpretuje treści.
    Nie rozpoznaje intencji, emocji ani znaczenia.
    Nie poprawia pisowni.
    Nie odpowiada użytkownikowi.
    Nie zapisuje wiedzy.
    """

    SOURCE = "user"
    MODALITY = "text"

    def receive(self, content: str) -> InputEvent:
        """
        Odbiera tekst dokładnie w takiej postaci,
        w jakiej został przekazany do systemu.
        """

        if not isinstance(content, str):
            raise TypeError("TextSense oczekuje tekstu.")

        if not content:
            raise ValueError("TextSense nie może odebrać pustego tekstu.")

        return InputEvent(
            source=self.SOURCE,
            modality=self.MODALITY,
            content=content,
            timestamp=utc_now(),
        )