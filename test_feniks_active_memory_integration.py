import gc
from pathlib import Path

from core.cognitive_cycle import CognitiveCycle
from core.experiment_interpreter import ExperimentInterpretation, HypothesisStatus
from core.feniks import Feniks
from core.knowledge_gate import KnowledgeGate
from core.persistent_memory import PersistentMemory


TEST_DATABASE = Path("data") / "feniks_active_memory_integration_test.db"


class ControlledCorrectInterpreter:
    """Deterministyczny interpreter testowy - bez Gemini i bez sieci."""

    def interpret(self, hypothesis, result):
        return ExperimentInterpretation(
            hypothesis_status=HypothesisStatus.REJECTED,
            reasoning=(
                "W przebadanym zakresie liczba przeciętnych dowodów "
                "przeciwnych nie doprowadziła do przewagi sprzeciwu "
                "nad poparciem."
            ),
            new_findings=[
                "Sprzeczność pojawiła się już przy N=1.",
                "Siła sprzeciwu wykazuje saturację od N=3.",
            ],
            remaining_unknowns=[],
            alternative_explanations=[],
            next_experiment_question=(
                "Czy wynik pozostanie taki sam dla innych "
                "poziomów wiarygodności?"
            ),
            next_experiment=(
                "Powtórzyć eksperyment dla innych kontrolowanych "
                "wartości wiarygodności."
            ),
            cannot_conclude_yet=[
                "Nie należy uogólniać wyniku poza zakres "
                "przebadanych parametrów."
            ],
            confidence=0.95,
        )


def check(name, condition, failures):
    passed = bool(condition)
    print(f"{name}: {'TAK' if passed else 'NIE'}")
    if not passed:
        failures.append(name)


def remove_database():
    gc.collect()
    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()


