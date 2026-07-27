from core.gemini_knowledge_relevance_provider import (
    GeminiKnowledgeRelevanceProvider,
)
from core.knowledge_relevance_engine import RelevanceLevel
from core.knowledge_retriever import RetrievedKnowledge


PROVENANCE = (
    "ExperimentRunner",
    "ExperimentInterpreter",
    "ReasoningValidator",
    "KnowledgeGate",
)


def check(name, condition, failures):
    passed = bool(condition)
    print(f"{name}: {'TAK' if passed else 'NIE'}")
    if not passed:
        failures.append(name)


def make_record(memory_id, title, content):
    metadata = {
        "knowledge_status": "ADMITTED",
        "validation_safe_for_memory": True,
        "false_unknowns": 0,
        "conflicts": 0,
        "unverifiable": 0,
        "interpretation_confidence": 0.95,
        "hypothesis_status": "OBALONA",
        "provenance": list(PROVENANCE),
    }

    return RetrievedKnowledge(
        memory_id=memory_id,
        title=title,
        content=content,
        source="FENIKS_KNOWLEDGE_GATE",
        created_at="2026-07-27T00:00:00",
        metadata=metadata,
        provenance=PROVENANCE,
        query="test_semantycznej_trafnosci",
    )


def main():
    failures = []

    print("=" * 90)
    print("TEST PRODUKCYJNEGO GEMINI KNOWLEDGE RELEVANCE PROVIDER")
    print("=" * 90)

    provider = GeminiKnowledgeRelevanceProvider()

    relevant = make_record(
        101,
        "Siła dowodów i saturacja sprzeciwu",
        (
            "Eksperyment badał, czy rosnąca liczba przeciętnych "
            "dowodów przeciwnych może przewyższyć jeden mocny dowód. "
            "Sprzeczność wystąpiła przy N=1, ale w przebadanym zakresie "
            "sprzeciw nie przewyższył poparcia. Nie wolno uogólniać "
            "wyniku poza przebadane parametry."
        ),
    )

    irrelevant = make_record(
        202,
        "Trwałość zapisu pamięci SQLite",
        (
            "Test potwierdził, że rekord zapisany w SQLite można "
            "ponownie odczytać po zakończeniu operacji zapisu."
        ),
    )

    problem = (
        "Czy bardzo duża liczba słabszych argumentów może ostatecznie "
        "przeważyć nad jednym bardzo wiarygodnym argumentem?"
    )

    print()
    print("ETAP 1 - KONSTRUKCJA REKORDÓW I PROVIDERA")
    print("-" * 90)

    check(
        "Rekord 101 został poprawnie utworzony",
        relevant.memory_id == 101,
        failures,
    )
    check(
        "Rekord 202 został poprawnie utworzony",
        irrelevant.memory_id == 202,
        failures,
    )
    check(
        "Rekordy zachowują pełne pochodzenie",
        relevant.provenance == PROVENANCE
        and irrelevant.provenance == PROVENANCE,
        failures,
    )

    print("Model:", provider.model)
    check(
        "Provider używa oczekiwanego modelu",
        provider.model == "gemini-3.5-flash",
        failures,
    )

    print()
    print("ETAP 2 - PRAWDZIWA SEMANTYCZNA OCENA GEMINI")
    print("-" * 90)

    assessments = provider.assess(
        problem=problem,
        records=[relevant, irrelevant],
    )

    print("Liczba ocen:", len(assessments))

    for assessment in assessments:
        print(
            f"ID={assessment.memory_id} | "
            f"{assessment.level.value} | "
            f"score={assessment.score:.2f}"
        )
        print("Uzasadnienie:", assessment.reasoning)

    by_id = {
        assessment.memory_id: assessment
        for assessment in assessments
    }

    check(
        "Gemini zwróciło ocenę rekordu 101",
        101 in by_id,
        failures,
    )
    check(
        "Gemini zwróciło ocenę rekordu 202",
        202 in by_id,
        failures,
    )
    check(
        "Gemini nie utworzyło obcego ID",
        set(by_id).issubset({101, 202}),
        failures,
    )
    check(
        "Gemini zwróciło po jednej ocenie dla każdego rekordu",
        len(assessments) == 2 and len(by_id) == 2,
        failures,
    )

    if 101 in by_id:
        check(
            "Rekord o sile dowodów został rozpoznany jako użyteczny",
            by_id[101].level
            in {
                RelevanceLevel.RELEVANT,
                RelevanceLevel.PARTIAL,
            },
            failures,
        )
        check(
            "Ocena rekordu 101 mieści się w zakresie 0-1",
            0.0 <= by_id[101].score <= 1.0,
            failures,
        )
        check(
            "Rekord 101 ma uzasadnienie semantyczne",
            bool(by_id[101].reasoning.strip()),
            failures,
        )

    if 202 in by_id:
        check(
            "Rekord SQLite nie został uznany za bezpośrednio istotny",
            by_id[202].level is not RelevanceLevel.RELEVANT,
            failures,
        )
        check(
            "Ocena rekordu 202 mieści się w zakresie 0-1",
            0.0 <= by_id[202].score <= 1.0,
            failures,
        )
        check(
            "Rekord 202 ma uzasadnienie semantyczne",
            bool(by_id[202].reasoning.strip()),
            failures,
        )

    print()
    print("ETAP 3 - GRANICE PROVIDERA")
    print("-" * 90)

    check(
        "Pusty problem zwraca pustą listę",
        provider.assess("   ", [relevant]) == [],
        failures,
    )
    check(
        "Brak rekordów zwraca pustą listę",
        provider.assess(problem, []) == [],
        failures,
    )

    print()
    print("=" * 90)

    if failures:
        print("WERDYKT: TEST PRODUKCYJNEGO PROVIDERA GEMINI NIEZALICZONY")
        print("=" * 90)
        print()
        print("NIEZALICZONE WARUNKI:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("WERDYKT: GEMINI POTRAFI OCENIAĆ TRAFNOŚĆ WCZEŚNIEJSZEJ WIEDZY")
    print("=" * 90)
    print()
    print(
        "Gemini działa wyłącznie jako warstwa semantycznej oceny "
        "trafności. Rekordy wejściowe zachowują źródło, pochodzenie "
        "i status wcześniej zweryfikowanej wiedzy."
    )
    print(
        "Provider nie zapisuje wiedzy i nie nadaje jej statusu. "
        "Ostateczna selekcja nadal należy do kodu FENIKSA."
    )


if __name__ == "__main__":
    main()
