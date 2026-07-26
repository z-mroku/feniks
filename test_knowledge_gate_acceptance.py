import gc
from pathlib import Path

from core.cognitive_cycle import (
    CognitiveCycle,
    CognitiveCycleDecision,
)
from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)
from core.knowledge_gate import (
    KnowledgeGate,
    KnowledgeGateDecision,
)
from core.persistent_memory import PersistentMemory


TEST_DATABASE = (
    Path("data")
    / "feniks_knowledge_gate_acceptance_test.db"
)


class ControlledCorrectInterpreter:
    """
    Kontrolowany poprawny interpreter testowy.

    Zwraca interpretację zgodną z obserwacjami
    eksperymentu i samowiedzą FENIKSA.
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
                (
                    "Sprzeczność pojawiła się już "
                    "przy N=1."
                ),
                (
                    "Siła sprzeciwu wykazuje "
                    "saturację od N=3."
                ),
            ],

            remaining_unknowns=[],

            alternative_explanations=[],

            next_experiment_question=(
                "Czy wynik pozostanie taki sam "
                "dla innych poziomów wiarygodności?"
            ),

            next_experiment=(
                "Powtórzyć eksperyment dla innych "
                "kontrolowanych wartości "
                "wiarygodności."
            ),

            cannot_conclude_yet=[
                (
                    "Nie należy uogólniać wyniku "
                    "poza zakres przebadanych "
                    "parametrów."
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
    """
    Usuwa wyłącznie bazę należącą do tego testu.

    Nigdy nie dotyka rzeczywistej bazy FENIKSA.
    """

    gc.collect()

    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()


def main():
    failures = []

    print("=" * 86)
    print("TEST PRZYJĘCIA PRZEZ BRAMĘ WIEDZY")
    print("=" * 86)

    remove_test_database()

    try:
        memory = PersistentMemory(
            database_path=str(TEST_DATABASE)
        )

        gate = KnowledgeGate(
            persistent_memory=memory
        )

        cycle = CognitiveCycle(
            interpreter=ControlledCorrectInterpreter()
        )

        print()
        print("ETAP 1 - POPRAWNY CYKL POZNAWCZY")
        print("-" * 86)

        cycle_result = cycle.run_quantity_vs_quality(
            hypothesis=(
                "Rosnąca liczba przeciętnych dowodów "
                "przeciwnych ostatecznie przewyższy "
                "jeden mocny dowód wspierający."
            ),
            strong_support_reliability=0.95,
            opposing_reliability=0.50,
            max_opposing=4,
        )

        check(
            "Cykl utworzył KANDYDATA DO WIEDZY",
            (
                cycle_result.decision
                == CognitiveCycleDecision
                .CANDIDATE_FOR_KNOWLEDGE
            ),
            failures,
        )

        check(
            "Walidator dopuścił interpretację",
            (
                cycle_result.validation_report
                .safe_for_memory
                is True
            ),
            failures,
        )

        check(
            "Przed Bramą nic nie zapisano",
            cycle_result.admitted_to_memory is False,
            failures,
        )

        print()
        print("ETAP 2 - BRAMA WIEDZY")
        print("-" * 86)

        count_before = memory.count()

        admission = gate.admit(
            cycle_result=cycle_result,
            title=(
                "Wpływ liczby przeciętnych dowodów "
                "na wynik TruthEngine"
            ),
        )

        count_after = memory.count()

        print(
            "Decyzja Bramy:",
            admission.decision.value,
        )

        print(
            "ID rekordu:",
            admission.memory_id,
        )

        print(
            "Liczba rekordów przed:",
            count_before,
        )

        print(
            "Liczba rekordów po:",
            count_after,
        )

        check(
            "Brama dopuściła wiedzę",
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
            "Powstał identyfikator trwałej pamięci",
            admission.memory_id is not None,
            failures,
        )

        check(
            "Cykl został oznaczony jako zapisany",
            cycle_result.admitted_to_memory is True,
            failures,
        )

        check(
            "Baza była pusta przed zapisem",
            count_before == 0,
            failures,
        )

        check(
            "W bazie istnieje dokładnie jeden rekord",
            count_after == 1,
            failures,
        )

        print()
        print("ETAP 3 - PONOWNY ODCZYT Z SQLITE")
        print("-" * 86)

        stored = memory.get(
            admission.memory_id
        )

        check(
            "Rekord można ponownie odczytać",
            stored is not None,
            failures,
        )

        if stored is not None:
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

            metadata = stored.get(
                "metadane",
                {},
            )

            print(
                "Status wiedzy:",
                metadata.get(
                    "knowledge_status"
                ),
            )

            print(
                "Pochodzenie:",
                metadata.get(
                    "provenance"
                ),
            )

            check(
                "Kategoria oznacza zweryfikowaną wiedzę",
                (
                    stored.get("kategoria")
                    == KnowledgeGate.KNOWLEDGE_CATEGORY
                ),
                failures,
            )

            check(
                "Źródłem jest Brama Wiedzy",
                (
                    stored.get("zrodlo")
                    == "FENIKS_KNOWLEDGE_GATE"
                ),
                failures,
            )

            check(
                "Metadane zachowały status ADMITTED",
                (
                    metadata.get(
                        "knowledge_status"
                    )
                    == "ADMITTED"
                ),
                failures,
            )

            check(
                "Metadane zachowały decyzję cyklu",
                (
                    metadata.get(
                        "cycle_decision"
                    )
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
                "Brak fałszywych niewiadomych",
                (
                    metadata.get(
                        "false_unknowns"
                    )
                    == 0
                ),
                failures,
            )

            check(
                "Brak sprzeczności z wiedzą",
                (
                    metadata.get(
                        "conflicts"
                    )
                    == 0
                ),
                failures,
            )

            check(
                "Brak twierdzeń nieweryfikowalnych",
                (
                    metadata.get(
                        "unverifiable"
                    )
                    == 0
                ),
                failures,
            )

            expected_provenance = [
                "ExperimentRunner",
                "ExperimentInterpreter",
                "ReasoningValidator",
                "KnowledgeGate",
            ]

            check(
                "Zachowano pełne pochodzenie wiedzy",
                (
                    metadata.get(
                        "provenance"
                    )
                    == expected_provenance
                ),
                failures,
            )

            content = stored.get(
                "tresc",
                "",
            )

            check(
                "Treść zachowała hipotezę",
                "HIPOTEZA:" in content,
                failures,
            )

            check(
                "Treść zachowała ustalenia",
                (
                    "ZWERYFIKOWANE USTALENIA:"
                    in content
                ),
                failures,
            )

            check(
                "Treść zachowała dane eksperymentalne",
                (
                    "DANE EKSPERYMENTALNE:"
                    in content
                ),
                failures,
            )

            check(
                "Treść zachowała granice wnioskowania",
                (
                    "GRANICE WNIOSKOWANIA:"
                    in content
                ),
                failures,
            )

        print()
        print("ETAP 4 - KONTROLA KATEGORII")
        print("-" * 86)

        knowledge_records = memory.find_by_category(
            KnowledgeGate.KNOWLEDGE_CATEGORY
        )

        check(
            "Istnieje dokładnie jeden rekord wiedzy",
            len(knowledge_records) == 1,
            failures,
        )

        if knowledge_records:
            check(
                "ID rekordu kategorii zgadza się z Bramą",
                (
                    knowledge_records[0].get("id")
                    == admission.memory_id
                ),
                failures,
            )

        del knowledge_records
        del stored
        del admission
        del gate
        del memory

        gc.collect()

    finally:
        remove_test_database()

    print()
    print("=" * 86)

    if failures:
        print("WERDYKT: TEST NIEZALICZONY")
        print("=" * 86)

        print()
        print("NIEZALICZONE WARUNKI:")

        for failure in failures:
            print(f"- {failure}")

        raise SystemExit(1)

    print(
        "WERDYKT: BRAMA WIEDZY POPRAWNIE "
        "ZAPISAŁA ZWERYFIKOWANĄ WIEDZĘ"
    )
    print("=" * 86)

    print()
    print(
        "Kandydat przeszedł walidację, "
        "został dopuszczony przez Bramę Wiedzy "
        "i zapisany do testowej bazy SQLite."
    )

    print(
        "Ponowny odczyt potwierdził zachowanie "
        "statusu, walidacji i pochodzenia wiedzy."
    )

    print(
        "Rzeczywista pamięć FENIKSA "
        "nie została użyta."
    )


if __name__ == "__main__":
    main()