def main():
    failures = []

    print("=" * 90)
    print("TEST AKTYWNEJ PAMIĘCI W GŁÓWNYM RDZENIU FENIKSA")
    print("=" * 90)

    remove_database()

    feniks = None
    test_memory = None

    try:
        print()
        print("ETAP 1 - URUCHOMIENIE GŁÓWNEGO FENIKSA")
        print("-" * 90)

        feniks = Feniks()

        check("Feniks został utworzony", feniks is not None, failures)
        check(
            "KnowledgeRetriever jest częścią Feniksa",
            hasattr(feniks, "knowledge_retriever"),
            failures,
        )
        check(
            "Feniks udostępnia retrieve_knowledge",
            callable(getattr(feniks, "retrieve_knowledge", None)),
            failures,
        )
        check(
            "Feniks udostępnia all_verified_knowledge",
            callable(getattr(feniks, "all_verified_knowledge", None)),
            failures,
        )
        check(
            "Status widzi KnowledgeRetriever",
            feniks.status().get("retriever_wiedzy_zaladowany") is True,
            failures,
        )

        print()
        print("ETAP 2 - IZOLACJA PAMIĘCI TESTOWEJ")
        print("-" * 90)

        test_memory = PersistentMemory(database_path=str(TEST_DATABASE))

        # Podmieniamy wyłącznie warstwę pamięci w tej instancji testowej.
        # Nie dotykamy rzeczywistej bazy FENIKSA.
        feniks.persistent_memory = test_memory
        feniks.knowledge_gate = KnowledgeGate(
            persistent_memory=test_memory
        )
        feniks.knowledge_retriever.persistent_memory = test_memory

        check(
            "KnowledgeGate używa izolowanej pamięci",
            feniks.knowledge_gate.persistent_memory is test_memory,
            failures,
        )
        check(
            "KnowledgeRetriever używa tej samej izolowanej pamięci",
            feniks.knowledge_retriever.persistent_memory is test_memory,
            failures,
        )
        check(
            "Izolowana baza jest początkowo pusta",
            test_memory.count() == 0,
            failures,
        )

        print()
        print("ETAP 3 - ZDOBYCIE WIEDZY PRZEZ CYKL POZNAWCZY")
        print("-" * 90)

        # Używamy współdzielonych komponentów głównego Feniksa,
        # ale kontrolowanego interpretera, aby test był deterministyczny.
        test_cycle = CognitiveCycle(
            interpreter=ControlledCorrectInterpreter(),
            system_knowledge=feniks.system_knowledge,
            experiment_runner=feniks.experiment_runner,
            reasoning_validator=feniks.reasoning_validator,
        )

        cycle_result = test_cycle.run_quantity_vs_quality(
            hypothesis=(
                "Rosnąca liczba przeciętnych dowodów przeciwnych "
                "ostatecznie przewyższy jeden mocny dowód wspierający."
            ),
            strong_support_reliability=0.95,
            opposing_reliability=0.50,
            max_opposing=4,
        )

        check(
            "Cykl utworzył kandydata do wiedzy",
            cycle_result.decision.value == "KANDYDAT_DO_WIEDZY",
            failures,
        )
        check(
            "Walidator dopuścił interpretację",
            cycle_result.validation_report.safe_for_memory is True,
            failures,
        )
        check(
            "Sam cykl nadal niczego nie zapisał",
            test_memory.count() == 0,
            failures,
        )

        print()
        print("ETAP 4 - ZAPIS PRZEZ BRAMĘ WIEDZY FENIKSA")
        print("-" * 90)

        admission = feniks.knowledge_gate.admit(
            cycle_result=cycle_result,
            title="TruthEngine aktywna pamięć Feniksa",
        )

        check(
            "Brama Wiedzy dopuściła rekord",
            admission.admitted is True,
            failures,
        )
        check(
            "Powstał trwały identyfikator rekordu",
            admission.memory_id is not None,
            failures,
        )
        check(
            "Po Bramie istnieje dokładnie jeden rekord",
            test_memory.count() == 1,
            failures,
        )

        valid_id = admission.memory_id

        print()
        print("ETAP 5 - FENIKS ODZYSKUJE WŁASNĄ WIEDZĘ")
        print("-" * 90)

        context = feniks.retrieve_knowledge("TruthEngine")

        print("Liczba odzyskanych rekordów:", context.count)

        check("Feniks znalazł wcześniejszą wiedzę", context.found, failures)
        check(
            "Feniks odzyskał dokładnie jeden rekord",
            context.count == 1,
            failures,
        )
        check(
            "Odzyskany rekord jest tym samym rekordem",
            (
                context.records[0].memory_id == valid_id
                if context.records
                else False
            ),
            failures,
        )
        check(
            "Odzyskany rekord zachował status ADMITTED",
            (
                context.records[0].metadata.get("knowledge_status") == "ADMITTED"
                if context.records
                else False
            ),
            failures,
        )
        check(
            "Odzyskany rekord zachował pełne pochodzenie",
            (
                context.records[0].provenance
                == (
                    "ExperimentRunner",
                    "ExperimentInterpreter",
                    "ReasoningValidator",
                    "KnowledgeGate",
                )
                if context.records
                else False
            ),
            failures,
        )

        print()
        print("ETAP 6 - PRÓBA PODSZYCIA SIĘ POD WIEDZĘ")
        print("-" * 90)

        fake_id = test_memory.save(
            category=KnowledgeGate.KNOWLEDGE_CATEGORY,
            title="TruthEngine fałszywa wiedza",
            content=(
                "Ten rekord zawiera frazę TruthEngine, ale nie przeszedł "
                "pełnej ścieżki walidacji."
            ),
            source="RECZNY_WPIS",
            metadata={
                "knowledge_status": "ADMITTED",
                "validation_safe_for_memory": True,
                "false_unknowns": 0,
                "conflicts": 0,
                "unverifiable": 0,
                "provenance": [
                    "ExperimentRunner",
                    "ExperimentInterpreter",
                    "ReasoningValidator",
                    "KnowledgeGate",
                ],
            },
        )

        context_after_attack = feniks.retrieve_knowledge("TruthEngine")
        returned_ids = [
            record.memory_id
            for record in context_after_attack.records
        ]

        check(
            "Fałszywy rekord istnieje fizycznie w SQLite",
            test_memory.get(fake_id) is not None,
            failures,
        )
        check(
            "Feniks nie uznał fałszywego rekordu za wiedzę",
            fake_id not in returned_ids,
            failures,
        )
        check(
            "Po ataku nadal odzyskiwany jest tylko prawdziwy rekord",
            context_after_attack.count == 1,
            failures,
        )

        print()
        print("ETAP 7 - KONTROLA KONTEKSTU DLA NOWEGO ROZUMOWANIA")
        print("-" * 90)

        context_text = context_after_attack.as_text()

        check(
            "Kontekst jawnie oznacza wcześniejszą wiedzę",
            "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA" in context_text,
            failures,
        )
        check(
            "Kontekst nie przedstawia pamięci jako automatycznego rozstrzygnięcia",
            "Nie stanowią automatycznego rozstrzygnięcia" in context_text,
            failures,
        )
        check(
            "Kontekst zawiera dane eksperymentalne",
            "DANE EKSPERYMENTALNE" in context_text,
            failures,
        )
        check(
            "Kontekst zachowuje granice wnioskowania",
            "GRANICE WNIOSKOWANIA" in context_text,
            failures,
        )

        print()
        print("ETAP 8 - ODCZYT CAŁEJ ZWERYFIKOWANEJ WIEDZY")
        print("-" * 90)

        all_verified = feniks.all_verified_knowledge()

        check(
            "Feniks widzi dokładnie jeden bezpieczny rekord wiedzy",
            all_verified.count == 1,
            failures,
        )
        check(
            "Odczyt całej wiedzy również odrzuca podszyty rekord",
            (
                all_verified.records[0].memory_id == valid_id
                if all_verified.records
                else False
            ),
            failures,
        )

        feniks = None
        test_memory = None
        gc.collect()

    finally:
        feniks = None
        test_memory = None
        gc.collect()
        remove_database()

    print()
    print("=" * 90)

    if failures:
        print("WERDYKT: TEST AKTYWNEJ PAMIĘCI FENIKSA NIEZALICZONY")
        print("=" * 90)
        print()
        print("NIEZALICZONE WARUNKI:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("WERDYKT: AKTYWNA PAMIĘĆ JEST CZĘŚCIĄ GŁÓWNEGO FENIKSA")
    print("=" * 90)
    print()
    print(
        "FENIKS potrafi zdobyć zweryfikowaną wiedzę, zapisać ją "
        "wyłącznie przez Bramę Wiedzy, a następnie samodzielnie "
        "odnaleźć ją jako bezpieczny kontekst dla kolejnego procesu "
        "poznawczego."
    )
    print(
        "Rekord podszywający się pod wiedzę pozostał fizycznie w bazie, "
        "ale nie został uznany przez aktywną pamięć za wiedzę."
    )


if __name__ == "__main__":
    main()
