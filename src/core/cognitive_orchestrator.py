from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from core.reasoning_engine import ReasoningEngine, ReasoningProblem, ReasoningResult

class CognitiveRoute(Enum):
    DIRECT = "DIRECT"
    REASON = "REASON"
    INVESTIGATE = "INVESTIGATE"
    INSUFFICIENT = "INSUFFICIENT"

@dataclass(frozen=True)
class CognitiveRouteDecision:
    route: CognitiveRoute
    reason: str
    structural_analysis: ReasoningResult

class RoutePolicy(Protocol):
    def choose(self, problem: ReasoningProblem, structural_analysis: ReasoningResult) -> tuple[CognitiveRoute, str]:
        ...

class ConservativeRoutePolicy:
    """Pierwsza ostrożna polityka: korzysta wyłącznie z jawnej struktury wejścia."""
    def choose(self, problem: ReasoningProblem, structural_analysis: ReasoningResult) -> tuple[CognitiveRoute, str]:
        evidence_count = len(problem.evidence)
        unknown_count = len(problem.unknowns)

        if evidence_count == 0 and unknown_count == 0:
            return CognitiveRoute.INSUFFICIENT, (
                "Brak jawnych dowodów i zapisanych niewiadomych. "
                "Brak podstaw do uczciwego rozstrzygnięcia."
            )
        if evidence_count == 0:
            return CognitiveRoute.INVESTIGATE, (
                "Są jawne niewiadome, ale brak bieżących dowodów. "
                "Najpierw trzeba zdobyć dane."
            )
        if unknown_count > 0:
            return CognitiveRoute.REASON, (
                "Są bieżące dowody oraz nierozstrzygnięte niewiadome. "
                "Uzasadniona jest dalsza analiza."
            )
        return CognitiveRoute.DIRECT, (
            "Są bieżące dowody i brak jawnych niewiadomych. "
            "Struktura wejścia nie wymusza dalszego badania."
        )

class CognitiveOrchestrator:
    """Wybiera następny krok poznawczy; nie rozstrzyga prawdy i nie zapisuje wiedzy."""
    def __init__(self, reasoning_engine: ReasoningEngine, policy: RoutePolicy | None = None):
        self.reasoning_engine = reasoning_engine
        self.policy = policy or ConservativeRoutePolicy()
        self.decision_count = 0

    def decide(self, problem: ReasoningProblem) -> CognitiveRouteDecision:
        structural = self.reasoning_engine.analyze(problem)
        route, reason = self.policy.choose(problem, structural)
        self.decision_count += 1
        return CognitiveRouteDecision(route, reason, structural)

    def stats(self) -> dict:
        return {
            "modul_gotowy": True,
            "liczba_decyzji": self.decision_count,
            "polityka": type(self.policy).__name__,
        }
