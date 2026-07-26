from core.cognitive_cycle import (
    CognitiveCycle,
    CognitiveCycleDecision,
)
from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)


class ControlledWrongInterpreter:
    """
    Kontrolowany interpreter testowy.

    Celowo zwraca interpretację zawierającą
    twierdzenia sprzeczne ze zweryfikowaną
    samowiedzą FENIKSA.
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


def main():
    failures = []

    print("=" * 86)
    print("TEST ODRZUCENIA BŁĘDNEGO ROZUMOWANIA")
    print("=" * 86)

    interpreter = ControlledWrongInterpreter()

    cycle = CognitiveCycle(
        interpreter=interpreter
    )

    print()
    print("URUCHAMIANIE PEŁNEGO CYKLU")
    print("-" * 86)

    result = cycle.run_quantity_vs_quality(
        hypothesis=(
            "Rosnąca liczba przeciętnych dowodów "
            "przeciwnych ostatecznie przewyższy "
            "jeden mocny dowód wspierający."
        ),
        strong_support_reliability=0.95,
        opposing_reliability=0.50,
        max_opposing=4,
    )

    print()
    print("WYNIK CYKLU")
    print("-" * 86)

    print(
        "Decyzja:",
        result.decision.value,
    )

    print(
        "Bezpieczne według walidatora:",
        result.validation_report.safe_for_memory,
    )

    print(
        "Dopuszczone do pamięci:",
        result.admitted_to_memory,
    )

    print(
        "Fałszywe niewiadome:",
        len(
            result.validation_report.false_unknowns
        ),
    )

    print(
        "Sprzeczności z wiedzą:",
        len(
            result.validation_report.conflicts
        ),
    )

    print()
    print("KONTROLA")
    print("-" * 86)

    check(
        "Eksperyment został rzeczywiście wykonany",
        len(result.experiment_result.observations) == 5,
        failures,
    )

    check(
        "Pierwsza sprzeczność wystąpiła przy N=1",
        (
            result.experiment_result
            .first_contradiction_at
            == 1
        ),
        failures,
    )

    check(
        "Interpretacja została zwalidowana",
        result.validation_report is not None,
        failures,
    )

    check(
        "Walidator wykrył fałszywe niewiadome",
        len(
            result.validation_report.false_unknowns
        ) > 0,
        failures,
    )

    check(
        "Walidator wykrył sprzeczności z wiedzą",
        len(
            result.validation_report.conflicts
        ) > 0,
        failures,
    )

    check(
        "Walidator nie uznał interpretacji za bezpieczną",
        (
            result.validation_report.safe_for_memory
            is False
        ),
        failures,
    )

    check(
        "Cykl zakończył się decyzją ODRZUCONO",
        (
            result.decision
            == CognitiveCycleDecision.REJECTED
        ),
        failures,
    )

    check(
        "Wynik nie jest kandydatem do wiedzy",
        (
            result.safe_for_knowledge_candidate
            is False
        ),
        failures,
    )

    check(
        "Nic nie zostało dopuszczone do pamięci",
        result.admitted_to_memory is False,
        failures,
    )

    check(
        "Cykl został zachowany w historii sesji",
        len(cycle.history()) == 1,
        failures,
    )

    check(
        "Ostatni wynik wskazuje ten sam cykl",
        cycle.last_result() is result,
        failures,
    )

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
        "WERDYKT: FENIKS ODRZUCIŁ "
        "BŁĘDNĄ INTERPRETACJĘ"
    )
    print("=" * 86)

    print()
    print(
        "Model mógł zaproponować rozumowanie, "
        "ale nie kontrolował końcowej decyzji."
    )

    print(
        "Błędna interpretacja nie została "
        "dopuszczona do pamięci."
    )


if __name__ == "__main__":
    main()