from core.feniks import Feniks
from core.reasoning_engine import ReasoningProblem
from core.reasoning_provider import ReasoningMode

def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition:
        raise AssertionError(label)

def main():
    print("=" * 90)
    print("TEST INTEGRACJI ROZUMOWANIA Z PAMIĘCIĄ SEMANTYCZNĄ FENIKSA")
    print("=" * 90)

    feniks = Feniks()

    check("Feniks posiada ReasoningEngine", hasattr(feniks, "reasoning_engine"))
    check("Feniks posiada GeminiReasoningProvider", hasattr(feniks, "reasoning_provider"))
    check("Feniks udostępnia reason_about_problem", hasattr(feniks, "reason_about_problem"))

    problem = ReasoningProblem(
        title="Czy sama wcześniejsza wiedza rozstrzyga nowy problem?",
        description="Sprawdź rozdział między bieżącymi dowodami a wcześniejszą pamięcią.",
        evidence=["Nie wykonano jeszcze eksperymentu rozstrzygającego."],
        unknowns=["Nie wiadomo jeszcze, jaki będzie wynik nowego eksperymentu."],
        history=["Historia użytkownika jest kontekstem, a nie dowodem."],
    )

    before = feniks.persistent_memory.count()
    result = feniks.reason_about_problem(
        problem=problem,
        mode=ReasoningMode.DIAGNOSIS,
        knowledge_limit=5,
    )
    after = feniks.persistent_memory.count()

    print("Model podstawowy:", feniks.reasoning_provider.model)
    print("Model zapasowy:", feniks.reasoning_provider.fallback_model)
    print("Model użyty:", feniks.reasoning_provider.last_model_used)
    print("Fallback:", "TAK" if feniks.reasoning_provider.last_fallback_used else "NIE")

    check("Provider zwrócił poprawną pewność", 0.0 <= result.confidence <= 1.0)
    check(
        "Brak rozstrzygających danych pozostał widoczny",
        bool(result.unknowns or result.cannot_conclude_yet),
    )
    check("Powstało kryterium rozstrzygnięcia", bool(result.conclusion_rule.strip()))
    check("Rozumowanie nie zapisało automatycznie nowej wiedzy", before == after)

    print("=" * 90)
    print("WERDYKT: MOST ROZUMOWANIA FENIKSA DZIAŁA")
    print("=" * 90)

if __name__ == "__main__":
    main()
