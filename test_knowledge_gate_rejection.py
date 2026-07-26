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


TEST_DATABASE = Path("data") / "feniks_knowledge_gate_test.db"


class ControlledWrongInterpreter:
    """
    Celowo błędny interpreter testowy.
    """

    def interpret(
        self,
        hypothesis,
        result,
    ):
        return ExperimentInterpretation(
            hypothesis_status=HypothesisStatus.REJECTED,

            reasoning=(
                "Hipoteza została obalona, ponieważ "
                "sprzeciw nie przewyższył poparcia."
            ),

            new_findings=[
                "Sprzeczność pojawiła się już przy N=1.",
                "Siła sprzeciwu wykazuje saturację od N=3.",
            ],

            remaining_unknowns=[
                (
                    "Nie wiadomo, jaki minimalny próg "
                    "sprzeciwu jest wymagany do wykrycia "
                    "SPRZECZNOŚCI."
                ),
                (
                    "Nie wiadomo, dlaczego wskaźnik "
                    "pewności zachowuje się w ten sposób."
                ),
            ],

            alternative_explanations=[
                (
                    "Klasyfikacja SPRZECZNOŚĆ może być "
                    "wyzwalana przez próg siły sprzeciwu."
                ),
                (
                    "Mechanizm agregacji może posiadać "
                    "dodatkową niewidoczną regułę."
                ),
            ],

            next_experiment_question=(
                "Jak zachowuje się TruthEngine "
                "w kolejnych warunkach?"
            ),

            next_experiment=(
                "Przeprowadzić kolejny kontrolowany "
                "eksperyment diagnostyczny."
            ),

            cannot_conclude_yet=[
                (
                    "Nie należy wyprowadzać wniosków "
                    "poza zakres wykonanych testów."
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

    Nigdy nie dotyka data/feniks.db.
    """

    gc.collect()

    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()


def main():
    failures = []

    print("=" * 86)
    print("TEST ODRZUCENIA PRZEZ BRAMĘ WIEDZY")
    print("=" * 86)

    # Gwarantujemy czysty początek testu.
    remove_test_database()

    try:
        memory = PersistentMemory(
            database_path=str(TEST_DATABASE)
        )

        gate = KnowledgeGate(
            persistent_memory=memory
        )

        cycle = CognitiveCycle(
            interpreter=ControlledWrongInterpreter()
        )

        print()
        print("ETAP 1 - BŁĘDNY CYKL POZNAWCZY")
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
            "Cykl został odrzucony",
            (
                cycle_result.decision
                == CognitiveCycleDecision.REJECTED
            ),
            failures,
        )

        check(
            "Walidator nie dopuścił interpretacji",
            (
                cycle_result.validation_report
                .safe_for_memory
                is False
            ),
            failures,
        )

        print()
        print("ETAP 2 - PRÓBA WYMUSZENIA ZAPISU")
        print("-" * 86)

        count_before = memory.count()

        admission = gate.admit(
            cycle_result=cycle_result,
            title="Test niedopuszczonej wiedzy",
        )

        count_after = memory.count()

        print(
            "Decyzja Bramy:",
            admission.decision.value,
        )

        print(
            "Powód:",
            admission.reason,
        )

        print(
            "Liczba rekordów przed:",
            count_before,
        )

        print(
            "Liczba rekordów po:",
            count_after,
        )

        print()
        print("ETAP 3 - KONTROLA BEZPIECZEŃSTWA")
        print("-" * 86)

        check(
            "Brama zwróciła ODRZUCONO",
            (
                admission.decision
                == KnowledgeGateDecision.REJECTED
            ),
            failures,
        )

        check(
            "Brama nie oznaczyła wyniku jako przyjęty",
            admission.admitted is False,
            failures,
        )

        check(
            "Nie powstał identyfikator pamięci",
            admission.memory_id is None,
            failures,
        )

        check(
            "Cykl nadal nie jest dopuszczony do pamięci",
            cycle_result.admitted_to_memory is False,
            failures,
        )

        check(
            "Baza była pusta przed próbą",
            count_before == 0,
            failures,
        )

        check(
            "Baza pozostała pusta po próbie",
            count_after == 0,
            failures,
        )

        knowledge_records = memory.find_by_category(
            KnowledgeGate.KNOWLEDGE_CATEGORY
        )

        check(
            "Nie istnieją rekordy zweryfikowanej wiedzy",
            len(knowledge_records) == 0,
            failures,
        )

        # Zwalniamy referencje przed sprzątaniem pliku.
        del knowledge_records
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
        "WERDYKT: BRAMA WIEDZY ZABLOKOWAŁA "
        "NIEDOPUSZCZONĄ INTERPRETACJĘ"
    )
    print("=" * 86)

    print()
    print(
        "Odrzucony wynik cyklu nie został zapisany "
        "nawet po bezpośrednim wywołaniu Bramy Wiedzy."
    )

    print(
        "Rzeczywista trwała pamięć FENIKSA "
        "nie została zmodyfikowana."
    )


if __name__ == "__main__":
    main()