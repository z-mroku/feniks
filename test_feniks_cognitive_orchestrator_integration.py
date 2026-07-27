from core.feniks import Feniks
from core.cognitive_orchestrator import CognitiveRoute
from core.reasoning_engine import ReasoningProblem

def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition:
        raise AssertionError(label)

def main():
    print("=" * 90)
    print("TEST INTEGRACJI ORKIESTRATORA Z GLOWNYM FENIKSEM")
    print("=" * 90)
    f = Feniks()
    check("Feniks posiada CognitiveOrchestrator", hasattr(f, "cognitive_orchestrator"))
    check("Orkiestrator uzywa ReasoningEngine Feniksa", f.cognitive_orchestrator.reasoning_engine is f.reasoning_engine)

    problem = ReasoningProblem(
        title="Nieznana przyczyna obserwacji",
        description="Mamy obserwacje, ale nie znamy jej przyczyny.",
        evidence=["Zaobserwowano zmiane."],
        unknowns=["Nie znamy przyczyny zmiany."],
    )
    decision = f.cognitive_orchestrator.decide(problem)
    check("Wybrano droge REASON", decision.route is CognitiveRoute.REASON)

    status = f.status()
    check("Status widzi orkiestrator", status["orkiestrator_poznawczy_zaladowany"] is True)
    check("Status widzi jedna decyzje", status["decyzje_orkiestratora"] == 1)

    print("=" * 90)
    print("WERDYKT: ORKIESTRATOR JEST CZESCIA GLOWNEGO RDZENIA FENIKSA")
    print("=" * 90)

if __name__ == "__main__":
    main()
