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
from core.knowledge_relevance_engine import (
    KnowledgeRelevanceEngine,
    RelevantKnowledgeResult,
)
from core.gemini_knowledge_relevance_provider import (
    GeminiKnowledgeRelevanceProvider,
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
    GĂ„Ä…Ă˘â‚¬ĹˇĂ„â€šÄąâ€šwny rdzeĂ„Ä…Ă˘â‚¬Ĺľ FENIKS OS.

    Ă„Ä…Ă‚ÂÄ‚â€žĂ˘â‚¬Â¦czy wyspecjalizowane moduĂ„Ä…Ă˘â‚¬Ĺˇy w jeden system.

    RdzeĂ„Ä…Ă˘â‚¬Ĺľ rozdziela:
    - dziaĂ„Ä…Ă˘â‚¬Ĺˇanie operacyjne,
    - pamiÄ‚â€žĂ˘â€žËÄ‚â€žĂ˘â‚¬Ë‡,
    - ocenÄ‚â€žĂ˘â€žË prawdy,
    - historiÄ‚â€žĂ˘â€žË rozwoju,
    - samoanalizÄ‚â€žĂ˘â€žË,
    - samowiedzÄ‚â€žĂ˘â€žË o dziaĂ„Ä…Ă˘â‚¬Ĺˇaniu systemu,
    - eksperymenty diagnostyczne,
    - walidacjÄ‚â€žĂ˘â€žË interpretacji.
    """

    def __init__(self):
        # ToĂ„Ä…Ă„ËťsamoĂ„Ä…Ă˘â‚¬ĹźÄ‚â€žĂ˘â‚¬Ë‡
        self.identity = Identity()

        # Konstytucja
        self.constitution = Constitution()

        # StraĂ„Ä…Ă„Ëťnik
        self.guardian = Guardian(
            self.constitution
        )

        # PamiÄ‚â€žĂ˘â€žËÄ‚â€žĂ˘â‚¬Ë‡ robocza
        self.memory = Memory(
            capacity=20
        )

        # TrwaĂ„Ä…Ă˘â‚¬Ĺˇa pamiÄ‚â€žĂ˘â€žËÄ‚â€žĂ˘â‚¬Ë‡ SQLite
        self.persistent_memory = PersistentMemory()

        # Silnik Prawdy
        self.truth_engine = TruthEngine()

        # Rejestr Rozwoju bieĂ„Ä…Ă„ËťÄ‚â€žĂ˘â‚¬Â¦cej sesji
        self.development_log = DevelopmentLog()

        # Samoanaliza
        self.self_analysis = SelfAnalysis(
            persistent_memory=self.persistent_memory
        )

        # =================================================
        # POZNAWCZY RDZEĂ„Ä…Ă‚Â DIAGNOSTYCZNY
        # =================================================

        # Jawna samowiedza FENIKSA o rzeczywistym
        # dziaĂ„Ä…Ă˘â‚¬Ĺˇaniu jego wĂ„Ä…Ă˘â‚¬Ĺˇasnych mechanizmĂ„â€šÄąâ€šw.
        self.system_knowledge = SystemKnowledge()

        # Wykonuje kontrolowane eksperymenty
        # na rzeczywistych komponentach systemu.
        self.experiment_runner = ExperimentRunner()

        # Sprawdza interpretacje wzglÄ‚â€žĂ˘â€žËdem:
        # - obserwacji eksperymentalnych,
        # - wykonaniowej samowiedzy,
        # - wiedzy uzyskanej z inspekcji kodu.
        self.reasoning_validator = ReasoningValidator(
            system_knowledge=self.system_knowledge
        )

        # Produkcyjna warstwa interpretacji eksperymentÄ‚Ĺ‚w.
        # Interpreter proponuje interpretacjĂ„â„˘,
        # ale nie podejmuje koÄąâ€žcowej decyzji o wiedzy.
        self.experiment_interpreter = GeminiExperimentInterpreter()

        # PeÄąâ€šny cykl poznawczy:
        # eksperyment -> interpretacja -> walidacja.
        self.cognitive_cycle = CognitiveCycle(
            interpreter=self.experiment_interpreter,
            system_knowledge=self.system_knowledge,
            experiment_runner=self.experiment_runner,
            reasoning_validator=self.reasoning_validator,
        )

        # Brama Wiedzy jest kontrolowanym przejÄąâ€şciem
        # od kandydata do wiedzy do trwaÄąâ€šej pamiĂ„â„˘ci.
        self.knowledge_gate = KnowledgeGate(
            persistent_memory=self.persistent_memory
        )

        # Aktywny dostÄ™p do wczeĹ›niej zweryfikowanej wiedzy.
        # Retriever przygotowuje kontekst, ale nie rozstrzyga
        # automatycznie nowego problemu.
        self.knowledge_retriever = KnowledgeRetriever(
            persistent_memory=self.persistent_memory
        )

        # Produkcyjna warstwa semantycznej oceny trafności.
        # Gemini może wyłącznie oceniać rekordy dopuszczone
        # wcześniej przez KnowledgeRetriever.
        self.knowledge_relevance_provider = (
            GeminiKnowledgeRelevanceProvider()
        )

        # Silnik semantycznego przypominania wiedzy.
        # Ostateczna selekcja pozostaje po stronie kodu FENIKSA.
        self.knowledge_relevance_engine = KnowledgeRelevanceEngine(
            knowledge_retriever=self.knowledge_retriever,
            provider=self.knowledge_relevance_provider,
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
                f"zostaĂ„Ä…Ă˘â‚¬Ĺˇ uruchomiony."
            ),
            source="system",
        )

        return (
            f"{self.name} v{self.version} "
            f"uruchomiony"
        )

    # =====================================================
    # TOĂ„Ä…Ă‚Â»SAMOĂ„Ä…ÄąË‡Ä‚â€žĂ˘â‚¬Â  I KONSTYTUCJA
    # =====================================================

    def who_am_i(self):
        """
        Odczytuje wĂ„Ä…Ă˘â‚¬ĹˇasnÄ‚â€žĂ˘â‚¬Â¦ toĂ„Ä…Ă„ËťsamoĂ„Ä…Ă˘â‚¬ĹźÄ‚â€žĂ˘â‚¬Ë‡.
        """

        return self.identity.describe()

    def who_created_me(self):
        """
        Odczytuje informacje o twĂ„â€šÄąâ€šrcach projektu.
        """

        return self.identity.get_creators()

    def read_constitution(self):
        """
        Odczytuje KonstytucjÄ‚â€žĂ˘â€žË.
        """

        return self.constitution.read_articles()

    # =====================================================
    # STRAĂ„Ä…Ă‚Â»NIK
    # =====================================================

    def evaluate_action(
        self,
        action: str,
    ):
        """
        Przekazuje planowane dziaĂ„Ä…Ă˘â‚¬Ĺˇanie do StraĂ„Ä…Ă„Ëťnika.
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
        Dodaje dowĂ„â€šÄąâ€šd dotyczÄ‚â€žĂ˘â‚¬Â¦cy twierdzenia.
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
    # PAMIÄ‚â€žĂ‚ÂÄ‚â€žĂ˘â‚¬Â  ROBOCZA
    # =====================================================

    def remember(
        self,
        content: str,
        source: str = "uĂ„Ä…Ă„Ëťytkownik",
    ):
        """
        Zapisuje informacjÄ‚â€žĂ˘â€žË w pamiÄ‚â€žĂ˘â€žËci roboczej.
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
        Odczytuje informacje z pamiÄ‚â€žĂ˘â€žËci roboczej.
        """

        return self.memory.recall(
            limit
        )

    # =====================================================
    # ZWYKĂ„Ä…Ă‚ÂA PAMIÄ‚â€žĂ‚ÂÄ‚â€žĂ˘â‚¬Â  TRWAĂ„Ä…Ă‚ÂA
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
        Zapisuje informacjÄ‚â€žĂ˘â€žË w trwaĂ„Ä…Ă˘â‚¬Ĺˇej pamiÄ‚â€žĂ˘â€žËci.
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
        Odczytuje ostatnie trwaĂ„Ä…Ă˘â‚¬Ĺˇe wspomnienia.
        """

        return self.persistent_memory.recent(
            limit=limit
        )

    def search_permanent_memory(
        self,
        phrase: str,
    ):
        """
        Przeszukuje trwaĂ„Ä…Ă˘â‚¬ĹˇÄ‚â€žĂ˘â‚¬Â¦ pamiÄ‚â€žĂ˘â€žËÄ‚â€žĂ˘â‚¬Ë‡.
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
        Rejestruje doĂ„Ä…Ă˘â‚¬Ĺźwiadczenie rozwojowe
        w pamiÄ‚â€žĂ˘â€žËci bieĂ„Ä…Ă„ËťÄ‚â€žĂ˘â‚¬Â¦cej sesji.
        """

        return self.development_log.register(
            title=title,
            description=description,
            category=category,
            discovered_by=discovered_by,
        )

    def development_history(self):
        """
        Odczytuje historiÄ‚â€žĂ˘â€žË rozwoju bieĂ„Ä…Ă„ËťÄ‚â€žĂ˘â‚¬Â¦cej sesji.
        """

        return self.development_log.history()

    # =====================================================
    # TRWAĂ„Ä…Ă‚ÂA HISTORIA ROZWOJU
    # =====================================================

    def save_development_permanently(
        self,
        entry,
    ):
        """
        Zapisuje wpis Rejestru Rozwoju
        do trwaĂ„Ä…Ă˘â‚¬Ĺˇej historii SQLite.
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
        Odczytuje trwaĂ„Ä…Ă˘â‚¬ĹˇÄ‚â€žĂ˘â‚¬Â¦ historiÄ‚â€žĂ˘â€žË rozwoju.
        """

        return self.persistent_memory.development_history(
            limit=limit
        )

    def unresolved_permanent_development(self):
        """
        Odczytuje trwaĂ„Ä…Ă˘â‚¬Ĺˇe wpisy posiadajÄ‚â€žĂ˘â‚¬Â¦ce
        nierozwiÄ‚â€žĂ˘â‚¬Â¦zane kwestie.
        """

        return self.persistent_memory.unresolved_development()

    # =====================================================
    # SAMOANALIZA
    # =====================================================

    def analyze_self(self):
        """
        Uruchamia samoanalizÄ‚â€žĂ˘â€žË FENIKSA na podstawie
        trwaĂ„Ä…Ă˘â‚¬Ĺˇej historii rozwoju.

        Samoanaliza nie zmienia kodu systemu.
        """

        return self.self_analysis.analyze_development_history()

    def last_self_analysis(self):
        """
        Zwraca ostatni raport samoanalizy
        z bieĂ„Ä…Ă„ËťÄ‚â€žĂ˘â‚¬Â¦cej sesji.
        """

        return self.self_analysis.last_report()

    # =====================================================
    # SAMOWIEDZA SYSTEMOWA
    # =====================================================

    def inspect_system_knowledge(self):
        """
        Uruchamia kontrolowane badanie wĂ„Ä…Ă˘â‚¬Ĺˇasnego
        TruthEngine i aktualizuje jawnÄ‚â€žĂ˘â‚¬Â¦ samowiedzÄ‚â€žĂ˘â€žË.

        Fakty pochodzÄ‚â€žĂ˘â‚¬Â¦ z rzeczywistego wykonania
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
        Zwraca fakty ustalone przez inspekcjÄ‚â€žĂ˘â€žË
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
        Uruchamia rzeczywisty eksperyment badajÄ‚â€žĂ˘â‚¬Â¦cy
        relacjÄ‚â€žĂ˘â€žË liczby dowodĂ„â€šÄąâ€šw do ich jakoĂ„Ä…Ă˘â‚¬Ĺźci.

        Eksperyment nie korzysta z modelu jÄ‚â€žĂ˘â€žËzykowego
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
        bieĂ„Ä…Ă„ËťÄ‚â€žĂ˘â‚¬Â¦cego Ă„Ä…Ă„Ëťycia obiektu Feniks.
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
        Waliduje interpretacjÄ‚â€žĂ˘â€žË eksperymentu wzglÄ‚â€žĂ˘â€žËdem
        twardych obserwacji i samowiedzy systemowej.

        Sama interpretacja nie staje siÄ‚â€žĂ˘â€žË faktem tylko
        dlatego, Ă„Ä…Ă„Ëťe zostaĂ„Ä…Ă˘â‚¬Ĺˇa wygenerowana przez model.
        """

        return (
            self.reasoning_validator
            .validate_experiment_interpretation(
                interpretation=interpretation,
                result=result,
            )
        )

    # =====================================================
    # PEÄąÂNY CYKL POZNAWCZY
    # =====================================================

    def run_cognitive_cycle(
        self,
        hypothesis: str,
        strong_support_reliability: float = 0.95,
        opposing_reliability: float = 0.50,
        max_opposing: int = 20,
    ) -> CognitiveCycleResult:
        """
        Uruchamia peÄąâ€šny cykl poznawczy FENIKSA:

        eksperyment -> interpretacja -> walidacja.

        Poprawny wynik moÄąÄ˝e staĂ„â€ˇ siĂ„â„˘ kandydatem
        do wiedzy, ale ta metoda nie zapisuje go
        automatycznie do trwaÄąâ€šej pamiĂ„â„˘ci.
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

        Brama ponownie sprawdza warunki przyjĂ„â„˘cia.
        Dopiero pozytywna decyzja Bramy moÄąÄ˝e
        spowodowaĂ„â€ˇ zapis zweryfikowanej wiedzy
        do trwaÄąâ€šej pamiĂ„â„˘ci.
        """

        return self.knowledge_gate.admit(
            cycle_result=cycle_result,
            title=title,
        )

    # =====================================================
    # AKTYWNA PAMIÄÄ† POZNAWCZA
    # =====================================================

    def retrieve_knowledge(
        self,
        query: str,
        limit: int | None = 10,
    ) -> KnowledgeContext:
        """Odnajduje bezpieczny kontekst wczeĹ›niejszej wiedzy."""

        return self.knowledge_retriever.retrieve(
            query=query,
            limit=limit,
        )

    def all_verified_knowledge(
        self,
        limit: int | None = None,
    ) -> KnowledgeContext:
        """Zwraca wczeĹ›niej dopuszczonÄ…, zweryfikowanÄ… wiedzÄ™."""

        return self.knowledge_retriever.all_verified(
            limit=limit
        )

    def recall_relevant_knowledge(
        self,
        problem: str,
        limit: int | None = 5,
    ) -> RelevantKnowledgeResult:
        """
        Dobiera wcześniej zweryfikowaną wiedzę
        do znaczenia nowego problemu.

        Provider semantyczny ocenia trafność,
        ale nie może ominąć KnowledgeRetriever
        ani zapisać czegokolwiek do pamięci.
        """

        return self.knowledge_relevance_engine.select(
            problem=problem,
            limit=limit,
        )

    # =====================================================
    # PIERWSZE DOĂ„Ä…ÄąË‡WIADCZENIE ROZWOJOWE
    # =====================================================

    def create_first_development_experience(self):
        """
        Tworzy pierwszy rzeczywisty wpis
        dotyczÄ‚â€žĂ˘â‚¬Â¦cy rozwoju Silnika Prawdy.
        """

        entry = self.register_development(
            title=(
                "Nadmierna pewnoĂ„Ä…Ă˘â‚¬ĹźÄ‚â€žĂ˘â‚¬Ë‡ pierwszej wersji "
                "Silnika Prawdy"
            ),
            description=(
                "Pierwsza wersja algorytmu nadawaĂ„Ä…Ă˘â‚¬Ĺˇa "
                "100% pewnoĂ„Ä…Ă˘â‚¬Ĺźci twierdzeniu, gdy istniaĂ„Ä…Ă˘â‚¬Ĺˇy "
                "dowody wspierajÄ‚â€žĂ˘â‚¬Â¦ce i nie byĂ„Ä…Ă˘â‚¬Ĺˇo dowodĂ„â€šÄąâ€šw "
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
                "Test Silnika Prawdy zwrĂ„â€šÄąâ€šciĂ„Ä…Ă˘â‚¬Ĺˇ 100% "
                "pewnoĂ„Ä…Ă˘â‚¬Ĺźci przy dwĂ„â€šÄąâ€šch dowodach "
                "o wiarygodnoĂ„Ä…Ă˘â‚¬Ĺźci 0.98 oraz 0.95."
            ),
        )

        self.development_log.add_change(
            entry,
            (
                "Algorytm zmieniono tak, aby "
                "uwzglÄ‚â€žĂ˘â€žËdniaĂ„Ä…Ă˘â‚¬Ĺˇ bilans dowodĂ„â€šÄąâ€šw, "
                "ich Ă„Ä…Ă˘â‚¬ĹźredniÄ‚â€žĂ˘â‚¬Â¦ jakoĂ„Ä…Ă˘â‚¬ĹźÄ‚â€žĂ˘â‚¬Ë‡ oraz liczbÄ‚â€žĂ˘â€žË."
            ),
        )

        self.development_log.add_test_result(
            entry,
            (
                "Po zmianie to samo twierdzenie "
                "otrzymaĂ„Ä…Ă˘â‚¬Ĺˇo 94% pewnoĂ„Ä…Ă˘â‚¬Ĺźci zamiast 100%."
            ),
        )

        self.development_log.add_unresolved(
            entry,
            (
                "NaleĂ„Ä…Ă„Ëťy rozdzieliÄ‚â€žĂ˘â‚¬Ë‡ siĂ„Ä…Ă˘â‚¬ĹˇÄ‚â€žĂ˘â€žË poparcia "
                "twierdzenia od pewnoĂ„Ä…Ă˘â‚¬Ĺźci klasyfikacji "
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
        Starsza nazwa zachowana dla zgodnoĂ„Ä…Ă˘â‚¬Ĺźci
        z wczeĂ„Ä…Ă˘â‚¬Ĺźniejszym kodem.
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

            # Poznawczy rdzeĂ„Ä…Ă˘â‚¬Ĺľ diagnostyczny
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
            "provider_trafnosci_wiedzy_zaladowany": True,
            "silnik_trafnosci_wiedzy_zaladowany": True,
        }


