from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from core.cognitive_executor import (
    CognitiveExecutionResult,
    CognitiveExecutionState,
)
from core.cognitive_orchestrator import CognitiveRoute


@dataclass(frozen=True)
class HumanResponse:
    """
    Odpowiedź przeznaczona dla człowieka.

    Treść nie może zmieniać statusu poznawczego wyniku
    ani tworzyć nowych faktów.
    """
    text: str
    source_state: CognitiveExecutionState
    source_route: CognitiveRoute
    used_reasoning: bool


class ResponseRenderer(Protocol):
    def render_reasoning(self, reasoning_result: Any) -> str:
        ...


class SafePolishResponseRenderer:
    """
    Deterministyczny renderer pierwszej wersji.

    Nie korzysta z modelu językowego, więc nie może dopisać
    nowych faktów podczas stylistycznego wygładzania odpowiedzi.
    """

    def render_reasoning(self, reasoning_result: Any) -> str:
        if reasoning_result is None:
            return ""

        parts: list[str] = []

        understood = getattr(reasoning_result, "problem_understood_as", "")
        if understood:
            parts.append(str(understood).strip())

        known = list(getattr(reasoning_result, "known_facts", []) or [])
        if known:
            parts.append(
                "Na podstawie dostępnych danych wiadomo, że "
                + "; ".join(str(x).strip() for x in known if str(x).strip())
                + "."
            )

        unknowns = list(getattr(reasoning_result, "unknowns", []) or [])
        cannot = list(
            getattr(reasoning_result, "cannot_conclude_yet", []) or []
        )
        limits = [
            str(x).strip()
            for x in unknowns + cannot
            if str(x).strip()
        ]
        if limits:
            parts.append(
                "Nadal nie można uczciwie rozstrzygnąć: "
                + "; ".join(limits)
                + "."
            )

        hypothesis = str(
            getattr(reasoning_result, "hypothesis", "") or ""
        ).strip()
        if hypothesis:
            parts.append(
                "Hipoteza do sprawdzenia: " + hypothesis + "."
            )

        experiment = str(
            getattr(reasoning_result, "experiment", "") or ""
        ).strip()
        if experiment:
            parts.append(
                "Żeby pójść dalej, można sprawdzić to tak: "
                + experiment
            )

        if not parts:
            return (
                "Analiza została wykonana, ale nie zawiera treści, "
                "które można bezpiecznie przedstawić jako ustalenia."
            )

        return " ".join(parts)


class ResponseEngine:
    """
    Zamienia wynik procesu poznawczego na bezpieczną,
    naturalną odpowiedź po polsku.

    Ta warstwa nie ustala prawdy i nie zapisuje wiedzy.
    """

    def __init__(self, renderer: ResponseRenderer | None = None):
        self.renderer = renderer or SafePolishResponseRenderer()
        self.response_count = 0

    def respond(
        self,
        execution: CognitiveExecutionResult,
    ) -> HumanResponse:
        if not isinstance(execution, CognitiveExecutionResult):
            raise TypeError(
                "execution musi być obiektem CognitiveExecutionResult."
            )

        self.response_count += 1
        route = execution.decision.route

        if execution.state is CognitiveExecutionState.INSUFFICIENT:
            text = (
                "Nie mam jeszcze wystarczających danych, żeby to "
                "uczciwie rozstrzygnąć. Potrzebuję najpierw konkretnych "
                "informacji, na których można oprzeć odpowiedź."
            )
        elif (
            execution.state
            is CognitiveExecutionState.NEEDS_INVESTIGATION
        ):
            text = (
                "Tego jeszcze nie da się uczciwie rozstrzygnąć. "
                "Brakuje danych lub obserwacji, które trzeba najpierw "
                "zdobyć albo sprawdzić."
            )
        elif route is CognitiveRoute.REASON:
            text = self.renderer.render_reasoning(
                execution.reasoning_result
            )
        elif route is CognitiveRoute.DIRECT:
            text = (
                "Mam dane, ale na tym etapie rdzeń FENIKSA nie tworzy "
                "jeszcze z tej ścieżki samodzielnej odpowiedzi. "
                "Nie będę dopowiadał czegoś, czego system nie ustalił."
            )
        else:
            text = (
                "Nie mogę jeszcze przygotować bezpiecznej odpowiedzi "
                "na podstawie tego wyniku."
            )

        return HumanResponse(
            text=text,
            source_state=execution.state,
            source_route=route,
            used_reasoning=execution.reasoning_result is not None,
        )

    def stats(self) -> dict:
        return {
            "modul_gotowy": True,
            "liczba_odpowiedzi": self.response_count,
            "jezyk_domyslny": "pl",
        }
