import gc
from pathlib import Path

from core.knowledge_gate import KnowledgeGate
from core.knowledge_relevance_engine import (
    KnowledgeRelevanceEngine,
    RelevanceAssessment,
    RelevanceLevel,
)
from core.knowledge_retriever import KnowledgeRetriever
from core.persistent_memory import PersistentMemory


TEST_DATABASE = Path("data") / "feniks_knowledge_relevance_test.db"


def admitted_metadata():
    return {
        "knowledge_status": "ADMITTED",
        "cycle_decision": "KANDYDAT_DO_WIEDZY",
        "validation_safe_for_memory": True,
        "false_unknowns": 0,
        "conflicts": 0,
        "unverifiable": 0,
        "hypothesis_status": "OBALONA",
        "interpretation_confidence": 0.95,
        "experiment_name": "test",
        "observation_count": 5,
        "first_contradiction_at": 1,
        "first_opposition_stronger_at": None,
        "provenance": [
            "ExperimentRunner",
            "ExperimentInterpreter",
            "ReasoningValidator",
            "KnowledgeGate",
        ],
    }


class ControlledSemanticProvider:
    """
    Deterministyczny provider testowy.

    Celowo rozpoznaje znaczenie problemu bez wymagania,
    aby problem zawierał słowo 'TruthEngine'.
    """

    def __init__(self, evidence_id, unrelated_id, injected_id):
        self.evidence_id = evidence_id
        self.unrelated_id = unrelated_id
        self.injected_id = injected_id

    def assess(self, problem, records):
        return [
            RelevanceAssessment(
                memory_id=self.evidence_id,
                level=RelevanceLevel.RELEVANT,
                score=0.96,
                reasoning=(
                    "Problem dotyczy relacji między liczbą słabszych "
                    "dowodów a jednym silnym dowodem."
                ),
            ),
            RelevanceAssessment(
                memory_id=self.unrelated_id,
                level=RelevanceLevel.IRRELEVANT,
                score=0.08,
                reasoning="Rekord dotyczy innego zagadnienia.",
            ),
            # Próba wstrzyknięcia ID, którego Retriever nie zwrócił.
            RelevanceAssessment(
                memory_id=self.injected_id,
                level=RelevanceLevel.RELEVANT,
                score=1.0,
                reasoning="Próba wstrzyknięcia obcego rekordu.",
            ),
        ]


def check(name, condition, failures):
    passed = bool(condition)
    print(f"{name}: {'TAK' if passed else 'NIE'}")
    if not passed:
        failures.append(name)


def remove_database():
    gc.collect()
    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()


