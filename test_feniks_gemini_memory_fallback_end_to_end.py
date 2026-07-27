from core.experiment_interpreter import (
    GeminiExperimentInterpreter,
    HypothesisStatus,
)
from core.experiment_runner import ExperimentRunner


def check(name, condition, failures):
    ok = bool(condition)
    print(f"{name}: {'TAK' if ok else 'NIE'}")
    if not ok:
        failures.append(name)


def main():
    failures = []

    print("=" * 90)
    print("TEST PRODUKCYJNY: PAMIĘĆ + PRAWDZIWE GEMINI + AUTOMATYCZNY FALLBACK")
    print("=" * 90)

    hypothesis = (
        "W badanym zakresie rosnąca liczba słabszych dowodów przeciwnych "
        "ostatecznie przewyższy jeden bardzo mocny dowód popierający."
    )

    print()
    print("ETAP 1 - RZECZYWISTY EKSPERYMENT")
    print("-" * 90)

    runner = ExperimentRunner()
    result = runner.run_quantity_vs_quality(
        strong_support_reliability=0.95,
        opposing_reliability=0.50,
        max_opposing=20,
    )

    print("Nazwa eksperymentu:", result.name)
    print("Liczba obserwacji:", len(result.observations))
    print("Pierwsza sprzeczność:", result.first_contradiction_at)
    print("Pierwsza przewaga sprzeciwu:", result.first_opposition_stronger_at)

    check(
        "Eksperyment zawiera rzeczywiste obserwacje",
        len(result.observations) > 0,
        failures,
    )

    print()
    print("ETAP 2 - CELOWO SPRZECZNY KONTEKST WCZEŚNIEJSZEJ WIEDZY")
    print("-" * 90)

    misleading_context = """
WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA FENIKSA:

Poprzedni rekord sugerował, że wiele słabszych dowodów przeciwnych
zawsze ostatecznie przewyższa jeden mocny dowód popierający.

WAŻNE:
To jest wyłącznie wcześniejszy kontekst.
Nie jest obserwacją bieżącego eksperymentu.
"""

    check(
        "Przygotowano wcześniejszą wiedzę sprzeczną z bieżącym wynikiem",
        "zawsze ostatecznie przewyższa" in misleading_context,
        failures,
    )

    print()
    print("ETAP 3 - PRAWDZIWE GEMINI Z PRODUKCYJNYM FALLBACKIEM")
    print("-" * 90)

    # Bez wymuszania modelu: używamy produkcyjnej konfiguracji interpretera.
    interpreter = GeminiExperimentInterpreter()

    interpretation = interpreter.interpret(
        hypothesis=hypothesis,
        result=result,
        prior_knowledge_context=misleading_context,
    )

    print("Model podstawowy:", interpreter.model)
    print("Model zapasowy:", interpreter.fallback_model)
    print("Model faktycznie użyty:", interpreter.last_model_used)
    print(
        "Czy użyto fallbacku:",
        "TAK" if interpreter.last_fallback_used else "NIE",
    )

    if interpreter.last_primary_error:
        print("Awaria modelu podstawowego została odnotowana: TAK")
        print("Skrót błędu:", interpreter.last_primary_error[:220])
    else:
        print("Awaria modelu podstawowego została odnotowana: NIE - model podstawowy zadziałał")

    print()
    print("Status hipotezy:", interpretation.hypothesis_status.value)
    print("Pewność:", interpretation.confidence)
    print("Uzasadnienie:")
    print(interpretation.reasoning)

    check(
        "Interpreter jawnie wskazuje faktycznie użyty model",
        interpreter.last_model_used
        in {interpreter.model, interpreter.fallback_model},
        failures,
    )

    if interpreter.last_fallback_used:
        check(
            "Fallback oznacza użycie modelu zapasowego",
            interpreter.last_model_used == interpreter.fallback_model,
            failures,
        )
        check(
            "Przy fallbacku zachowano błąd modelu podstawowego",
            bool(interpreter.last_primary_error),
            failures,
        )
    else:
        check(
            "Bez fallbacku użyto modelu podstawowego",
            interpreter.last_model_used == interpreter.model,
            failures,
        )

    print()
    print("ETAP 4 - PIERWSZEŃSTWO BIEŻĄCYCH DOWODÓW")
    print("-" * 90)

    if result.first_opposition_stronger_at is None:
        expected_status = HypothesisStatus.REJECTED
        print("Dane programu: sprzeciw NIE przewyższył poparcia w badanym zakresie.")
    else:
        expected_status = HypothesisStatus.CONFIRMED
        print(
            "Dane programu: sprzeciw przewyższył poparcie przy N=",
            result.first_opposition_stronger_at,
            sep="",
        )

    print("Status oczekiwany z danych:", expected_status.value)

    check(
        "Gemini podporządkowało status bieżącym danym",
        interpretation.hypothesis_status == expected_status,
        failures,
    )
    check(
        "Sprzeczna pamięć nie przegłosowała bieżących dowodów",
        interpretation.hypothesis_status
        != (
            HypothesisStatus.CONFIRMED
            if expected_status is HypothesisStatus.REJECTED
            else HypothesisStatus.REJECTED
        ),
        failures,
    )
    check(
        "Pewność mieści się w zakresie 0-1",
        0.0 <= interpretation.confidence <= 1.0,
        failures,
    )

    print()
    print("=" * 90)

    if failures:
        print("WERDYKT: PRODUKCYJNY ŁAŃCUCH NIE PRZESZEDŁ WSZYSTKICH KONTROLI")
        print("=" * 90)
        for item in failures:
            print("-", item)
        raise SystemExit(1)

    print("WERDYKT: PRODUKCYJNY ŁAŃCUCH PAMIĘCI I FALLBACKU DZIAŁA")
    print("=" * 90)
    print()
    print(
        "FENIKS użył prawdziwego API Gemini, zachował informację o faktycznie "
        "użytym modelu i podporządkował interpretację bieżącym dowodom, "
        "a nie sprzecznemu kontekstowi wcześniejszej wiedzy."
    )


if __name__ == "__main__":
    main()
