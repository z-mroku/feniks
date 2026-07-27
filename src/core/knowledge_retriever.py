from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.knowledge_gate import KnowledgeGate
from core.persistent_memory import PersistentMemory


@dataclass(frozen=True)
class RetrievedKnowledge:
    """Wcześniej dopuszczony rekord wiedzy FENIKSA."""

    memory_id: int
    title: str
    content: str
    source: str
    created_at: str
    metadata: dict[str, Any]
    provenance: tuple[str, ...]
    query: str

    @property
    def confidence(self) -> float | None:
        value = self.metadata.get("interpretation_confidence")
        if isinstance(value, (int, float)):
            return float(value)
        return None

    @property
    def hypothesis_status(self) -> str | None:
        value = self.metadata.get("hypothesis_status")
        return value if isinstance(value, str) else None


@dataclass(frozen=True)
class KnowledgeContext:
    """Bezpieczny kontekst wcześniejszej wiedzy."""

    query: str
    records: tuple[RetrievedKnowledge, ...]

    @property
    def found(self) -> bool:
        return bool(self.records)

    @property
    def count(self) -> int:
        return len(self.records)

    def as_text(self) -> str:
        if not self.records:
            return (
                "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA:\n"
                "Brak pasujących rekordów."
            )

        sections = [
            "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA:",
            (
                "Poniższe rekordy są materiałem kontekstowym. "
                "Nie stanowią automatycznego rozstrzygnięcia "
                "nowego problemu."
            ),
        ]

        for index, record in enumerate(self.records, start=1):
            sections.extend([
                "",
                f"REKORD {index}",
                f"ID: {record.memory_id}",
                f"TYTUŁ: {record.title}",
                f"ŹRÓDŁO: {record.source}",
                f"PEWNOŚĆ INTERPRETACJI: {record.confidence}",
                f"STATUS HIPOTEZY: {record.hypothesis_status}",
                "POCHODZENIE: " + " -> ".join(record.provenance),
                "TREŚĆ:",
                record.content,
            ])

        return "\n".join(sections)


class KnowledgeRetriever:
    """
    Kontrolowany dostęp do wcześniej zweryfikowanej wiedzy.

    Znalezienie rekordu nie oznacza, że rekord rozstrzyga
    nowy problem. Retriever jedynie przygotowuje kontekst.
    """

    EXPECTED_SOURCE = "FENIKS_KNOWLEDGE_GATE"
    EXPECTED_PROVENANCE = (
        "ExperimentRunner",
        "ExperimentInterpreter",
        "ReasoningValidator",
        "KnowledgeGate",
    )

    def __init__(self, persistent_memory: PersistentMemory):
        self.persistent_memory = persistent_memory

    def retrieve(
        self,
        query: str,
        limit: int | None = 10,
    ) -> KnowledgeContext:
        query = query.strip()

        if not query:
            return KnowledgeContext(query="", records=())

        candidates = self.persistent_memory.search(query)

        records = [
            self._to_retrieved_knowledge(memory, query)
            for memory in candidates
            if self._is_admitted_knowledge(memory)
        ]

        records = self._apply_limit(records, limit)

        return KnowledgeContext(
            query=query,
            records=tuple(records),
        )

    def all_verified(
        self,
        limit: int | None = None,
    ) -> KnowledgeContext:
        candidates = self.persistent_memory.find_by_category(
            KnowledgeGate.KNOWLEDGE_CATEGORY
        )

        records = [
            self._to_retrieved_knowledge(memory, "")
            for memory in candidates
            if self._is_admitted_knowledge(memory)
        ]

        records = self._apply_limit(records, limit)

        return KnowledgeContext(
            query="",
            records=tuple(records),
        )

    @staticmethod
    def _apply_limit(
        records: list[RetrievedKnowledge],
        limit: int | None,
    ) -> list[RetrievedKnowledge]:
        if limit is None:
            return records

        if limit < 0:
            raise ValueError("limit nie może być ujemny.")

        return records[:limit]

    def _is_admitted_knowledge(
        self,
        memory: dict[str, Any],
    ) -> bool:
        if memory.get("kategoria") != KnowledgeGate.KNOWLEDGE_CATEGORY:
            return False

        if memory.get("zrodlo") != self.EXPECTED_SOURCE:
            return False

        metadata = memory.get("metadane")
        if not isinstance(metadata, dict):
            return False

        if metadata.get("knowledge_status") != "ADMITTED":
            return False

        if metadata.get("validation_safe_for_memory") is not True:
            return False

        if metadata.get("false_unknowns") != 0:
            return False

        if metadata.get("conflicts") != 0:
            return False

        if metadata.get("unverifiable") != 0:
            return False

        if metadata.get("provenance") != list(self.EXPECTED_PROVENANCE):
            return False

        return True

    @staticmethod
    def _to_retrieved_knowledge(
        memory: dict[str, Any],
        query: str,
    ) -> RetrievedKnowledge:
        metadata = dict(memory.get("metadane", {}))

        return RetrievedKnowledge(
            memory_id=int(memory["id"]),
            title=str(memory.get("tytul") or ""),
            content=str(memory.get("tresc") or ""),
            source=str(memory.get("zrodlo") or ""),
            created_at=str(memory.get("utworzono") or ""),
            metadata=metadata,
            provenance=tuple(metadata.get("provenance", [])),
            query=query,
        )
