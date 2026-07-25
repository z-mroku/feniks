from datetime import datetime


class Memory:
    """
    Pierwsza pamięć robocza FENIKSA.

    Na tym etapie przechowuje informacje podczas działania programu.
    Później podłączymy pamięć trwałą, semantyczną i doświadczenia.
    """

    def __init__(self, capacity: int = 20):
        self.capacity = capacity
        self.entries = []

    def remember(self, content: str, source: str = "system"):
        entry = {
            "content": content,
            "source": source,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        self.entries.append(entry)

        # Nie pozwalamy pamięci roboczej rosnąć bez końca.
        if len(self.entries) > self.capacity:
            self.entries.pop(0)

        return entry

    def recall(self, limit: int = 5):
        """Zwraca ostatnie zapamiętane informacje."""
        return self.entries[-limit:]

    def clear(self):
        """Czyści wyłącznie pamięć roboczą."""
        self.entries.clear()

    def count(self):
        """Podaje liczbę informacji znajdujących się w pamięci."""
        return len(self.entries)