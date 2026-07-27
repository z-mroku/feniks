from core.feniks import Feniks
from core.gemini_knowledge_relevance_provider import GeminiKnowledgeRelevanceProvider
from core.knowledge_relevance_engine import KnowledgeRelevanceEngine


def check(name, condition, failures):
    ok = bool(condition)
    print(f"{name}: {'TAK' if ok else 'NIE'}")
    if not ok:
        failures.append(name)


def main():
    failures = []

    print("=" * 90)
    print("TEST INTEGRACJI PRODUKCYJNEJ PAMIĘCI SEMANTYCZNEJ FENIKSA")
    print("=" * 90)

    feniks = Feniks()

    print()
    print("ETAP 1 - KOMPONENTY GŁÓWNEGO RDZENIA")
    print("-" * 90)

    check(
        "Feniks posiada GeminiKnowledgeRelevanceProvider",
        isinstance(
            feniks.knowledge_relevance_provider,
            GeminiKnowledgeRelevanceProvider,
        ),
        failures,
    )
    check(
        "Feniks posiada KnowledgeRelevanceEngine",
        isinstance(
            feniks.knowledge_relevance_engine,
            KnowledgeRelevanceEngine,
        ),
        failures,
    )
    check(
        "Silnik używa KnowledgeRetriever Feniksa",
        feniks.knowledge_relevance_engine.knowledge_retriever
        is feniks.knowledge_retriever,
        failures,
    )
    check(
        "Silnik używa providera Feniksa",
        feniks.knowledge_relevance_engine.provider
        is feniks.knowledge_relevance_provider,
        failures,
    )
    check(
        "Feniks udostępnia recall_relevant_knowledge",
        callable(feniks.recall_relevant_knowledge),
        failures,
    )

    print()
    print("ETAP 2 - SAMOOBSERWACJA")
    print("-" * 90)

    status = feniks.status()

    check(
        "Status widzi providera trafności wiedzy",
        status.get("provider_trafnosci_wiedzy_zaladowany") is True,
        failures,
    )
    check(
        "Status widzi silnik trafności wiedzy",
        status.get("silnik_trafnosci_wiedzy_zaladowany") is True,
        failures,
    )

    print()
    print("ETAP 3 - GRANICA PUSTEGO PROBLEMU")
    print("-" * 90)

    empty = feniks.recall_relevant_knowledge("   ")

    check(
        "Pusty problem nie wybiera żadnej wiedzy",
        len(empty.context.records) == 0,
        failures,
    )
    check(
        "Pusty problem nie uruchamia kandydatów",
        empty.candidate_count == 0,
        failures,
    )

    print()
    print("=" * 90)

    if failures:
        print("WERDYKT: INTEGRACJA PAMIĘCI SEMANTYCZNEJ NIEZALICZONA")
        print("=" * 90)
        print()
        print("NIEZALICZONE WARUNKI:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("WERDYKT: PRODUKCYJNA PAMIĘĆ SEMANTYCZNA JEST W GŁÓWNYM FENIKSIE")
    print("=" * 90)
    print()
    print(
        "Główny rdzeń posiada KnowledgeRetriever, produkcyjnego providera Gemini "
        "oraz KnowledgeRelevanceEngine i udostępnia semantyczne przypominanie wiedzy."
    )


if __name__ == "__main__":
    main()
