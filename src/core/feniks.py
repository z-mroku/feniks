from core.constitution import Constitution
from core.guardian import Guardian
from core.identity import Identity
from core.memory import Memory


class Feniks:
    """
    Główny rdzeń FENIKS OS.

    Rdzeń łączy wyspecjalizowane moduły w jeden system.
    """

    def __init__(self):
        # Tożsamość
        self.identity = Identity()

        # Konstytucja
        self.constitution = Constitution()

        # Strażnik korzysta z TEJ SAMEJ instancji Konstytucji.
        # Dzięki temu cały system odwołuje się do jednego źródła zasad.
        self.guardian = Guardian(self.constitution)

        # Pamięć robocza
        self.memory = Memory(capacity=20)

        self.name = self.identity.name
        self.version = self.identity.version

    def start(self):
        """
        Uruchamia podstawowy cykl FENIKSA.
        """

        self.memory.remember(
            content=f"{self.name} v{self.version} został uruchomiony.",
            source="system",
        )

        return f"{self.name} v{self.version} uruchomiony"

    def who_am_i(self):
        """Odczytuje własną tożsamość."""
        return self.identity.describe()

    def who_created_me(self):
        """Odczytuje informacje o twórcach projektu."""
        return self.identity.get_creators()

    def read_constitution(self):
        """Odczytuje Konstytucję."""
        return self.constitution.read_articles()

    def evaluate_action(self, action: str):
        """
        Przekazuje planowane działanie do Strażnika.

        FENIKS nie musi wykonywać zamiaru,
        aby móc go najpierw przeanalizować.
        """
        return self.guardian.evaluate(action)

    def remember(self, content: str, source: str = "user"):
        """Przekazuje informację do pamięci roboczej."""
        return self.memory.remember(
            content=content,
            source=source,
        )

    def recall(self, limit: int = 5):
        """Odczytuje ostatnie informacje z pamięci roboczej."""
        return self.memory.recall(limit)

    def status(self):
        """
        Podstawowa samoobserwacja stanu systemu.
        """

        constitution_summary = self.constitution.summary()

        return {
            "name": self.identity.name,
            "version": self.identity.version,
            "memory_entries": self.memory.count(),
            "identity_loaded": True,
            "constitution_loaded": True,
            "constitution_version": constitution_summary["version"],
            "constitution_articles": constitution_summary["articles"],
            "guardian_loaded": True,
            "guardian_checks": len(self.guardian.history()),
        }