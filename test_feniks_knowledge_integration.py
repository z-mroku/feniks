import gc
from pathlib import Path

from core.cognitive_cycle import (
    CognitiveCycleDecision,
)
from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)
from core.feniks import Feniks
from core.knowledge_gate import (
    KnowledgeGate,
    KnowledgeGateDecision,
)
from core.persistent_memory import PersistentMemory


TEST_DATABASE = (
    Path("data")
    / "feniks_full_knowledge_integration_test.db"
)


class ControlledCorrectInterpreter:
    """
    Deterministyczny interpreter testowy.

    Nie korzysta z Gemini ani z sieci.
    Zwraca interpretację zgodną z rzeczywistymi
    obserwacjami ExperimentRunner i samowiedzą FENIKSA.
    """

    def interpret(
        self,
        hypothesis,
        result,
    ):
        return ExperimentInterpretation(
            hypothesis_status=HypothesisStatus.REJECTED,
            reasoning=(
                "W przebadanym zakresie liczba "
                "przeciętnych dowodów przeciwnych "
                "nie doprowadziła do przewagi "
                "sprzeciwu nad poparciem."
            ),
            new_findings=[
                "Sprzeczność pojawiła się już przy N=1.",
                "Siła sprzeciwu wykazuje saturację od N=3.",
            ],
            remaining_unknowns=[],
            alternative_explanations=[],
            next_experiment_question=(
                "Czy wynik pozostanie taki sam "
                "dla innych poziomów wiarygodności?"
            ),
            next_experiment=(
                "Powtórzyć eksperyment dla innych "
                "kontrolowanych wartości wiarygodności."
            ),
            cannot_conclude_yet=[
                (
                    "Nie należy uogólniać wyniku "
                    "poza zakres przebadanych parametrów."
                ),
            ],
            confidence=0.95,
        )


def check(
    name: str,
    condition: bool,
    failures: list[str],
):
    status = "TAK" if condition else "NIE"
    print(f"{name}: {status}")

    if not condition:
        failures.append(name)


def remove_test_database():
    gc.collect()

    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()


