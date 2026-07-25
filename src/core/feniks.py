from core.constitution import Constitution
from core.development_log import (
    DevelopmentCategory,
    DevelopmentLog,
    DevelopmentStatus,
)
from core.guardian import Guardian
from core.identity import Identity
from core.memory import Memory
from core.truth_engine import Claim, Evidence, TruthEngine


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

        # Silnik Prawdy
        self.truth_engine = TruthEngine()

        # Rejestr Rozwoju
        self.development_log = DevelopmentLog()

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
        """
        Odczytuje własną tożsamość.
        """
        return self.identity.describe()

    def who_created_me(self):
        """
        Odczytuje informacje o twórcach projektu.
        """
        return self.identity.get_creators()

    def read_constitution(self):
        """
        Odczytuje Konstytucję.
        """
        return self.constitution.read_articles()

    def evaluate_action(self, action: str):
        """
        Przekazuje planowane działanie do Strażnika.
        """
        return self.guardian.evaluate(action)

    def register_claim(self, claim: Claim):
        """
        Rejestruje twierdzenie w Silniku Prawdy.
        """
        return self.truth_engine.register_claim(claim)

    def add_evidence(
        self,
        claim: Claim,
        evidence: Evidence,
    ):
        """
        Dodaje dowód dotyczący twierdzenia.
        """
        self.truth_engine.add_evidence(
            claim=claim,
            evidence=evidence,
        )

    def assess_claim(self, claim: Claim):
        """
        Analizuje twierdzenie w Silniku Prawdy.
        """
        return self.truth_engine.assess(claim)

    def remember(
        self,
        content: str,
        source: str = "user",
    ):
        """
        Zapisuje informację w pamięci roboczej.
        """
        return self.memory.remember(
            content=content,
            source=source,
        )

    def recall(self, limit: int = 5):
        """
        Odczytuje ostatnie informacje z pamięci roboczej.
        """
        return self.memory.recall(limit)

    def register_development(
        self,
        title: str,
        description: str,
        category: DevelopmentCategory,
        discovered_by: str = "FENIKS",
    ):
        """
        Rejestruje problem, odkrycie albo ulepszenie.
        """
        return self.development_log.register(
            title=title,
            description=description,
            category=category,
            discovered_by=discovered_by,
        )

    def development_history(self):
        """
        Odczytuje historię rozwoju.
        """
        return self.development_log.history()

    def register_first_development_experience(self):
        """
        Rejestruje pierwsze rzeczywiste doświadczenie
        rozwojowe FENIKSA związane z Silnikiem Prawdy.

        Metoda jest przeznaczona do testu obecnej
        architektury Rejestru Rozwoju.
        """

        entry = self.register_development(
            title=(
                "Nadmierna pewność pierwszej wersji "
                "Silnika Prawdy"
            ),
            description=(
                "Pierwsza wersja algorytmu nadawała "
                "100% pewności twierdzeniu, gdy istniały "
                "dowody wspierające i nie było dowodów "
                "przeciwnych."
            ),
            category=DevelopmentCategory.TRUTH,
            discovered_by="Krzysztof Godlewski i FENIKS",
        )

        self.development_log.add_evidence(
            entry,
            (
                "Test twierdzenia o uruchomieniu "
                "Silnika Prawdy zwrócił 100% pewności "
                "przy dwóch dowodach o wiarygodności "
                "0.98 oraz 0.95."
            ),
        )

        self.development_log.add_change(
            entry,
            (
                "Zmieniono algorytm pewności tak, aby "
                "uwzględniał bilans dowodów, ich średnią "
                "jakość oraz liczbę."
            ),
        )

        self.development_log.add_test_result(
            entry,
            (
                "Po zmianie to samo twierdzenie "
                "otrzymało 94% pewności zamiast 100%."
            ),
        )

        self.development_log.add_unresolved(
            entry,
            (
                "Należy rozdzielić siłę poparcia "
                "twierdzenia od pewności klasyfikacji "
                "w przypadku sprzecznych dowodów."
            ),
        )

        self.development_log.change_status(
            entry,
            DevelopmentStatus.TESTED,
        )

        return entry

    def status(self):
        """
        Podstawowa samoobserwacja stanu systemu.
        """

        constitution_summary = self.constitution.summary()
        truth_stats = self.truth_engine.stats()
        development_stats = self.development_log.stats()

        return {
            "nazwa": self.identity.name,
            "wersja": self.identity.version,
            "wpisy_pamieci_roboczej": self.memory.count(),

            "tozsamosc_zaladowana": True,

            "konstytucja_zaladowana": True,
            "wersja_konstytucji": constitution_summary["version"],
            "artykuly_konstytucji": constitution_summary["articles"],

            "straznik_zaladowany": True,
            "kontrole_straznika": len(
                self.guardian.history()
            ),

            "silnik_prawdy_zaladowany": True,
            "twierdzenia": truth_stats["registered_claims"],
            "analizy_twierdzen": truth_stats["assessments"],
            "sprzecznosci": truth_stats["contradictions"],
            "nierozstrzygniete": truth_stats["unresolved"],

            "rejestr_rozwoju_zaladowany": True,
            "wpisy_rozwoju": development_stats["liczba_wpisow"],
            "nierozwiazane_kwestie": development_stats[
                "nierozwiazane"
            ],
        }