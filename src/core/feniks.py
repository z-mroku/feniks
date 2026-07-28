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
from core.cognitive_orchestrator import CognitiveOrchestrator
from core.cognitive_executor import CognitiveExecutor
from core.response_engine import ResponseEngine, HumanResponse
from core.reasoning_engine import ReasoningProblem, ReasoningEngine
from core.reasoning_provider import (
    GeminiReasoningProvider,
    ReasoningMode,
    ReasoningResult as ProviderReasoningResult,
)
from core.reasoning_validator import (
    ValidationReport,
    ReasoningValidator,
)
from core.self_analysis import SelfAnalysis
from core.system_knowledge import SystemKnowledge
from core.truth_engine import Claim, Evidence, TruthEngine


class Feniks:
    """
    Główny rdzeń FENIKS OS.

    Łączy wyspecjalizowane moduły w jeden system.

    Rdzeń rozdziela:
    - działanie operacyjne,
    - pamięć,
    - ocenę prawdy,
    - historię rozwoju,
    - samoanalizę,
    - samowiedzę o działaniu systemu,
    - eksperymenty diagnostyczne,
    - walidację interpretacji.
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

        # =================================================
        # POZNAWCZY RDZEŃ DIAGNOSTYCZNY
        # =================================================

        # Jawna samowiedza FENIKSA o rzeczywistym
        # działaniu jego własnych mechanizmów.
        self.system_knowledge = SystemKnowledge()

        # Wykonuje kontrolowane eksperymenty
        # na rzeczywistych komponentach systemu.
        self.experiment_runner = ExperimentRunner()

        # Sprawdza interpretacje względem:
        # - obserwacji eksperymentalnych,
        # - wykonaniowej samowiedzy,
        # - wiedzy uzyskanej z inspekcji kodu.
        self.reasoning_validator = ReasoningValidator(
            system_knowledge=self.system_knowledge
        )

        # Produkcyjna warstwa interpretacji eksperymentów.
        # Interpreter proponuje interpretację,
        # ale nie podejmuje końcowej decyzji o wiedzy.
        self.experiment_interpreter = GeminiExperimentInterpreter()

        # Pełny cykl poznawczy:
        # eksperyment -> interpretacja -> walidacja.
        self.cognitive_cycle = CognitiveCycle(
            interpreter=self.experiment_interpreter,
            system_knowledge=self.system_knowledge,
            experiment_runner=self.experiment_runner,
            reasoning_validator=self.reasoning_validator,
        )

        # Brama Wiedzy jest kontrolowanym przejściem
        # od kandydata do wiedzy do trwałej pamięci.
        self.knowledge_gate = KnowledgeGate(
            persistent_memory=self.persistent_memory
        )

        # Aktywny dostęp do wcześniej zweryfikowanej wiedzy.
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

        # Strukturalny silnik rozumowania nie zgaduje semantyki.
        self.reasoning_engine = ReasoningEngine()

        # Orkiestrator wybiera dalsza droge poznawcza.
        # Nie rozstrzyga prawdy i nie zapisuje wiedzy.
        self.cognitive_orchestrator = CognitiveOrchestrator(
            reasoning_engine=self.reasoning_engine,
        )

        # Wykonuje bezpieczny następny krok wybrany przez orkiestrator.
        self.cognitive_executor = CognitiveExecutor(
            orchestrator=self.cognitive_orchestrator,
            reason_callback=self.reason_about_problem,
        )

        # Warstwa odpowiedzi dla człowieka.
        self.response_engine = ResponseEngine()

        # Zewnętrzna warstwa semantycznego rozumowania.
        # Wynik jest propozycją analizy, nie źródłem prawdy.
        self.reasoning_provider = GeminiReasoningProvider()

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
    # SAMOWIEDZA SYSTEMOWA
    # =====================================================

    def inspect_system_knowledge(self):
        """
        Uruchamia kontrolowane badanie własnego
        TruthEngine i aktualizuje jawną samowiedzę.

        Fakty pochodzą z rzeczywistego wykonania
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
        Zwraca fakty ustalone przez inspekcję
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
        Uruchamia rzeczywisty eksperyment badający
        relację liczby dowodów do ich jakości.

        Eksperyment nie korzysta z modelu językowego
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
        bieżącego życia obiektu Feniks.

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
        Waliduje interpretację eksperymentu względem
        twardych obserwacji i samowiedzy systemowej.

        Sama interpretacja nie staje się faktem tylko
        dlatego, że została wygenerowana przez model.

        """

        return (
            self.reasoning_validator
            .validate_experiment_interpretation(
                interpretation=interpretation,
                result=result,
            )
        )

    # =====================================================
    # PEŁNY CYKL POZNAWCZY
    # =====================================================

    def run_cognitive_cycle(
        self,
        hypothesis: str,
        strong_support_reliability: float = 0.95,
        opposing_reliability: float = 0.50,
        max_opposing: int = 20,
        knowledge_limit: int | None = 5,
    ) -> CognitiveCycleResult:
        """
        Uruchamia pełny cykl poznawczy FENIKSA.

        Przed eksperymentem FENIKS semantycznie dobiera wcześniejszą
        zweryfikowaną wiedzę. Jest ona osobnym kontekstem pomocniczym,
        a nie częścią hipotezy ani obserwacją bieżącego eksperymentu.
        """

        relevant_knowledge = self.recall_relevant_knowledge(
            problem=hypothesis,
            limit=knowledge_limit,
        )

        prior_knowledge_context = (
            relevant_knowledge.context.as_text()
            if relevant_knowledge.context.records
            else ""
        )

        return self.cognitive_cycle.run_quantity_vs_quality(
            hypothesis=hypothesis,
            strong_support_reliability=strong_support_reliability,
            opposing_reliability=opposing_reliability,
            max_opposing=max_opposing,
            prior_knowledge_context=prior_knowledge_context,
        )

    # =====================================================
    # ROZUMOWANIE NAD NOWYM PROBLEMEM
    # =====================================================

    def reason_about_problem(
        self,
        problem: ReasoningProblem,
        mode: ReasoningMode = ReasoningMode.DIAGNOSIS,
        knowledge_limit: int | None = 5,
    ) -> ProviderReasoningResult:
        """Analizuje nowy problem z bezpiecznym kontekstem wcześniejszej wiedzy."""
        if not isinstance(problem, ReasoningProblem):
            raise TypeError("problem musi być obiektem ReasoningProblem.")

        self.reasoning_engine.analyze(problem)

        semantic_query = "\n".join(
            part.strip()
            for part in (problem.title, problem.description)
            if part and part.strip()
        )

        relevant = self.recall_relevant_knowledge(
            problem=semantic_query,
            limit=knowledge_limit,
        )

        history = list(problem.history)
        if relevant.context.records:
            history.append(
                "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA FENIKSA "
                "(KONTEKST, NIE BIEŻĄCY DOWÓD):\n"
                + relevant.context.as_text()
            )

        return self.reasoning_provider.analyze(
            title=problem.title,
            description=problem.description,
            evidence=list(problem.evidence),
            unknowns=list(problem.unknowns),
            history=history,
            mode=mode,
        )

    # =====================================================
    # BRAMA WIEDZY
    # =====================================================

    def admit_knowledge(
        self,
        cycle_result: CognitiveCycleResult,
        title: str,
    ) -> KnowledgeAdmissionResult:
        '\n        Przekazuje wynik cyklu poznawczego\n        do Bramy Wiedzy.\n\n        Brama ponownie sprawdza warunki przyjęcia.\n        Dopiero pozytywna decyzja Bramy może\n        spowodować zapis zweryfikowanej wiedzy\n        do trwałej pamięci.\n        '

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
        'Odnajduje bezpieczny kontekst wcześniejszej wiedzy.'
        return self.knowledge_retriever.retrieve(
            query=query,
            limit=limit,
        )

    def all_verified_knowledge(
        self,
        limit: int | None = None,
    ) -> KnowledgeContext:
        'Zwraca wcześniej dopuszczoną, zweryfikowaną wiedzę.'
        return self.knowledge_retriever.all_verified(
            limit=limit
        )

    def recall_relevant_knowledge(
        self,
        problem: str,
        limit: int | None = 5,
    ) -> RelevantKnowledgeResult:
        '\n        Dobiera wcześniej zweryfikowaną wiedzę\n        do znaczenia nowego problemu.\n\n        Provider semantyczny ocenia trafność,\n        ale nie może ominąć KnowledgeRetriever\n        ani zapisać czegokolwiek do pamięci.\n        '

        return self.knowledge_relevance_engine.select(
            problem=problem,
            limit=limit,
        )

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

    def respond_to_problem(
        self,
        problem: ReasoningProblem,
        mode: ReasoningMode = ReasoningMode.DIAGNOSIS,
        knowledge_limit: int | None = 5,
    ) -> HumanResponse:
        # Pełny obecny łańcuch: decyzja -> wykonanie -> odpowiedź dla człowieka.
        execution = self.cognitive_executor.execute(
            problem=problem,
            mode=mode,
            knowledge_limit=knowledge_limit,
        )
        return self.response_engine.respond(execution)

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

            # Poznawczy rdzeń diagnostyczny
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
            "orkiestrator_poznawczy_zaladowany": True,
            "decyzje_orkiestratora":
                self.cognitive_orchestrator.stats()["liczba_decyzji"],
            "wykonawca_poznawczy_zaladowany": True,
            "wykonania_poznawcze": self.cognitive_executor.stats()["liczba_wykonan"],
            "warstwa_odpowiedzi_zaladowana": True,
            "odpowiedzi_dla_czlowieka":
                self.response_engine.stats()["liczba_odpowiedzi"],
        }



