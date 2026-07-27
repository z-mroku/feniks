from types import SimpleNamespace

from core.cognitive_executor import (
    CognitiveExecutionResult,
    CognitiveExecutionState,
)
from core.cognitive_orchestrator import (
    CognitiveRoute,
    CognitiveRouteDecision,
)
from core.reasoning_engine import ReasoningResult
from core.response_engine import ResponseEngine


def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition:
        raise AssertionError(label)


def decision(route):
    return CognitiveRouteDecision(
        route=route,
        reason="kontrolowany test",
        structural_analysis=ReasoningResult(),
    )


def main():
    print("=" * 90)
    print("TEST LUDZKIEJ WARSTWY ODPOWIEDZI FENIKSA")
    print("=" * 90)

    engine = ResponseEngine()

    insufficient = engine.respond(
        CognitiveExecutionResult(
            decision(CognitiveRoute.INSUFFICIENT),
            CognitiveExecutionState.INSUFFICIENT,
        )
    )
    check(
        "INSUFFICIENT mówi po ludzku o braku danych",
        "wystarczających danych" in insufficient.text,
    )

    investigate = engine.respond(
        CognitiveExecutionResult(
            decision(CognitiveRoute.INVESTIGATE),
            CognitiveExecutionState.NEEDS_INVESTIGATION,
        )
    )
    check(
        "INVESTIGATE mówi o potrzebie sprawdzenia danych",
        "Brakuje danych" in investigate.text,
    )

    reasoning = SimpleNamespace(
        problem_understood_as="Badamy zachowanie obecnego systemu.",
        known_facts=["Sprzeciw nie przewyższył poparcia"],
        unknowns=["Nie znamy przyczyny nasycenia"],
        cannot_conclude_yet=[],
        hypothesis="Nasycenie może zależeć od obecnego mechanizmu agregacji",
        experiment="Porównać zachowanie dla kontrolowanych danych wejściowych.",
    )

    reason = engine.respond(
        CognitiveExecutionResult(
            decision(CognitiveRoute.REASON),
            CognitiveExecutionState.COMPLETED,
            reasoning_result=reasoning,
        )
    )
    check(
        "REASON zachowuje fakt z analizy",
        "Sprzeciw nie przewyższył poparcia" in reason.text,
    )
    check(
        "REASON zachowuje niewiadomą",
        "Nie znamy przyczyny nasycenia" in reason.text,
    )
    check(
        "Hipoteza pozostaje oznaczona jako hipoteza",
        "Hipoteza do sprawdzenia:" in reason.text,
    )
    check(
        "Odpowiedź nie wystawia technicznego enumu",
        "CognitiveExecutionState" not in reason.text,
    )

    direct = engine.respond(
        CognitiveExecutionResult(
            decision(CognitiveRoute.DIRECT),
            CognitiveExecutionState.COMPLETED,
        )
    )
    check(
        "DIRECT nie wymyśla odpowiedzi",
        "Nie będę dopowiadał" in direct.text,
    )

    check(
        "Silnik policzył cztery odpowiedzi",
        engine.stats()["liczba_odpowiedzi"] == 4,
    )

    print("=" * 90)
    print("WERDYKT: FENIKS POTRAFI PRZEŁOŻYĆ STAN POZNAWCZY NA BEZPIECZNĄ POLSZCZYZNĘ")
    print("=" * 90)


if __name__ == "__main__":
    main()