def main():
    failures = []

    print("=" * 90)
    print("TEST PEŁNEJ INTEGRACJI WIEDZY W GŁÓWNYM RDZENIU FENIKSA")
    print("=" * 90)

    remove_test_database()

    feniks = None
    test_memory = None

    try:
        print()
        print("ETAP 1 - URUCHOMIENIE GŁÓWNEGO RDZENIA")
        print("-" * 90)

        feniks = Feniks()

        check(
            "Feniks został utworzony",
            feniks is not None,
            failures,
        )

        check(
            "Produkcyjny interpreter jest dostępny",
            hasattr(feniks, "experiment_interpreter"),
            failures,
        )

        check(
            "CognitiveCycle jest częścią Feniksa",
            hasattr(feniks, "cognitive_cycle"),
            failures,
        )

        check(
            "KnowledgeGate jest częścią Feniksa",
            hasattr(feniks, "knowledge_gate"),
            failures,
        )

        print()
        print("ETAP 2 - WSPÓŁDZIELENIE INSTANCJI RDZENIA")
        print("-" * 90)

        check(
            "Cykl używa interpretera Feniksa",
            (
                feniks.cognitive_cycle.interpreter
                is feniks.experiment_interpreter
            ),
            failures,
        )

        check(
            "Cykl używa SystemKnowledge Feniksa",
            (
                feniks.cognitive_cycle.system_knowledge
                is feniks.system_knowledge
            ),
            failures,
        )

        check(
            "Cykl używa ExperimentRunner Feniksa",
            (
                feniks.cognitive_cycle.experiment_runner
                is feniks.experiment_runner
            ),
            failures,
        )

        check(
            "Cykl używa ReasoningValidator Feniksa",
            (
                feniks.cognitive_cycle.reasoning_validator
                is feniks.reasoning_validator
            ),
            failures,
        )

        check(
            "Brama używa PersistentMemory Feniksa",
            (
                feniks.knowledge_gate.persistent_memory
                is feniks.persistent_memory
            ),
            failures,
        )

        print()
        print("ETAP 3 - STATUS SAMOOBSERWACJI")
        print("-" * 90)

        status = feniks.status()

        check(
            "Status widzi interpreter eksperymentów",
            (
                status.get(
                    "interpreter_eksperymentow_zaladowany"
                )
                is True
            ),
            failures,
        )

        check(
            "Status widzi cykl poznawczy",
            (
                status.get(
                    "cykl_poznawczy_zaladowany"
                )
                is True
            ),
            failures,
        )

        check(
            "Status widzi Bramę Wiedzy",
            (
                status.get(
                    "brama_wiedzy_zaladowana"
                )
                is True
            ),
            failures,
        )

        print()
        print("ETAP 4 - ODDZIELENIE POZNANIA OD ZAPISU")
        print("-" * 90)

        # Test ma być deterministyczny i nie może zależeć
        # od Gemini. Podmieniamy wyłącznie interpreter
        # wewnątrz już zintegrowanego CognitiveCycle.
        original_interpreter = feniks.cognitive_cycle.interpreter
        feniks.cognitive_cycle.interpreter = (
            ControlledCorrectInterpreter()
        )

        # Brama produkcyjna została już sprawdzona powyżej
        # pod kątem współdzielenia pamięci głównego Feniksa.
        # Dalszy zapis kierujemy wyłącznie do izolowanej
        # testowej bazy SQLite.
        test_memory = PersistentMemory(
            database_path=str(TEST_DATABASE)
        )
        feniks.knowledge_gate = KnowledgeGate(
            persistent_memory=test_memory
        )

        count_before_cycle = test_memory.count()

        cycle_result = feniks.run_cognitive_cycle(
            hypothesis=(
                "Rosnąca liczba przeciętnych dowodów "
                "przeciwnych ostatecznie przewyższy "
                "jeden mocny dowód wspierający."
            ),
            strong_support_reliability=0.95,
            opposing_reliability=0.50,
            max_opposing=4,
        )

        count_after_cycle = test_memory.count()

        check(
            "Cykl zakończył się KANDYDATEM DO WIEDZY",
            (
                cycle_result.decision
                == CognitiveCycleDecision
                .CANDIDATE_FOR_KNOWLEDGE
            ),
            failures,
        )

        check(
            "Walidator uznał interpretację za bezpieczną",
            (
                cycle_result.validation_report
                .safe_for_memory
                is True
            ),
            failures,
        )

        check(
            "Cykl sam nie zapisał wiedzy",
            cycle_result.admitted_to_memory is False,
            failures,
        )

        check(
            "Baza testowa była pusta przed cyklem",
            count_before_cycle == 0,
            failures,
        )

        check(
            "Po samym cyklu baza nadal jest pusta",
            count_after_cycle == 0,
            failures,
        )

        check(
            "Cykl został zachowany w historii",
            len(feniks.cognitive_cycle.history()) == 1,
            failures,
        )

        check(
            "Ostatni wynik wskazuje wykonany cykl",
            feniks.cognitive_cycle.last_result() is cycle_result,
            failures,
        )

        print()
        print("ETAP 5 - JAWNE PRZEJŚCIE PRZEZ BRAMĘ WIEDZY")
        print("-" * 90)

        admission = feniks.admit_knowledge(
            cycle_result=cycle_result,
            title=(
                "Wpływ liczby przeciętnych dowodów "
                "na wynik TruthEngine"
            ),
        )

        count_after_gate = test_memory.count()

        check(
            "Brama dopuściła zweryfikowaną wiedzę",
            (
                admission.decision
                == KnowledgeGateDecision.ADMITTED
            ),
            failures,
        )

        check(
            "Wynik Bramy jest oznaczony jako przyjęty",
            admission.admitted is True,
            failures,
        )

        check(
            "Powstał identyfikator trwałego rekordu",
            admission.memory_id is not None,
            failures,
        )

        check(
            "Cykl został oznaczony jako zapisany",
            cycle_result.admitted_to_memory is True,
            failures,
        )

        check(
            "Dopiero Brama utworzyła jeden rekord",
            count_after_gate == 1,
            failures,
        )

        print()
        print("ETAP 6 - PONOWNY ODCZYT Z SQLITE")
        print("-" * 90)

        stored = test_memory.get(
            admission.memory_id
        )

        check(
            "Zapisany rekord można ponownie odczytać",
            stored is not None,
            failures,
        )

        if stored is not None:
            metadata = stored.get("metadane", {})
            content = stored.get("tresc", "")

            print(
                "Kategoria:",
                stored.get("kategoria"),
            )
            print(
                "Tytuł:",
                stored.get("tytul"),
            )
            print(
                "Źródło:",
                stored.get("zrodlo"),
            )
            print(
                "Status wiedzy:",
                metadata.get("knowledge_status"),
            )
            print(
                "Pochodzenie:",
                metadata.get("provenance"),
            )

            check(
                "Rekord ma kategorię zweryfikowanej wiedzy",
                (
                    stored.get("kategoria")
                    == KnowledgeGate.KNOWLEDGE_CATEGORY
                ),
                failures,
            )

            check(
                "Źródłem rekordu jest Brama Wiedzy",
                (
                    stored.get("zrodlo")
                    == "FENIKS_KNOWLEDGE_GATE"
                ),
                failures,
            )

            check(
                "Metadane zachowały status ADMITTED",
                (
                    metadata.get("knowledge_status")
                    == "ADMITTED"
                ),
                failures,
            )

            check(
                "Metadane zachowały decyzję cyklu",
                (
                    metadata.get("cycle_decision")
                    == "KANDYDAT_DO_WIEDZY"
                ),
                failures,
            )

            check(
                "Metadane zachowały wynik walidacji",
                (
                    metadata.get(
                        "validation_safe_for_memory"
                    )
                    is True
                ),
                failures,
            )

            check(
                "Zachowano pełne pochodzenie wiedzy",
                (
                    metadata.get("provenance")
                    == [
                        "ExperimentRunner",
                        "ExperimentInterpreter",
                        "ReasoningValidator",
                        "KnowledgeGate",
                    ]
                ),
                failures,
            )

            check(
                "Treść zachowała hipotezę",
                "HIPOTEZA:" in content,
                failures,
            )

            check(
                "Treść zachowała zweryfikowane ustalenia",
                "ZWERYFIKOWANE USTALENIA:" in content,
                failures,
            )

            check(
                "Treść zachowała dane eksperymentalne",
                "DANE EKSPERYMENTALNE:" in content,
                failures,
            )

            check(
                "Treść zachowała granice wnioskowania",
                "GRANICE WNIOSKOWANIA:" in content,
                failures,
            )

        print()
        print("ETAP 7 - KONTROLA GRANICY BEZPIECZEŃSTWA")
        print("-" * 90)

        check(
            "Poznanie i zapis są osobnymi operacjami",
            (
                count_after_cycle == 0
                and count_after_gate == 1
            ),
            failures,
        )

        check(
            "Gemini nie był potrzebny do deterministycznego testu",
            (
                feniks.cognitive_cycle.interpreter
                is not original_interpreter
            ),
            failures,
        )

        check(
            "Test korzystał wyłącznie z izolowanej bazy",
            (
                feniks.knowledge_gate.persistent_memory
                is test_memory
            ),
            failures,
        )

        # Zwolnienie obiektów związanych z testową bazą.
        stored = None
        admission = None
        cycle_result = None

        feniks.knowledge_gate = None
        test_memory = None

        gc.collect()

    finally:
        test_memory = None
        feniks = None
        gc.collect()
        remove_test_database()

    print()
    print("=" * 90)

    if failures:
        print("WERDYKT: TEST PEŁNEJ INTEGRACJI NIEZALICZONY")
        print("=" * 90)
        print()
        print("NIEZALICZONE WARUNKI:")

        for failure in failures:
            print(f"- {failure}")

        raise SystemExit(1)

    print(
        "WERDYKT: PEŁNY ŁAŃCUCH WIEDZY "
        "GŁÓWNEGO FENIKSA DZIAŁA"
    )
    print("=" * 90)

    print()
    print(
        "Główny Feniks posiada zintegrowany "
        "CognitiveCycle i KnowledgeGate."
    )
    print(
        "Sam cykl poznawczy nie zapisuje wiedzy."
    )
    print(
        "Dopiero jawne przejście przez Bramę Wiedzy "
        "utworzyło trwały rekord w izolowanej bazie testowej."
    )
    print(
        "Ponowny odczyt potwierdził walidację, "
        "pochodzenie i granice zapisanej wiedzy."
    )


if __name__ == "__main__":
    main()
