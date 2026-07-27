from core.feniks import Feniks
from core.cognitive_executor import CognitiveExecutionState
from core.cognitive_orchestrator import CognitiveRoute
from core.reasoning_engine import ReasoningProblem

def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition: raise AssertionError(label)

def main():
    print("="*90); print("TEST INTEGRACJI COGNITIVE EXECUTOR Z FENIKSEM"); print("="*90)
    f=Feniks()
    check("Feniks posiada CognitiveExecutor", hasattr(f,"cognitive_executor"))
    check("Executor używa orkiestratora Feniksa",
        f.cognitive_executor.orchestrator is f.cognitive_orchestrator)
    p=ReasoningProblem(title="Brak danych", description="Nie mamy obserwacji.",
        unknowns=["Brakuje pomiaru."])
    result=f.cognitive_executor.execute(p)
    check("Wybrano INVESTIGATE", result.decision.route is CognitiveRoute.INVESTIGATE)
    check("Stan żąda dalszego badania",
        result.state is CognitiveExecutionState.NEEDS_INVESTIGATION)
    check("Nie powstał wynik rozumowania", result.reasoning_result is None)
    s=f.status()
    check("Status widzi wykonawcę", s["wykonawca_poznawczy_zaladowany"] is True)
    check("Status widzi jedno wykonanie", s["wykonania_poznawcze"]==1)
    print("="*90); print("WERDYKT: COGNITIVE EXECUTOR JEST CZĘŚCIĄ GŁÓWNEGO FENIKSA"); print("="*90)

if __name__=="__main__": main()
