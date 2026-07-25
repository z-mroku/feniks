from core.constitution import Constitution
from core.guardian import Guardian
from core.identity import Identity
from core.memory import Memory
from core.truth_engine import TruthEngine, Claim, Evidence


class Feniks:
    """
    Główny rdzeń FENIKS OS.

    Łączy wyspecjalizowane moduły w jeden system.
    """

    def __init__(self):
        # Tożsamość
        self.identity = Identity()

        # Konstytucja
        self.constitution = Constitution()

        # Strażnik
        self.guardian = Guardian(self.constitution)

        # Pamięć robocza
        self.memory = Memory(capacity=20)

        # Silnik oceny wiedzy i dowodów
        self.truth_engine = TruthEngine()

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
        return self.identity.describe()

    def who_created_me(self):
        return self.identity.get_creators()

    def read_constitution(self):
        return self.constitution.read_articles()

    def evaluate_action(self, action: str):
        """
        Przekazuje planowane działanie do Strażnika.
        """
        return self.guardian.evaluate(action)

    def register_claim(self, claim: Claim):
        """
        Rejestruje twierdzenie w Truth Engine.
        """
        return self.truth_engine.register_claim(claim)

    def add_evidence(self, claim: Claim, evidence: Evidence):
        """
        Dodaje dowód dotyczący konkretnego twierdzenia.
        """
        self.truth_engine.add_evidence(
            claim=claim,
            evidence=evidence,
        )

    def assess_claim(self, claim: Claim):
        """
        Przekazuje twierdzenie do analizy Truth Engine.
        """
        return self.truth_engine.assess(claim)

    def remember(self, content: str, source: str = "user"):
        return self.memory.remember(
            content=content,
            source=source,
        )

    def recall(self, limit: int = 5):
        return self.memory.recall(limit)

    def status(self):
        """
        Podstawowa samoobserwacja stanu systemu.
        """

        constitution_summary = self.constitution.summary()
        truth_stats = self.truth_engine.stats()

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

            "truth_engine_loaded": True,
            "truth_claims": truth_stats["registered_claims"],
            "truth_assessments": truth_stats["assessments"],
            "truth_contradictions": truth_stats["contradictions"],
            "truth_unresolved": truth_stats["unresolved"],
        }