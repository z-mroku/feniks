from core.cognitive_cycle import (
    CognitiveCycle,
    CognitiveCycleResult,
)
from core.constitution import Constitution
from core.development_log import (
    DevelopmentCategory,
    DevelopmentLog,
    DevelopmentStatus,
)
from core.experiment_runner import ExperimentResult, ExperimentRunner
from core.experiment_interpreter import GeminiExperimentInterpreter
from core.guardian import Guardian
from core.knowledge_gate import (
    KnowledgeAdmissionResult,
    KnowledgeGate,
)
from core.knowledge_retriever import (
    KnowledgeContext,
    KnowledgeRetriever,
)
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
    GÄąâ€šÄ‚Ĺ‚wny rdzeÄąâ€ž FENIKS OS.

    ÄąÂĂ„â€¦czy wyspecjalizowane moduÄąâ€šy w jeden system.

    RdzeÄąâ€ž rozdziela:
    - dziaÄąâ€šanie operacyjne,
    - pamiĂ„â„˘Ă„â€ˇ,
    - ocenĂ„â„˘ prawdy,
    - historiĂ„â„˘ rozwoju,
    - samoanalizĂ„â„˘,
    - samowiedzĂ„â„˘ o dziaÄąâ€šaniu systemu,
    - eksperymenty diagnostyczne,
    - walidacjĂ„â„˘ interpretacji.
    """

    def __init__(self):
        # ToÄąÄ˝samoÄąâ€şĂ„â€ˇ
        self.identity = Identity()

        # Konstytucja
        self.constitution = Constitution()

        # StraÄąÄ˝nik
        self.guardian = Guardian(
            self.constitution
        )

        # PamiĂ„â„˘Ă„â€ˇ robocza
        self.memory = Memory(
            capacity=20
        )

        # TrwaÄąâ€ša pamiĂ„â„˘Ă„â€ˇ SQLite
        self.persistent_memory = PersistentMemory()

        # Silnik Prawdy
        self.truth_engine = TruthEngine()

        # Rejestr Rozwoju bieÄąÄ˝Ă„â€¦cej sesji
        self.development_log = DevelopmentLog()

        # Samoanaliza
        self.self_analysis = SelfAnalysis(
            persistent_memory=self.persistent_memory
        )

        # =================================================
        # POZNAWCZY RDZEÄąÂ DIAGNOSTYCZNY
        # =================================================

        # Jawna samowiedza FENIKSA o rzeczywistym
        # dziaÄąâ€šaniu jego wÄąâ€šasnych mechanizmÄ‚Ĺ‚w.
        self.system_knowledge = SystemKnowledge()

        # Wykonuje kontrolowane eksperymenty
        # na rzeczywistych komponentach systemu.
        self.experiment_runner = ExperimentRunner()

        # Sprawdza interpretacje wzglĂ„â„˘dem:
        # - obserwacji eksperymentalnych,
        # - wykonaniowej samowiedzy,
        # - wiedzy uzyskanej z inspekcji kodu.
        self.reasoning_validator = ReasoningValidator(
            system_knowledge=self.system_knowledge
        )

        # Produkcyjna warstwa interpretacji eksperymentĂłw.
        # Interpreter proponuje interpretacjÄ™,
        # ale nie podejmuje koĹ„cowej decyzji o wiedzy.
        self.experiment_interpreter = GeminiExperimentInterpreter()

        # PeĹ‚ny cykl poznawczy:
        # eksperyment -> interpretacja -> walidacja.
        self.cognitive_cycle = CognitiveCycle(
            interpreter=self.experiment_interpreter,
            system_knowledge=self.system_knowledge,
            experiment_runner=self.experiment_runner,
            reasoning_validator=self.reasoning_validator,
        )

        # Brama Wiedzy jest kontrolowanym przejĹ›ciem
        # od kandydata do wiedzy do trwaĹ‚ej pamiÄ™ci.
        self.knowledge_gate = KnowledgeGate(
            persistent_memory=self.persistent_memory
        )

        # Aktywny dostęp do wcześniej zweryfikowanej wiedzy.
        # Retriever przygotowuje kontekst, ale nie rozstrzyga
        # automatycznie nowego problemu.
        self.knowledge_retriever = KnowledgeRetriever(
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
                f"zostaÄąâ€š uruchomiony."
            ),
            source="system",
        )

        return (
            f"{self.name} v{self.version} "
            f"uruchomiony"
        )

    # =====================================================
    # TOÄąÂ»SAMOÄąĹˇĂ„â€  I KONSTYTUCJA
    # =====================================================

    def who_am_i(self):
        """
        Odczytuje wÄąâ€šasnĂ„â€¦ toÄąÄ˝samoÄąâ€şĂ„â€ˇ.
        """

        return self.identity.describe()

    def who_created_me(self):
        """
        Odczytuje informacje o twÄ‚Ĺ‚rcach projektu.
        """

        return self.identity.get_creators()

    def read_constitution(self):
        """
        Odczytuje KonstytucjĂ„â„˘.
        """

        return self.constitution.read_articles()

    # =====================================================
    # STRAÄąÂ»NIK
    # =====================================================

    def evaluate_action(
        self,
        action: str,
    ):
        """
        Przekazuje planowane dziaÄąâ€šanie do StraÄąÄ˝nika.
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
        Dodaje dowÄ‚Ĺ‚d dotyczĂ„â€¦cy twierdzenia.
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
    # PAMIĂ„ÂĂ„â€  ROBOCZA
    # =====================================================

    def remember(
        self,
        content: str,
        source: str = "uÄąÄ˝ytkownik",
    ):
        """
        Zapisuje informacjĂ„â„˘ w pamiĂ„â„˘ci roboczej.
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
        Odczytuje informacje z pamiĂ„â„˘ci roboczej.
        """

        return self.memory.recall(
            limit
        )

    # =====================================================
    # ZWYKÄąÂA PAMIĂ„ÂĂ„â€  TRWAÄąÂA
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
        Zapisuje informacjĂ„â„˘ w trwaÄąâ€šej pamiĂ„â„˘ci.
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
        Odczytuje ostatnie trwaÄąâ€še wspomnienia.
        """

        return self.persistent_memory.recent(
            limit=limit
        )

    def search_permanent_memory(
        self,
        phrase: str,
    ):
        """
        Przeszukuje trwaÄąâ€šĂ„â€¦ pamiĂ„â„˘Ă„â€ˇ.
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
        Rejestruje doÄąâ€şwiadczenie rozwojowe
        w pamiĂ„â„˘ci bieÄąÄ˝Ă„â€¦cej sesji.
        """

        return self.development_log.register(
            title=title,
            description=description,
            category=category,
            discovered_by=discovered_by,
        )

    def development_history(self):
        """
        Odczytuje historiĂ„â„˘ rozwoju bieÄąÄ˝Ă„â€¦cej sesji.
        """

        return self.development_log.history()

    # =====================================================
    # TRWAÄąÂA HISTORIA ROZWOJU
    # =====================================================

    def save_development_permanently(
        self,
        entry,
    ):
        """
        Zapisuje wpis Rejestru Rozwoju
        do trwaÄąâ€šej historii SQLite.
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
        Odczytuje trwaÄąâ€šĂ„â€¦ historiĂ„â„˘ rozwoju.
        """

        return self.persistent_memory.development_history(
            limit=limit
        )

    def unresolved_permanent_development(self):
        """
        Odczytuje trwaÄąâ€še wpisy posiadajĂ„â€¦ce
        nierozwiĂ„â€¦zane kwestie.
        """

        return self.persistent_memory.unresolved_development()

    # =====================================================
    # SAMOANALIZA
    # =====================================================

    def analyze_self(self):
        """
        Uruchamia samoanalizĂ„â„˘ FENIKSA na podstawie
        trwaÄąâ€šej historii rozwoju.

        Samoanaliza nie zmienia kodu systemu.
        """

        return self.self_analysis.analyze_development_history()

    def last_self_analysis(self):
        """
        Zwraca ostatni raport samoanalizy
        z bieÄąÄ˝Ă„â€¦cej sesji.
        """

        return self.self_analysis.last_report()

    # =====================================================
    # SAMOWIEDZA SYSTEMOWA
    # =====================================================

    def inspect_system_knowledge(self):
        """
        Uruchamia kontrolowane badanie wÄąâ€šasnego
        TruthEngine i aktualizuje jawnĂ„â€¦ samowiedzĂ„â„˘.

        Fakty pochodzĂ„â€¦ z rzeczywistego wykonania
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
        Zwraca fakty ustalone przez inspekcjĂ„â„˘
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
        Uruchamia rzeczywisty eksperyment badajĂ„â€¦cy
        relacjĂ„â„˘ liczby dowodÄ‚Ĺ‚w do ich jakoÄąâ€şci.

        Eksperyment nie korzysta z modelu jĂ„â„˘zykowego
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
        bieÄąÄ˝Ă„â€¦cego ÄąÄ˝ycia obiektu Feniks.
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
        Waliduje interpretacjĂ„â„˘ eksperymentu wzglĂ„â„˘dem
        twardych obserwacji i samowiedzy systemowej.

        Sama interpretacja nie staje siĂ„â„˘ faktem tylko
        dlatego, ÄąÄ˝e zostaÄąâ€ša wygenerowana przez model.
        """

        return (
            self.reasoning_validator
            .validate_experiment_interpretation(
                interpretation=interpretation,
                result=result,
            )
        )

    # =====================================================
    # PEĹNY CYKL POZNAWCZY
    # =====================================================

    def run_cognitive_cycle(
        self,
        hypothesis: str,
        strong_support_reliability: float = 0.95,
        opposing_reliability: float = 0.50,
        max_opposing: int = 20,
    ) -> CognitiveCycleResult:
        """
        Uruchamia peĹ‚ny cykl poznawczy FENIKSA:

        eksperyment -> interpretacja -> walidacja.

        Poprawny wynik moĹĽe staÄ‡ siÄ™ kandydatem
        do wiedzy, ale ta metoda nie zapisuje go
        automatycznie do trwaĹ‚ej pamiÄ™ci.
        """

        return self.cognitive_cycle.run_quantity_vs_quality(
            hypothesis=hypothesis,
            strong_support_reliability=strong_support_reliability,
            opposing_reliability=opposing_reliability,
            max_opposing=max_opposing,
        )

    # =====================================================
    # BRAMA WIEDZY
    # =====================================================

    def admit_knowledge(
        self,
        cycle_result: CognitiveCycleResult,
        title: str,
    ) -> KnowledgeAdmissionResult:
        """
        Przekazuje wynik cyklu poznawczego
        do Bramy Wiedzy.

        Brama ponownie sprawdza warunki przyjÄ™cia.
        Dopiero pozytywna decyzja Bramy moĹĽe
        spowodowaÄ‡ zapis zweryfikowanej wiedzy
        do trwaĹ‚ej pamiÄ™ci.
        """

        return self.knowledge_gate.admit(
            cycle_result=cycle_result,
            title=title,
        )

    # =====================================================
    # AKTYWNA PAMIĘĆ POZNAWCZA
    # =====================================================

    def retrieve_knowledge(
        self,
        query: str,
        limit: int | None = 10,
    ) -> KnowledgeContext:
        """Odnajduje bezpieczny kontekst wcześniejszej wiedzy."""

        return self.knowledge_retriever.retrieve(
            query=query,
            limit=limit,
        )

    def all_verified_knowledge(
        self,
        limit: int | None = None,
    ) -> KnowledgeContext:
        """Zwraca wcześniej dopuszczoną, zweryfikowaną wiedzę."""

        return self.knowledge_retriever.all_verified(
            limit=limit
        )

    # =====================================================
    # PIERWSZE DOÄąĹˇWIADCZENIE ROZWOJOWE
    # =====================================================

    def create_first_development_experience(self):
        """
        Tworzy pierwszy rzeczywisty wpis
        dotyczĂ„â€¦cy rozwoju Silnika Prawdy.
        """

        entry = self.register_development(
            title=(
                "Nadmierna pewnoÄąâ€şĂ„â€ˇ pierwszej wersji "
                "Silnika Prawdy"
            ),
            description=(
                "Pierwsza wersja algorytmu nadawaÄąâ€ša "
                "100% pewnoÄąâ€şci twierdzeniu, gdy istniaÄąâ€šy "
                "dowody wspierajĂ„â€¦ce i nie byÄąâ€šo dowodÄ‚Ĺ‚w "
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
                "Test Silnika Prawdy zwrÄ‚Ĺ‚ciÄąâ€š 100% "
                "pewnoÄąâ€şci przy dwÄ‚Ĺ‚ch dowodach "
                "o wiarygodnoÄąâ€şci 0.98 oraz 0.95."
            ),
        )

        self.development_log.add_change(
            entry,
            (
                "Algorytm zmieniono tak, aby "
                "uwzglĂ„â„˘dniaÄąâ€š bilans dowodÄ‚Ĺ‚w, "
                "ich Äąâ€şredniĂ„â€¦ jakoÄąâ€şĂ„â€ˇ oraz liczbĂ„â„˘."
            ),
        )

        self.development_log.add_test_result(
            entry,
            (
                "Po zmianie to samo twierdzenie "
                "otrzymaÄąâ€šo 94% pewnoÄąâ€şci zamiast 100%."
            ),
        )

        self.development_log.add_unresolved(
            entry,
            (
                "NaleÄąÄ˝y rozdzieliĂ„â€ˇ siÄąâ€šĂ„â„˘ poparcia "
                "twierdzenia od pewnoÄąâ€şci klasyfikacji "
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
        Starsza nazwa zachowana dla zgodnoÄąâ€şci
        z wczeÄąâ€şniejszym kodem.
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

            # Poznawczy rdzeÄąâ€ž diagnostyczny
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

            "interpreter_eksperymentow_zaladowany": True,
            "cykl_poznawczy_zaladowany": True,
            "brama_wiedzy_zaladowana": True,
            "retriever_wiedzy_zaladowany": True,
        }

