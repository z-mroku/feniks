from __future__ import annotations

import os
from typing import Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from core.knowledge_relevance_engine import (
    KnowledgeRelevanceProvider,
    RelevanceAssessment,
    RelevanceLevel,
)
from core.knowledge_retriever import RetrievedKnowledge


class _GeminiRelevanceAssessment(BaseModel):
    memory_id: int
    level: RelevanceLevel
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class _GeminiRelevanceResponse(BaseModel):
    assessments: list[_GeminiRelevanceAssessment]


class GeminiKnowledgeRelevanceProvider(KnowledgeRelevanceProvider):
    """
    Produkcyjna warstwa semantyczna do oceny trafności
    wcześniej zweryfikowanej wiedzy.

    Gemini nie otrzymuje prawa zapisu do pamięci.
    Może wyłącznie oceniać rekordy przekazane przez
    KnowledgeRelevanceEngine.
    """

    MODEL = "gemini-3.5-flash"

    SYSTEM_INSTRUCTION = """
Jesteś zewnętrzną warstwą semantycznej oceny trafności
dla systemu FENIKS.

Otrzymujesz:
1. nowy problem,
2. listę wcześniej zweryfikowanych rekordów wiedzy.

Twoim jedynym zadaniem jest ocenić, czy każdy przekazany
rekord może być przydatnym kontekstem dla nowego problemu.

Nie oceniasz, czy nowy problem jest prawdziwy.
Nie rozwiązujesz problemu.
Nie tworzysz nowej wiedzy.
Nie zmieniasz statusu żadnego rekordu.
Nie wolno ci tworzyć nowych memory_id.
Nie wolno ci traktować podobieństwa słów jako dowodu trafności.

Dla każdego przekazanego rekordu zwróć dokładnie jedną ocenę:

ISTOTNE
- rekord bezpośrednio dotyczy mechanizmu, zależności,
  zjawiska lub pytania zawartego w nowym problemie;

CZESCIOWO_ISTOTNE
- rekord może dostarczyć użytecznego kontekstu,
  ale dotyczy tylko części problemu albo analogicznego mechanizmu;

NIEISTOTNE
- rekord nie wnosi użytecznego kontekstu do tego problemu.

score musi być liczbą od 0.0 do 1.0 i oznacza wyłącznie
pewność oceny trafności, a nie prawdziwość rekordu.

reasoning ma krótko wyjaśniać związek znaczeniowy
między problemem a rekordem.

Historia i wcześniejsza wiedza FENIKSA są kontekstem,
a nie automatycznym rozstrzygnięciem nowego problemu.
""".strip()

    def __init__(
        self,
        model: Optional[str] = None,
    ):
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError(
                "Brak GEMINI_API_KEY w środowisku."
            )

        self.model = model or self.MODEL
        self.client = genai.Client()

    def assess(
        self,
        problem: str,
        records: list[RetrievedKnowledge],
    ) -> list[RelevanceAssessment]:
        if not problem.strip():
            return []

        if not records:
            return []

        prompt = self._build_prompt(
            problem=problem,
            records=records,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=_GeminiRelevanceResponse,
                temperature=0.1,
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini nie zwróciło oceny trafności wiedzy."
            )

        parsed = _GeminiRelevanceResponse.model_validate_json(
            response.text
        )

        return [
            RelevanceAssessment(
                memory_id=item.memory_id,
                level=item.level,
                score=item.score,
                reasoning=item.reasoning.strip(),
            )
            for item in parsed.assessments
        ]

    def _build_prompt(
        self,
        problem: str,
        records: list[RetrievedKnowledge],
    ) -> str:
        blocks = []

        for record in records:
            blocks.append(
                "\n".join(
                    [
                        f"MEMORY_ID: {record.memory_id}",
                        f"TYTUŁ: {record.title}",
                        f"ŹRÓDŁO: {record.source}",
                        "TREŚĆ:",
                        record.content,
                    ]
                )
            )

        records_text = "\n\n--- REKORD ---\n\n".join(blocks)

        return (
            "NOWY PROBLEM:\n"
            f"{problem.strip()}\n\n"
            "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA:\n"
            f"{records_text}\n\n"
            "Oceń trafność każdego przekazanego rekordu. "
            "Nie rozwiązuj nowego problemu."
        )
