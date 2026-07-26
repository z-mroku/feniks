from core.constitution import Constitution
from core.development_log import (
    DevelopmentCategory,
    DevelopmentLog,
    DevelopmentStatus,
)
from core.experiment_runner import ExperimentResult, ExperimentRunner
from core.guardian import Guardian
from core.identity import Identity
from core.memory import Memory
from core.persistent_memory import PersistentMemory
from core.reasoning_validator import (
    ValidationReport,
    ReasoningValidator,
)
from core.self_analysis import SelfAnalysis
from core.system_knowledge import SystemKnowledge
from core.truth_engine import Claim, Evidence, TruthEngine


class Feniks:
    """
    GĹ‚Ăłwny rdzeĹ„ FENIKS OS.

    ĹÄ…czy wyspecjalizowane moduĹ‚y w jeden system.

    RdzeĹ„ rozdziela:
    - dziaĹ‚anie operacyjne,
    - pamiÄ™Ä‡,
    - ocenÄ™ prawdy,
    - historiÄ™ rozwoju,
    - samoanalizÄ™,
    - samowiedzÄ™ o dziaĹ‚aniu systemu,
    - eksperymenty diagnostyczne,
    - walidacjÄ™ interpretacji.
    """

    def __init__(self):
        # ToĹĽsamoĹ›Ä‡
        self.identity = Identity()

        # Konstytucja
        self.constitution = Constitution()

        # StraĹĽnik
        self.guardian = Guardian(
            self.constitution
        )

        # PamiÄ™Ä‡ robocza
        self.memory = Memory(
            capacity=20
        )

        # TrwaĹ‚a pamiÄ™Ä‡ SQLite
        self.persistent_memory = PersistentMemory()

        # Silnik Prawdy
        self.truth_engine = TruthEngine()

        # Rejestr Rozwoju bieĹĽÄ…cej sesji
        self.development_log = DevelopmentLog()

        # Samoanaliza
        self.self_analysis = SelfAnalysis(
            persistent_memory=self.persistent_memory
        )

        # =================================================
        # POZNAWCZY RDZEĹ DIAGNOSTYCZNY
        # =================================================

        # Jawna samowiedza FENIKSA o rzeczywistym
        # dziaĹ‚aniu jego wĹ‚asnych mechanizmĂłw.
        self.system_knowledge = SystemKnowledge()

        # Wykonuje kontrolowane eksperymenty
        # na rzeczywistych komponentach systemu.
        self.experiment_runner = ExperimentRunner()

        # Sprawdza interpretacje wzglÄ™dem:
        # - obserwacji eksperymentalnych,
        # - wykonaniowej samowiedzy,
        # - wiedzy uzyskanej z inspekcji kodu.
        self.reasoning_validator = ReasoningValidator(
            system_knowledge=self.system_knowledge
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
                f"zostaĹ‚ uruchomiony."
            ),
            source="system",
        )

        return (
            f"{self.name} v{self.version} "
            f"uruchomiony"
        )

    # =====================================================
    # TOĹ»SAMOĹšÄ† I KONSTYTUCJA
    # =====================================================

    def who_am_i(self):
        """
        Odczytuje wĹ‚asnÄ… toĹĽsamoĹ›Ä‡.
        """

        return self.identity.describe()

    def who_created_me(self):
        """
        Odczytuje informacje o twĂłrcach projektu.
        """

        return self.identity.get_creators()

    def read_constitution(self):
        """
        Odczytuje KonstytucjÄ™.
        """

        return self.constitution.read_articles()

    # =====================================================
    # STRAĹ»NIK
    # =====================================================

    def evaluate_action(
        self,
        action: str,
    ):
        """
        Przekazuje planowane dziaĹ‚anie do StraĹĽnika.
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
        Dodaje dowĂłd dotyczÄ…cy twierdzenia.
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
    # PAMIÄÄ† ROBOCZA
    # =====================================================

    def remember(
        self,
        content: str,
        source: str = "uĹĽytkownik",
    ):
        """
        Zapisuje informacjÄ™ w pamiÄ™ci roboczej.
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
        Odczytuje informacje z pamiÄ™ci roboczej.
        """

        return self.memory.recall(
            limit
        )

    # =====================================================
    # ZWYKĹA PAMIÄÄ† TRWAĹA
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
        Zapisuje informacjÄ™ w trwaĹ‚ej pamiÄ™ci.
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
        Odczytuje ostatnie trwaĹ‚e wspomnienia.
        """

        return self.persistent_memory.recent(
            limit=limit
        )

    def search_permanent_memory(
        self,
        phrase: str,
    ):
        """
        Przeszukuje trwaĹ‚Ä… pamiÄ™Ä‡.
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
        Rejestruje doĹ›wiadczenie rozwojowe
        w pamiÄ™ci bieĹĽÄ…cej sesji.
        """

        return self.development_log.register(
            title=title,
            description=description,
            category=category,
            discovered_by=discovered_by,
        )

    def development_history(self):
        """
        Odczytuje historiÄ™ rozwoju bieĹĽÄ…cej sesji.
        """

        return self.development_log.history()

    # =====================================================
    # TRWAĹA HISTORIA ROZWOJU
    # =====================================================

    def save_development_permanently(
        self,
        entry,
    ):
        """
        Zapisuje wpis Rejestru Rozwoju
        do trwaĹ‚ej historii SQLite.
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
        Odczytuje trwaĹ‚Ä… historiÄ™ rozwoju.
        """

        return self.persistent_memory.development_history(
            limit=limit
        )

    def unresolved_permanent_development(self):
        """
        Odczytuje trwaĹ‚e wpisy posiadajÄ…ce
        nierozwiÄ…zane kwestie.
        """

        return self.persistent_memory.unresolved_development()

    # =====================================================
    # SAMOANALIZA
    # =====================================================

    def analyze_self(self):
        """
        Uruchamia samoanalizÄ™ FENIKSA na podstawie
        trwaĹ‚ej historii rozwoju.

        Samoanaliza nie zmienia kodu systemu.
        """

        return self.self_analysis.analyze_development_history()

    def last_self_analysis(self):
        """
        Zwraca ostatni raport samoanalizy
        z bieĹĽÄ…cej sesji.
        """

        return self.self_analysis.last_report()

    # =====================================================
    # SAMOWIEDZA SYSTEMOWA
    # =====================================================

    def inspect_system_knowledge(self):
        """
        Uruchamia kontrolowane badanie wĹ‚asnego
        TruthEngine i aktualizuje jawnÄ… samowiedzÄ™.

        Fakty pochodzÄ… z rzeczywistego wykonania
        systemu albo z jawnej inspekcji jego kodu.
        """

        return self.system_knowledge.inspect_truth_engine()

    def system_facts(self):
        """
        Zwraca wszystkie aktualnie znane
        i zweryfikowane fakty systemowe.
        """

        return self.system_knowledge.all_facts()

    def system_execution_facts(self):
        """
        Zwraca fakty ustalone przez rzeczywiste
        wykonanie kodu FENIKSA.
        """

        return self.system_knowledge.execution_facts()

    def system_code_facts(self):
        """
        Zwraca fakty ustalone przez inspekcjÄ™
        aktualnej implementacji systemu.
        """

        return self.system_knowledge.code_inspection_facts()

    # =====================================================
    # EKSPERYMENTY DIAGNOSTYCZNE
    # =====================================================

    def run_quantity_vs_quality_experiment(
        self,
        strong_support_reliability: float = 0.95,
        opposing_reliability: float = 0.50,
        max_opposing: int = 20,
    ) -> ExperimentResult:
        """
        Uruchamia rzeczywisty eksperyment badajÄ…cy
        relacjÄ™ liczby dowodĂłw do ich jakoĹ›ci.

        Eksperyment nie korzysta z modelu jÄ™zykowego
        do przewidywania wyniku.
        """

        return self.experiment_runner.run_quantity_vs_quality(
            strong_support_reliability=strong_support_reliability,
            opposing_reliability=opposing_reliability,
            max_opposing=max_opposing,
        )

    def experiment_history(self):
        """
        Zwraca eksperymenty wykonane podczas
        bieĹĽÄ…cego ĹĽycia obiektu Feniks.
        """

        return list(
            self.experiment_runner.experiments
        )

    # =====================================================
    # WALIDACJA ROZUMOWANIA
    # =====================================================

    def validate_experiment_interpretation(
        self,
        interpretation,
        result: ExperimentResult,
    ) -> ValidationReport:
        """
        Waliduje interpretacjÄ™ eksperymentu wzglÄ™dem
        twardych obserwacji i samowiedzy systemowej.

        Sama interpretacja nie staje siÄ™ faktem tylko
        dlatego, ĹĽe zostaĹ‚a wygenerowana przez model.
        """

        return (
            self.reasoning_validator
            .validate_experiment_interpretation(
                interpretation=interpretation,
                result=result,
            )
        )

    # =====================================================
    # PIERWSZE DOĹšWIADCZENIE ROZWOJOWE
    # =====================================================

    def create_first_development_experience(self):
        """
        Tworzy pierwszy rzeczywisty wpis
        dotyczÄ…cy rozwoju Silnika Prawdy.
        """

        entry = self.register_development(
            title=(
                "Nadmierna pewnoĹ›Ä‡ pierwszej wersji "
                "Silnika Prawdy"
            ),
            description=(
                "Pierwsza wersja algorytmu nadawaĹ‚a "
                "100% pewnoĹ›ci twierdzeniu, gdy istniaĹ‚y "
                "dowody wspierajÄ…ce i nie byĹ‚o dowodĂłw "
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
                "Test Silnika Prawdy zwrĂłciĹ‚ 100% "
                "pewnoĹ›ci przy dwĂłch dowodach "
                "o wiarygodnoĹ›ci 0.98 oraz 0.95."
            ),
        )

        self.development_log.add_change(
            entry,
            (
                "Algorytm zmieniono tak, aby "
                "uwzglÄ™dniaĹ‚ bilans dowodĂłw, "
                "ich Ĺ›redniÄ… jakoĹ›Ä‡ oraz liczbÄ™."
            ),
        )

        self.development_log.add_test_result(
            entry,
            (
                "Po zmianie to samo twierdzenie "
                "otrzymaĹ‚o 94% pewnoĹ›ci zamiast 100%."
            ),
        )

        self.development_log.add_unresolved(
            entry,
            (
                "NaleĹĽy rozdzieliÄ‡ siĹ‚Ä™ poparcia "
                "twierdzenia od pewnoĹ›ci klasyfikacji "
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
        Starsza nazwa zachowana dla zgodnoĹ›ci
        z wczeĹ›niejszym kodem.
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

        system_facts = self.system_knowledge.all_facts()

        execution_facts = (
            self.system_knowledge.execution_facts()
        )

        code_facts = (
            self.system_knowledge.code_inspection_facts()
        )

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

            # Poznawczy rdzeĹ„ diagnostyczny
            "samowiedza_systemowa_zaladowana": True,
            "fakty_systemowe":
                len(system_facts),
            "fakty_z_wykonania_kodu":
                len(execution_facts),
            "fakty_z_inspekcji_kodu":
                len(code_facts),

            "runner_eksperymentow_zaladowany": True,
            "wykonane_eksperymenty":
                len(self.experiment_runner.experiments),

            "walidator_rozumowania_zaladowany": True,
        }
