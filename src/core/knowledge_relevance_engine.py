from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence

from core.knowledge_retriever import (
    KnowledgeContext,
    KnowledgeRetriever,
    RetrievedKnowledge,
)


class RelevanceLevel(str, Enum):
    RELEVANT = "ISTOTNE"
    PARTIAL = "CZESCIOWO_ISTOTNE"
    IRRELEVANT = "NIEISTOTNE"


@dataclass(frozen=True)
class RelevanceAssessment:
    memory_id: int
    level: RelevanceLevel
    score: float
    reasoning: str


class KnowledgeRelevanceProvider(Protocol):
    """
    Minimalny kontrakt warstwy semantycznej.

    Provider ocenia trafność wcześniej zweryfikowanych
    rekordów. Nie nadaje rekordom statusu wiedzy.
    """

    def assess(
        self,
        problem: str,
        records: Sequence[RetrievedKnowledge],
    ) -> list[RelevanceAssessment]:
        ...


@dataclass(frozen=True)
class RelevantKnowledgeResult:
    problem: str
    context: KnowledgeContext
    assessments: tuple[RelevanceAssessment, ...]
    candidate_count: int

    @property
    def found(self) -> bool:
        return self.context.found

    @property
    def selected_count(self) -> int:
        return self.context.count


class KnowledgeRelevanceEngine:
    """
    Dobiera wcześniejszą zweryfikowaną wiedzę
    do znaczenia nowego problemu.

    Granice bezpieczeństwa:
    - kandydaci pochodzą wyłącznie z KnowledgeRetriever,
    - provider semantyczny nie może dodać własnego rekordu,
    - provider nie może zmienić statusu wiedzy,
    - ocena trafności nie jest oceną prawdziwości.
    """

    def __init__(
        self,
        knowledge_retriever: KnowledgeRetriever,
        provider: KnowledgeRelevanceProvider,
        minimum_score: float = 0.60,
        include_partial: bool = True,
    ):
        if not 0.0 <= minimum_score <= 1.0:
            raise ValueError(
                "minimum_score musi mieścić się w zakresie 0.0-1.0."
            )

        self.knowledge_retriever = knowledge_retriever
        self.provider = provider
        self.minimum_score = minimum_score
        self.include_partial = include_partial

    def select(
        self,
        problem: str,
        limit: int | None = 5,
    ) -> RelevantKnowledgeResult:
        problem = problem.strip()

        if not problem:
            return RelevantKnowledgeResult(
                problem="",
                context=KnowledgeContext(query="", records=()),
                assessments=(),
                candidate_count=0,
            )

        candidates_context = self.knowledge_retriever.all_verified()
        candidates = list(candidates_context.records)

        if not candidates:
            return RelevantKnowledgeResult(
                problem=problem,
                context=KnowledgeContext(query=problem, records=()),
                assessments=(),
                candidate_count=0,
            )

        assessments = self.provider.assess(
            problem=problem,
            records=candidates,
        )

        candidate_by_id = {
            record.memory_id: record
            for record in candidates
        }

        safe_assessments: list[RelevanceAssessment] = []
        selected_pairs: list[
            tuple[RelevanceAssessment, RetrievedKnowledge]
        ] = []
        seen_ids: set[int] = set()

        for assessment in assessments:
            if assessment.memory_id in seen_ids:
                continue

            record = candidate_by_id.get(assessment.memory_id)
            if record is None:
                # Provider nie może wstrzyknąć rekordu,
                # którego nie zwrócił KnowledgeRetriever.
                continue

            if not 0.0 <= assessment.score <= 1.0:
                continue

            seen_ids.add(assessment.memory_id)
            safe_assessments.append(assessment)

            if assessment.score < self.minimum_score:
                continue

            if assessment.level is RelevanceLevel.IRRELEVANT:
                continue

            if (
                assessment.level is RelevanceLevel.PARTIAL
                and not self.include_partial
            ):
                continue

            selected_pairs.append((assessment, record))

        selected_pairs.sort(
            key=lambda pair: pair[0].score,
            reverse=True,
        )

        if limit is not None:
            if limit < 0:
                raise ValueError("limit nie może być ujemny.")
            selected_pairs = selected_pairs[:limit]

        selected_records = tuple(
            record
            for _, record in selected_pairs
        )

        return RelevantKnowledgeResult(
            problem=problem,
            context=KnowledgeContext(
                query=problem,
                records=selected_records,
            ),
            assessments=tuple(safe_assessments),
            candidate_count=len(candidates),
        )
