from core.feniks import Feniks
from core.cognitive_executor import CognitiveExecutionState
from core.cognitive_orchestrator import CognitiveRoute
from core.reasoning_engine import ReasoningProblem


def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition:
        raise AssertionError(label)


def memory_count(feniks):
    # Liczymy wyłącznie zweryfikowaną wiedzę dostępną przez publiczną bramę.
    return len(feniks.all_verified_knowledge().records)


def main():
    print("=" * 90)
    print("TEST PRODUKCYJNY END-TO-END: ORKIESTRATOR -> REASON -> GEMINI")
    print("=" * 90)

    feniks = Feniks()

    problem = ReasoningProblem(
        title="Wpływ liczby słabszych dowodów na jeden silny dowód",
        description=(
            "Mamy obserwacje dotyczące konkurencji jednego bardzo mocnego "
            "dowodu z wieloma słabszymi dowodami. Trzeba przeanalizować "
            "bieżące fakty i wskazać, czego nadal nie można rozstrzygnąć."
        ),
        evidence=[
            "W badanym przebiegu siła poparcia wynosiła 0.8575.",
            "Siła sprzeciwu osiągnęła 0.5750 i nie przewyższyła poparcia.",
        ],
        unknowns=[
            "Nie znamy przyczyny nasycenia siły sprzeciwu.",
        ],
    )

    before = memory_count(feniks)

    print("\nETAP 1 - DECYZJA I WYKONANIE")
    print("-" * 90)

    result = feniks.cognitive_executor.execute(
        problem=problem,
        knowledge_limit=5,
    )

    check("Orkiestrator wybrał REASON", result.decision.route is CognitiveRoute.REASON)
    check("Executor zakończył kontrolowane wykonanie", result.state is CognitiveExecutionState.COMPLETED)
    check("Powstał wynik rozumowania", result.reasoning_result is not None)

    print("\nETAP 2 - PRODUKCYJNY PROVIDER")
    print("-" * 90)

    provider = feniks.reasoning_provider
    print("Model podstawowy:", provider.model)
    print("Model zapasowy:", provider.fallback_model)
    print("Model faktycznie użyty:", provider.last_model_used)
    print("Fallback:", "TAK" if provider.last_fallback_used else "NIE")

    check("Faktycznie użyty model jest znany", provider.last_model_used is not None)

    reasoning = result.reasoning_result
    check("Pewność mieści się w zakresie 0-1", 0.0 <= reasoning.confidence <= 1.0)
    check("Powstało kryterium rozstrzygnięcia", bool(reasoning.conclusion_rule.strip()))
    check(
        "Granice wnioskowania pozostały widoczne",
        bool(reasoning.unknowns) or bool(reasoning.cannot_conclude_yet),
    )

    print("\nETAP 3 - KONTROLA PAMIĘCI")
    print("-" * 90)

    after = memory_count(feniks)
    print("Zweryfikowana wiedza przed:", before)
    print("Zweryfikowana wiedza po:", after)

    check("Samo rozumowanie nie dopisało zweryfikowanej wiedzy", before == after)

    print("\nETAP 4 - SAMOOBSERWACJA")
    print("-" * 90)

    status = feniks.status()
    check("Status widzi decyzję orkiestratora", status["decyzje_orkiestratora"] >= 1)
    check("Status widzi wykonanie poznawcze", status["wykonania_poznawcze"] >= 1)

    print("\n" + "=" * 90)
    print("WERDYKT: FENIKS SAM WYBRAŁ REASON I URUCHOMIŁ PRODUKCYJNE ROZUMOWANIE")
    print("=" * 90)
    print(
        "Wynik pozostał analizą. Nie został automatycznie uznany za prawdę "
        "ani zapisany jako zweryfikowana wiedza."
    )


if __name__ == "__main__":
    main()
