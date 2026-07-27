from core.cognitive_executor import CognitiveExecutor, CognitiveExecutionState
from core.cognitive_orchestrator import CognitiveOrchestrator, CognitiveRoute
from core.reasoning_engine import ReasoningEngine, ReasoningProblem

class ControlledReasoner:
    def __init__(self): self.calls = []
    def __call__(self, problem, mode, knowledge_limit):
        self.calls.append((problem, mode, knowledge_limit))
        return {"analysis": "kontrolowany wynik"}

def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition: raise AssertionError(label)

def p(evidence=None, unknowns=None):
    return ReasoningProblem(title="Problem testowy", description="Opis.",
        evidence=evidence or [], unknowns=unknowns or [])

def main():
    print("="*90); print("TEST WYKONAWCZEGO ORKIESTRATORA FENIKSA"); print("="*90)
    r=ControlledReasoner()
    e=CognitiveExecutor(CognitiveOrchestrator(ReasoningEngine()), r)
    a=e.execute(p())
    check("INSUFFICIENT nie uruchamia rozumowania", len(r.calls)==0)
    check("INSUFFICIENT zachowuje stan", a.state is CognitiveExecutionState.INSUFFICIENT)
    b=e.execute(p(unknowns=["brak pomiaru"]))
    check("INVESTIGATE nie uruchamia rozumowania", len(r.calls)==0)
    check("INVESTIGATE żąda danych", b.state is CognitiveExecutionState.NEEDS_INVESTIGATION)
    c=e.execute(p(evidence=["fakt"]))
    check("DIRECT nie uruchamia rozumowania", len(r.calls)==0)
    check("DIRECT zachowuje drogę", c.decision.route is CognitiveRoute.DIRECT)
    d=e.execute(p(["fakt"], ["nieznana przyczyna"]), knowledge_limit=3)
    check("REASON uruchamia dokładnie jedno rozumowanie", len(r.calls)==1)
    check("REASON zachowuje wynik analizy", d.reasoning_result=={"analysis":"kontrolowany wynik"})
    check("Przekazano knowledge_limit", r.calls[0][2]==3)
    check("Wykonano cztery ścieżki", e.execution_count==4)
    print("="*90); print("WERDYKT: EXECUTOR WYKONUJE REASON, ALE NIE ZASTĘPUJE BRAKU DOWODÓW"); print("="*90)

if __name__=="__main__": main()