def main():
    failures = []

    print("=" * 90)
    print("TEST SEMANTYCZNEGO DOBORU WCZEŚNIEJSZEJ WIEDZY FENIKSA")
    print("=" * 90)

    remove_database()
    memory = None

    try:
        memory = PersistentMemory(database_path=str(TEST_DATABASE))

        evidence_id = memory.save(
            category=KnowledgeGate.KNOWLEDGE_CATEGORY,
            title="TruthEngine: siła dowodów i saturacja",
            content=(
                "HIPOTEZA:\n"
                "Czy wiele przeciętnych dowodów przeciwnych przewyższy "
                "jeden mocny dowód wspierający?\n\n"
                "ZWERYFIKOWANE USTALENIA:\n"
                "- Sprzeczność pojawiła się przy N=1.\n"
                "- Sprzeciw nie przewyższył poparcia.\n\n"
                "GRANICE WNIOSKOWANIA:\n"
                "- Wyniku nie należy uogólniać poza przebadane parametry."
            ),
            source="FENIKS_KNOWLEDGE_GATE",
            metadata=admitted_metadata(),
        )

        unrelated_id = memory.save(
            category=KnowledgeGate.KNOWLEDGE_CATEGORY,
            title="Inny zweryfikowany eksperyment",
            content=(
                "ZWERYFIKOWANE USTALENIA:\n"
                "- Ten rekord dotyczy całkowicie innego zagadnienia."
            ),
            source="FENIKS_KNOWLEDGE_GATE",
            metadata=admitted_metadata(),
        )

        fake_id = memory.save(
            category=KnowledgeGate.KNOWLEDGE_CATEGORY,
            title="Fałszywy rekord",
            content="Nie przeszedł prawidłowej Bramy Wiedzy.",
            source="RECZNY_WPIS",
            metadata=admitted_metadata(),
        )

        retriever = KnowledgeRetriever(memory)

        provider = ControlledSemanticProvider(
            evidence_id=evidence_id,
            unrelated_id=unrelated_id,
            injected_id=fake_id,
        )

        engine = KnowledgeRelevanceEngine(
            knowledge_retriever=retriever,
            provider=provider,
            minimum_score=0.60,
        )

        print()
        print("ETAP 1 - KANDYDACI Z BEZPIECZNEJ PAMIĘCI")
        print("-" * 90)

        verified = retriever.all_verified()

        check(
            "Retriever widzi dwa prawidłowe rekordy",
            verified.count == 2,
            failures,
        )
        check(
            "Fałszywy rekord nie trafia do kandydatów",
            fake_id not in [r.memory_id for r in verified.records],
            failures,
        )

        print()
        print("ETAP 2 - PROBLEM BEZ SŁOWA KLUCZOWEGO TRUTHENGINE")
        print("-" * 90)

        problem = (
            "Czy duża liczba słabszych argumentów może ostatecznie "
            "pokonać jeden bardzo wiarygodny argument?"
        )

        check(
            "Problem nie zawiera słowa TruthEngine",
            "truthengine" not in problem.lower(),
            failures,
        )

        result = engine.select(problem)

        print("Liczba kandydatów:", result.candidate_count)
        print("Liczba wybranych rekordów:", result.selected_count)

        check(
            "Silnik rozpatrzył dwa bezpieczne rekordy",
            result.candidate_count == 2,
            failures,
        )
        check(
            "Silnik znalazł wiedzę istotną znaczeniowo",
            result.found,
            failures,
        )
        check(
            "Wybrano dokładnie jeden rekord",
            result.selected_count == 1,
            failures,
        )
        check(
            "Wybrano rekord o sile dowodów",
            (
                result.context.records[0].memory_id == evidence_id
                if result.context.records
                else False
            ),
            failures,
        )
        check(
            "Nieistotny rekord został odrzucony",
            unrelated_id not in [
                r.memory_id for r in result.context.records
            ],
            failures,
        )

        print()
        print("ETAP 3 - GRANICA BEZPIECZEŃSTWA PROVIDERA")
        print("-" * 90)

        selected_ids = [
            record.memory_id
            for record in result.context.records
        ]
        assessment_ids = [
            assessment.memory_id
            for assessment in result.assessments
        ]

        check(
            "Provider nie może wstrzyknąć fałszywego rekordu",
            fake_id not in selected_ids,
            failures,
        )
        check(
            "Ocena obcego ID została usunięta",
            fake_id not in assessment_ids,
            failures,
        )
        check(
            "Semantyka nie omija KnowledgeRetriever",
            all(
                memory_id in [r.memory_id for r in verified.records]
                for memory_id in selected_ids
            ),
            failures,
        )

        print()
        print("ETAP 4 - KONTEKST DLA DALSZEGO ROZUMOWANIA")
        print("-" * 90)

        context_text = result.context.as_text()

        check(
            "Kontekst nadal oznacza wiedzę jako wcześniejszą",
            "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA" in context_text,
            failures,
        )
        check(
            "Kontekst nadal nie rozstrzyga automatycznie problemu",
            "Nie stanowią automatycznego rozstrzygnięcia" in context_text,
            failures,
        )
        check(
            "Zachowano granice wnioskowania",
            "GRANICE WNIOSKOWANIA" in context_text,
            failures,
        )

        print()
        print("ETAP 5 - PRZYPADKI BRZEGOWE")
        print("-" * 90)

        empty = engine.select("   ")
        check(
            "Pusty problem nie uruchamia selekcji",
            empty.selected_count == 0 and empty.candidate_count == 0,
            failures,
        )

        negative_limit_rejected = False
        try:
            engine.select(problem, limit=-1)
        except ValueError:
            negative_limit_rejected = True

        check(
            "Ujemny limit jest odrzucany",
            negative_limit_rejected,
            failures,
        )

        memory = None
        gc.collect()

    finally:
        memory = None
        gc.collect()
        remove_database()

    print()
    print("=" * 90)

    if failures:
        print("WERDYKT: TEST KNOWLEDGE RELEVANCE ENGINE NIEZALICZONY")
        print("=" * 90)
        print()
        print("NIEZALICZONE WARUNKI:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("WERDYKT: FENIKS POTRAFI DOBRAĆ WIEDZĘ DO ZNACZENIA NOWEGO PROBLEMU")
    print("=" * 90)
    print()
    print(
        "Warstwa semantyczna wybrała właściwy wcześniej zweryfikowany "
        "rekord mimo braku dosłownego słowa kluczowego w nowym problemie."
    )
    print(
        "Provider mógł oceniać trafność, ale nie mógł ominąć "
        "KnowledgeRetriever ani wstrzyknąć obcego rekordu jako wiedzy."
    )


if __name__ == "__main__":
    main()
