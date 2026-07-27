import gc
import os
import tempfile

from core.feniks import Feniks
from core.knowledge_relevance_engine import KnowledgeRelevanceEngine
from core.knowledge_retriever import KnowledgeRetriever
from core.persistent_memory import PersistentMemory


PROVENANCE = [
    "ExperimentRunner",
    "ExperimentInterpreter",
    "ReasoningValidator",
    "KnowledgeGate",
]


def check(name, condition, failures):
    passed = bool(condition)
    print(f"{name}: {'TAK' if passed else 'NIE'}")
    if not passed:
        failures.append(name)


def verified_metadata():
    return {
        "knowledge_status": "ADMITTED",
        "cycle_decision": "KANDYDAT_DO_WIEDZY",
        "validation_safe_for_memory": True,
        "false_unknowns": 0,
        "conflicts": 0,
        "unverifiable": 0,
        "hypothesis_status": "NIEROZSTRZYGNIETA",
        "interpretation_confidence": 0.95,
        "experiment_name": "semantic_memory_end_to_end",
        "observation_count": 10,
        "first_contradiction_at": 1,
        "first_opposition_stronger_at": None,
        "provenance": PROVENANCE,
    }


def main():
    failures = []

    print("=" * 90)
    print("TEST END-TO-END PRODUKCYJNEJ PAMIĘCI SEMANTYCZNEJ FENIKSA")
    print("=" * 90)

    print()
    print("ETAP 1 - URUCHOMIENIE GŁÓWNEGO FENIKSA")
    print("-" * 90)

    feniks = Feniks()

    check(
        "Feniks udostępnia semantyczne przypominanie wiedzy",
        callable(feniks.recall_relevant_knowledge),
        failures,
    )
    check(
        "Produkcyjny provider Gemini jest dostępny",
        feniks.knowledge_relevance_provider is not None,
        failures,
    )

    print()
    print("ETAP 2 - IZOLACJA TESTU OD RZECZYWISTEJ PAMIĘCI")
    print("-" * 90)

    with tempfile.TemporaryDirectory() as temp_directory:
        database_path = os.path.join(
            temp_directory,
            "feniks_semantic_end_to_end.db",
        )

        isolated_memory = PersistentMemory(
            database_path=database_path
        )
        isolated_retriever = KnowledgeRetriever(
            persistent_memory=isolated_memory
        )

        # Podmieniamy wyłącznie pamięć testową i zależne od niej
        # komponenty. Produkcyjny provider Gemini pozostaje ten sam.
        feniks.persistent_memory = isolated_memory
        feniks.knowledge_retriever = isolated_retriever
        feniks.knowledge_relevance_engine = KnowledgeRelevanceEngine(
            knowledge_retriever=isolated_retriever,
            provider=feniks.knowledge_relevance_provider,
        )

        check(
            "Test używa izolowanej bazy SQLite",
            feniks.knowledge_retriever.persistent_memory
            is isolated_memory,
            failures,
        )
        check(
            "Baza testowa jest początkowo pusta",
            isolated_memory.count() == 0,
            failures,
        )

        print()
        print("ETAP 3 - PRZYGOTOWANIE WIEDZY I REKORDU-PUŁAPKI")
        print("-" * 90)

        relevant_id = isolated_memory.save(
            category="ZWERYFIKOWANA_WIEDZA",
            title="Wpływ liczby słabszych dowodów na jeden mocny dowód",
            content=(
                "HIPOTEZA:\n"
                "Czy wiele przeciętnych dowodów przeciwnych może "
                "przewyższyć jeden mocny dowód?\n\n"
                "STATUS HIPOTEZY:\n"
                "NIEROZSTRZYGNIETA\n\n"
                "ZWERYFIKOWANE USTALENIA:\n"
                "- Eksperyment badał relację liczby dowodów do ich siły.\n"
                "- W przebadanym zakresie rosnąca liczba słabszych "
                "dowodów nie przewyższyła jednego mocnego poparcia.\n\n"
                "GRANICE WNIOSKOWANIA:\n"
                "- Nie wolno uogólniać wyniku poza przebadane parametry.\n\n"
                "DANE EKSPERYMENTALNE:\n"
                "Liczba obserwacji: 10\n"
                "Pierwsza sprzeczność: 1\n"
                "Pierwsza przewaga sprzeciwu: None\n\n"
                "POCHODZENIE:\n"
                "ExperimentRunner -> Interpreter -> "
                "ReasoningValidator -> KnowledgeGate"
            ),
            source="FENIKS_KNOWLEDGE_GATE",
            metadata=verified_metadata(),
        )

        irrelevant_id = isolated_memory.save(
            category="ZWERYFIKOWANA_WIEDZA",
            title="Trwałość zapisu SQLite",
            content=(
                "HIPOTEZA:\n"
                "Czy zapisany rekord można ponownie odczytać?\n\n"
                "ZWERYFIKOWANE USTALENIA:\n"
                "- Rekord zapisany w SQLite został ponownie odczytany.\n\n"
                "GRANICE WNIOSKOWANIA:\n"
                "- Test dotyczył trwałości technicznego zapisu danych.\n\n"
                "DANE EKSPERYMENTALNE:\n"
                "Liczba obserwacji: 1\n\n"
                "POCHODZENIE:\n"
                "ExperimentRunner -> Interpreter -> "
                "ReasoningValidator -> KnowledgeGate"
            ),
            source="FENIKS_KNOWLEDGE_GATE",
            metadata=verified_metadata(),
        )

        trap_id = isolated_memory.save(
            category="ZWERYFIKOWANA_WIEDZA",
            title="Fałszywy rekord o sile argumentów",
            content=(
                "Ten rekord jest bardzo podobny znaczeniowo do problemu, "
                "ale nie pochodzi z Bramy Wiedzy."
            ),
            source="RECZNY_WPIS",
            metadata=verified_metadata(),
        )

        check(
            "W bazie fizycznie istnieją trzy rekordy",
            isolated_memory.count() == 3,
            failures,
        )

        safe_context = feniks.all_verified_knowledge()
        safe_ids = {
            record.memory_id
            for record in safe_context.records
        }

        check(
            "Retriever dopuścił dwa prawidłowe rekordy",
            len(safe_ids) == 2,
            failures,
        )
        check(
            "Wiedza o sile dowodów jest bezpiecznym kandydatem",
            relevant_id in safe_ids,
            failures,
        )
        check(
            "Wiedza SQLite jest bezpiecznym kandydatem",
            irrelevant_id in safe_ids,
            failures,
        )
        check(
            "Rekord-pułapka został odrzucony przed Gemini",
            trap_id not in safe_ids,
            failures,
        )

        print()
        print("ETAP 4 - PRAWDZIWE GEMINI I SEMANTYCZNE PRZYPOMNIENIE")
        print("-" * 90)

        problem = (
            "Czy ogromna liczba słabszych argumentów może ostatecznie "
            "pokonać jeden bardzo wiarygodny argument?"
        )

        count_before_recall = isolated_memory.count()

        result = feniks.recall_relevant_knowledge(
            problem=problem,
            limit=5,
        )

        count_after_recall = isolated_memory.count()

        selected_ids = {
            record.memory_id
            for record in result.context.records
        }
        assessed_ids = {
            assessment.memory_id
            for assessment in result.assessments
        }

        print("Liczba bezpiecznych kandydatów:", result.candidate_count)
        print("Liczba wybranych rekordów:", len(result.context.records))
        print("Wybrane ID:", sorted(selected_ids))

        for assessment in result.assessments:
            print(
                f"ID={assessment.memory_id} | "
                f"{assessment.level.value} | "
                f"score={assessment.score:.2f}"
            )
            print("Uzasadnienie:", assessment.reasoning)

        check(
            "Gemini otrzymało tylko dwa bezpieczne rekordy",
            result.candidate_count == 2,
            failures,
        )
        check(
            "Gemini oceniło wiedzę o sile dowodów",
            relevant_id in assessed_ids,
            failures,
        )
        check(
            "Gemini oceniło wiedzę SQLite",
            irrelevant_id in assessed_ids,
            failures,
        )
        check(
            "Gemini nigdy nie otrzymało rekordu-pułapki",
            trap_id not in assessed_ids,
            failures,
        )
        check(
            "Feniks przypomniał właściwą wiedzę znaczeniowo",
            relevant_id in selected_ids,
            failures,
        )
        check(
            "Nieistotna wiedza SQLite nie została wybrana",
            irrelevant_id not in selected_ids,
            failures,
        )
        check(
            "Rekord-pułapka nie został wybrany",
            trap_id not in selected_ids,
            failures,
        )

        print()
        print("ETAP 5 - KONTROLA BRAKU ZAPISU PODCZAS PRZYPOMINANIA")
        print("-" * 90)

        check(
            "Liczba rekordów nie zmieniła się po przypomnieniu",
            count_before_recall == count_after_recall == 3,
            failures,
        )
        check(
            "Semantyczne przypomnienie nie utworzyło nowej wiedzy",
            isolated_memory.count() == 3,
            failures,
        )

        print()
        print("ETAP 6 - KONTROLA KONTEKSTU")
        print("-" * 90)

        context_text = result.context.as_text()

        check(
            "Kontekst zachowuje treść nowego problemu",
            result.context.query == problem,
            failures,
        )
        check(
            "Kontekst oznacza dane jako wcześniejszą wiedzę",
            "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA" in context_text,
            failures,
        )
        check(
            "Kontekst nie przedstawia pamięci jako automatycznego rozstrzygnięcia",
            "Nie stanowią automatycznego rozstrzygnięcia" in context_text,
            failures,
        )
        check(
            "Kontekst zachowuje granice wnioskowania",
            "GRANICE WNIOSKOWANIA" in context_text,
            failures,
        )

        # Jawnie zwalniamy referencje przed usunięciem katalogu
        # tymczasowego, aby Windows nie trzymał pliku SQLite.
        feniks.knowledge_relevance_engine = None
        feniks.knowledge_retriever = None
        feniks.persistent_memory = None
        isolated_retriever = None
        isolated_memory = None
        gc.collect()

    print()
    print("=" * 90)

    if failures:
        print("WERDYKT: TEST END-TO-END PAMIĘCI SEMANTYCZNEJ NIEZALICZONY")
        print("=" * 90)
        print()
        print("NIEZALICZONE WARUNKI:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("WERDYKT: FENIKS SAMODZIELNIE PRZYPOMINA SOBIE WŁAŚCIWĄ WIEDZĘ")
    print("=" * 90)
    print()
    print(
        "Pełny łańcuch przeszedł przez główny rdzeń FENIKSA, "
        "izolowaną pamięć SQLite, KnowledgeRetriever, prawdziwe Gemini "
        "i KnowledgeRelevanceEngine."
    )
    print(
        "Fałszywy rekord został zatrzymany przed warstwą semantyczną, "
        "nieistotna wiedza nie została wybrana, a samo przypominanie "
        "nie zmodyfikowało trwałej pamięci."
    )


if __name__ == "__main__":
    main()
