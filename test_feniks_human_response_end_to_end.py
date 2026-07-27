from core.feniks import Feniks
from core.reasoning_engine import ReasoningProblem

def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition:
        raise AssertionError(label)

def main():
    print("=" * 90)
    print("TEST PRODUKCYJNY: PROBLEM -> REASON -> GEMINI -> LUDZKA ODPOWIEDZ")
    print("=" * 90)
    feniks = Feniks()

    problem = ReasoningProblem(
        title="Zachowanie konkurujacych dowodow",
        description=(
            "Trzeba przeanalizowac obserwacje obecnego systemu i jasno "
            "oddzielic to, co wiadomo, od tego, czego nadal nie wiadomo."
        ),
        evidence=[
            "W badanym przebiegu sila poparcia wynosila 0.8575.",
            "Sila sprzeciwu osiagnela 0.5750 i nie przewyzszyla poparcia.",
        ],
        unknowns=["Nie znamy przyczyny nasycenia sily sprzeciwu."],
    )

    response = feniks.respond_to_problem(problem=problem, knowledge_limit=5)
    provider = feniks.reasoning_provider

    print("Model faktycznie uzyty:", provider.last_model_used)
    print("Fallback:", "TAK" if provider.last_fallback_used else "NIE")
    print()
    print("ODPOWIEDZ FENIKSA:")
    print("-" * 90)
    print(response.text)
    print("-" * 90)

    check("Powstala ludzka odpowiedz", isinstance(response.text, str) and bool(response.text.strip()))
    check("Produkcyjne rozumowanie zostalo uzyte", response.used_reasoning is True)
    check("Faktycznie uzyty model jest znany", provider.last_model_used is not None)
    check("Odpowiedz nie pokazuje technicznego stanu", "CognitiveExecutionState" not in response.text)
    check("Odpowiedz nie pokazuje nazwy klasy wyniku", "ReasoningResult" not in response.text)
    check("Odpowiedz zachowuje granice wiedzy",
          ("nie można" in response.text.lower()) or ("nie mozna" in response.text.lower()) or ("nie znamy" in response.text.lower()))

    print("=" * 90)
    print("WERDYKT: FENIKS PRZECHODZI OD PROBLEMU DO ODPOWIEDZI DLA CZLOWIEKA")
    print("=" * 90)

if __name__ == "__main__":
    main()
