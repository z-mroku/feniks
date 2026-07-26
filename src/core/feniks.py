from core.constitution import Constitution
from core.development_log import (
    DevelopmentCategory,
    DevelopmentLog,
    DevelopmentStatus,
)
from core.guardian import Guardian
from core.identity import Identity
from core.memory import Memory
from core.persistent_memory import PersistentMemory
from core.self_analysis import SelfAnalysis
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
        self.guardian = Guardian(
            self.constitution
        )

        # Pamięć robocza
        self.memory = Memory(
            capacity=20
        )

        # Trwała pamięć SQLite
        self.persistent_memory = PersistentMemory()

        # Silnik Prawdy
        self.truth_engine = TruthEngine()

        # Rejestr Rozwoju bieżącej sesji
        self.development_log = DevelopmentLog()

        # Samoanaliza
        self.self_analysis = SelfAnalysis(
            persistent_memory=self.persistent_memory
        )

        self.name = self.identity.name
        self.version = self.identity.version

    def start(self):
        """
        Uruchamia podstawowy cykl FENIKSA.
        """

        self.memory.remember(
            content=(
                f"{self.name} v{self.version} "
                f"został uruchomiony."
            ),
            source="system",
        )

        return (
            f"{self.name} v{self.version} "
            f"uruchomiony"
        )

    # =====================================================
    # TOŻSAMOŚĆ I KONSTYTUCJA
    # =====================================================

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

    # =====================================================
    # STRAŻNIK
    # =====================================================

    def evaluate_action(
        self,
        action: str,
    ):
        """
        Przekazuje planowane działanie do Strażnika.
        """

        return self.guardian.evaluate(
            action
        )

    # =====================================================
    # SILNIK PRAWDY
    # =====================================================

    def register_claim(
        self,
        claim: Claim,
    ):
        """
        Rejestruje twierdzenie w Silniku Prawdy.
        """

        return self.truth_engine.register_claim(
            claim
        )

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

    def assess_claim(
        self,
        claim: Claim,
    ):
        """
        Analizuje twierdzenie w Silniku Prawdy.
        """

        return self.truth_engine.assess(
            claim
        )

    # =====================================================
    # PAMIĘĆ ROBOCZA
    # =====================================================

    def remember(
        self,
        content: str,
        source: str = "użytkownik",
    ):
        """
        Zapisuje informację w pamięci roboczej.
        """

        return self.memory.remember(
            content=content,
            source=source,
        )

    def recall(
        self,
        limit: int = 5,
    ):
        """
        Odczytuje informacje z pamięci roboczej.
        """

        return self.memory.recall(
            limit
        )

    # =====================================================
    # ZWYKŁA PAMIĘĆ TRWAŁA
    # =====================================================

    def remember_permanently(
        self,
        category: str,
        title: str,
        content: str,
        source: str = "FENIKS",
        metadata=None,
    ):
        """
        Zapisuje informację w trwałej pamięci.
        """

        return self.persistent_memory.save(
            category=category,
            title=title,
            content=content,
            source=source,
            metadata=metadata,
        )

    def recall_permanent(
        self,
        limit: int = 10,
    ):
        """
        Odczytuje ostatnie trwałe wspomnienia.
        """

        return self.persistent_memory.recent(
            limit=limit
        )

    def search_permanent_memory(
        self,
        phrase: str,
    ):
        """
        Przeszukuje trwałą pamięć.
        """

        return self.persistent_memory.search(
            phrase=phrase
        )

    # =====================================================
    # REJESTR ROZWOJU
    # =====================================================

    def register_development(
        self,
        title: str,
        description: str,
        category: DevelopmentCategory,
        discovered_by: str = "FENIKS",
    ):
        """
        Rejestruje doświadczenie rozwojowe
        w pamięci bieżącej sesji.
        """

        return self.development_log.register(
            title=title,
            description=description,
            category=category,
            discovered_by=discovered_by,
        )

    def development_history(self):
        """
        Odczytuje historię rozwoju bieżącej sesji.
        """

        return self.development_log.history()

    # =====================================================
    # TRWAŁA HISTORIA ROZWOJU
    # =====================================================

    def save_development_permanently(
        self,
        entry,
    ):
        """
        Zapisuje wpis Rejestru Rozwoju
        do trwałej historii SQLite.
        """

        return self.persistent_memory.save_development_entry(
            title=entry.title,
            description=entry.description,
            category=entry.category.value,
            status=entry.status.value,
            discovered_by=entry.discovered_by,
            evidence=entry.evidence,
            changes=entry.changes,
            test_results=entry.test_results,
            unresolved=entry.unresolved,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )

    def permanent_development_history(
        self,
        limit=None,
    ):
        """
        Odczytuje trwałą historię rozwoju.
        """

        return self.persistent_memory.development_history(
            limit=limit
        )

    def unresolved_permanent_development(self):
        """
        Odczytuje trwałe wpisy posiadające
        nierozwiązane kwestie.
        """

        return self.persistent_memory.unresolved_development()

    # =====================================================
    # SAMOANALIZA
    # =====================================================

    def analyze_self(self):
        """
        Uruchamia samoanalizę FENIKSA na podstawie
        trwałej historii rozwoju.

        Samoanaliza nie zmienia kodu systemu.
        """

        return self.self_analysis.analyze_development_history()

    def last_self_analysis(self):
        """
        Zwraca ostatni raport samoanalizy
        z bieżącej sesji.
        """

        return self.self_analysis.last_report()

    # =====================================================
    # PIERWSZE DOŚWIADCZENIE ROZWOJOWE
    # =====================================================

    def create_first_development_experience(self):
        """
        Tworzy pierwszy rzeczywisty wpis
        dotyczący rozwoju Silnika Prawdy.
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
            discovered_by=(
                "Krzysztof Godlewski i FENIKS"
            ),
        )

        self.development_log.add_evidence(
            entry,
            (
                "Test Silnika Prawdy zwrócił 100% "
                "pewności przy dwóch dowodach "
                "o wiarygodności 0.98 oraz 0.95."
            ),
        )

        self.development_log.add_change(
            entry,
            (
                "Algorytm zmieniono tak, aby "
                "uwzględniał bilans dowodów, "
                "ich średnią jakość oraz liczbę."
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
                "przy sprzecznych dowodach."
            ),
        )

        self.development_log.change_status(
            entry,
            DevelopmentStatus.TESTED,
        )

        return entry

    def register_first_development_experience(self):
        """
        Starsza nazwa zachowana dla zgodności
        z wcześniejszym kodem.
        """

        return self.create_first_development_experience()

    # =====================================================
    # STAN SYSTEMU
    # =====================================================

    def status(self):
        """
        Podstawowa samoobserwacja stanu FENIKSA.
        """

        constitution_summary = self.constitution.summary()
        truth_stats = self.truth_engine.stats()
        development_stats = self.development_log.stats()
        permanent_status = self.persistent_memory.status()
        self_analysis_stats = self.self_analysis.stats()

        return {
            "nazwa": self.identity.name,
            "wersja": self.identity.version,

            "wpisy_pamieci_roboczej":
                self.memory.count(),

            "tozsamosc_zaladowana": True,

            "konstytucja_zaladowana": True,
            "wersja_konstytucji":
                constitution_summary["version"],
            "artykuly_konstytucji":
                constitution_summary["articles"],

            "straznik_zaladowany": True,
            "kontrole_straznika":
                len(self.guardian.history()),

            "silnik_prawdy_zaladowany": True,
            "twierdzenia":
                truth_stats["registered_claims"],
            "analizy_twierdzen":
                truth_stats["assessments"],
            "sprzecznosci":
                truth_stats["contradictions"],
            "nierozstrzygniete":
                truth_stats["unresolved"],

            "rejestr_rozwoju_zaladowany": True,
            "wpisy_rozwoju_biezacej_sesji":
                development_stats["liczba_wpisow"],

            "pamiec_trwala_zaladowana": True,
            "trwale_wspomnienia":
                permanent_status["liczba_wspomnien"],
            "trwale_wpisy_rozwoju":
                permanent_status["liczba_wpisow_rozwoju"],
            "nierozwiazane_wpisy_rozwoju":
                permanent_status[
                    "nierozwiazane_wpisy_rozwoju"
                ],

            "samoanaliza_zaladowana":
                self_analysis_stats["modul_gotowy"],
            "raporty_samoanalizy":
                self_analysis_stats["liczba_raportow"],
            "ustalenia_samoanalizy":
                self_analysis_stats["liczba_ustalen"],
        }