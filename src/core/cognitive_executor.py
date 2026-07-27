from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional
from core.cognitive_orchestrator import CognitiveOrchestrator, CognitiveRoute, CognitiveRouteDecision
from core.reasoning_engine import ReasoningProblem
from core.reasoning_provider import ReasoningMode

class CognitiveExecutionState(Enum):
    COMPLETED = "COMPLETED"
    NEEDS_INVESTIGATION = "NEEDS_INVESTIGATION"
    INSUFFICIENT = "INSUFFICIENT"

@dataclass(frozen=True)
class CognitiveExecutionResult:
    decision: CognitiveRouteDecision
    state: CognitiveExecutionState
    reasoning_result: Optional[Any] = None
    message: str = ""

class CognitiveExecutor:
    """Wykonuje następny krok poznawczy bez zapisywania wiedzy."""
    def __init__(self, orchestrator: CognitiveOrchestrator, reason_callback: Callable[..., Any]):
        self.orchestrator = orchestrator
        self.reason_callback = reason_callback
        self.execution_count = 0

    def execute(self, problem: ReasoningProblem, mode: ReasoningMode = ReasoningMode.DIAGNOSIS,
                knowledge_limit: int | None = 5) -> CognitiveExecutionResult:
        decision = self.orchestrator.decide(problem)
        self.execution_count += 1
        if decision.route is CognitiveRoute.REASON:
            result = self.reason_callback(problem=problem, mode=mode, knowledge_limit=knowledge_limit)
            return CognitiveExecutionResult(decision, CognitiveExecutionState.COMPLETED, result,
                "Uruchomiono kontrolowane rozumowanie. Wynik jest analizą, nie automatycznie prawdą.")
        if decision.route is CognitiveRoute.DIRECT:
            return CognitiveExecutionResult(decision, CognitiveExecutionState.COMPLETED, None,
                "Dane nie wymuszają głębszego rozumowania; nie utworzono nowej wiedzy.")
        if decision.route is CognitiveRoute.INVESTIGATE:
            return CognitiveExecutionResult(decision, CognitiveExecutionState.NEEDS_INVESTIGATION, None,
                "Najpierw potrzebne są dodatkowe dane lub obserwacje.")
        return CognitiveExecutionResult(decision, CognitiveExecutionState.INSUFFICIENT, None,
            "Brak wystarczających podstaw do dalszego uczciwego wnioskowania.")

    def stats(self) -> dict:
        return {"modul_gotowy": True, "liczba_wykonan": self.execution_count}
