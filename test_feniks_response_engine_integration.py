from core.feniks import Feniks
from core.reasoning_engine import ReasoningProblem

def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition:
        raise AssertionError(label)

def main():
    print("=" * 90)
    print("TEST INTEGRACJI LUDZKIEJ ODPOWIEDZI Z GLOWNYM FENIKSEM")
    print("=" * 90)
    feniks = Feniks()
    check("Feniks posiada ResponseEngine", hasattr(feniks, "response_engine"))
    check("Feniks udostepnia respond_to_problem", hasattr(feniks, "respond_to_problem"))

    problem = ReasoningProblem(
        title="Nieznana przyczyna",
        description="Nie mamy jeszcze obserwacji pozwalajacych ustalic przyczyne.",
        unknowns=["Brakuje pomiaru."],
    )
    response = feniks.respond_to_problem(problem)

    check("Powstala odpowiedz tekstowa", isinstance(response.text, str) and bool(response.text.strip()))
    check("Odpowiedz nie wystawia technicznego enumu", "CognitiveExecutionState" not in response.text)
    check("Odpowiedz uczciwie komunikuje brak danych",
          ("Brakuje danych" in response.text) or ("nie da sie uczciwie rozstrzygnac" in response.text))

    status = feniks.status()
    check("Status widzi warstwe odpowiedzi", status["warstwa_odpowiedzi_zaladowana"] is True)
    check("Status widzi jedna odpowiedz", status["odpowiedzi_dla_czlowieka"] == 1)
    check("Status widzi jedno wykonanie poznawcze", status["wykonania_poznawcze"] == 1)

    print("=" * 90)
    print("WERDYKT: LUDZKA WARSTWA ODPOWIEDZI JEST CZESCIA GLOWNEGO FENIKSA")
    print("=" * 90)

if __name__ == "__main__":
    main()
