from core.cognitive_orchestrator import CognitiveOrchestrator, CognitiveRoute
from core.reasoning_engine import ReasoningEngine, ReasoningProblem

def check(label, condition):
    print(f"{label}: {'TAK' if condition else 'NIE'}")
    if not condition:
        raise AssertionError(label)

def p(evidence=None, unknowns=None):
    return ReasoningProblem(
        title="Problem testowy",
        description="Kontrolowany problem testowy.",
        evidence=evidence or [],
        unknowns=unknowns or [],
    )

def main():
    print("=" * 90)
    print("TEST ORKIESTRATORA POZNAWCZEGO FENIKSA")
    print("=" * 90)
    engine = ReasoningEngine()
    o = CognitiveOrchestrator(engine)

    check("Brak danych -> INSUFFICIENT", o.decide(p()).route is CognitiveRoute.INSUFFICIENT)
    check("Niewiadome bez dowodów -> INVESTIGATE", o.decide(p(unknowns=["x"])).route is CognitiveRoute.INVESTIGATE)
    check("Dowody i niewiadome -> REASON", o.decide(p(["fakt"], ["x"])).route is CognitiveRoute.REASON)
    last = o.decide(p(["fakt"]))
    check("Dowody bez niewiadomych -> DIRECT", last.route is CognitiveRoute.DIRECT)
    check("Cztery decyzje", o.stats()["liczba_decyzji"] == 4)
    check("Cztery analizy strukturalne", engine.stats()["liczba_analiz"] == 4)
    check("Decyzja zachowuje analizę", last.structural_analysis.known_facts == ["fakt"])

    print("=" * 90)
    print("WERDYKT: ORKIESTRATOR WYBIERA DROGĘ POZNAWCZĄ BEZ UDAWANIA PRAWDY")
    print("=" * 90)

if __name__ == "__main__":
    main()
