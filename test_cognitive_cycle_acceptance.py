from core.cognitive_cycle import (
    CognitiveCycle,
    CognitiveCycleDecision,
)
from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)


class ControlledCorrectInterpreter:
    """
    Kontrolowany interpreter testowy.

    Zwraca ostrożną interpretację zgodną
    z rzeczywistym wynikiem eksperymentu
    i zweryfikowaną samowiedzą FENIKSA.
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
                "dla innych poziomów wiarygodności "
                "dowodów?"
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


def main():
    failures = []

    print("=" * 86)
    print("TEST AKCEPTACJI POPRAWNEGO ROZUMOWANIA")
    print("=" * 86)

    interpreter = ControlledCorrectInterpreter()

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

    print(
        "Nieweryfikowalne:",
        len(
            result.validation_report.unverifiable
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
        "Sprzeciw nie przewyższył poparcia",
        (
            result.experiment_result
            .first_opposition_stronger_at
            is None
        ),
        failures,
    )

    check(
        "Interpretacja została zwalidowana",
        result.validation_report is not None,
        failures,
    )

    check(
        "Nie wykryto fałszywych niewiadomych",
        len(
            result.validation_report.false_unknowns
        ) == 0,
        failures,
    )

    check(
        "Nie wykryto sprzeczności z wiedzą",
        len(
            result.validation_report.conflicts
        ) == 0,
        failures,
    )

    check(
        "Nie pozostały twierdzenia nieweryfikowalne",
        len(
            result.validation_report.unverifiable
        ) == 0,
        failures,
    )

    check(
        "Walidator uznał interpretację za bezpieczną",
        (
            result.validation_report.safe_for_memory
            is True
        ),
        failures,
    )

    check(
        "Cykl utworzył KANDYDATA DO WIEDZY",
        (
            result.decision
            == CognitiveCycleDecision
            .CANDIDATE_FOR_KNOWLEDGE
        ),
        failures,
    )

    check(
        "Wynik jest kandydatem do wiedzy",
        (
            result.safe_for_knowledge_candidate
            is True
        ),
        failures,
    )

    check(
        "Kandydat nie został automatycznie zapisany",
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
        "WERDYKT: FENIKS ROZPOZNAŁ "
        "POPRAWNĄ INTERPRETACJĘ"
    )
    print("=" * 86)

    print()
    print(
        "Interpretacja została uznana za "
        "kandydata do wiedzy."
    )

    print(
        "Nie została jednak automatycznie "
        "zapisana do trwałej pamięci."
    )


if __name__ == "__main__":
    main()