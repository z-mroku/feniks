import sys
from pathlib import Path


# ============================================================
# ŚCIEŻKA PROJEKTU
# ============================================================

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ============================================================
# IMPORTY FENIKSA
# ============================================================

from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)
from core.experiment_runner import ExperimentRunner
from core.reasoning_validator import (
    ReasoningValidator,
    ValidationLevel,
)


# ============================================================
# TEST WALIDATORA SAMOWIEDZY
# ============================================================

def main():
    print("=" * 78)
    print("TEST WALIDATORA SAMOWIEDZY FENIKSA")
    print("=" * 78)

    # ========================================================
    # 1. RZECZYWISTY EKSPERYMENT
    # ========================================================

    runner = ExperimentRunner()

    result = runner.run_quantity_vs_quality(
        strong_support_reliability=0.95,
        opposing_reliability=0.50,
        max_opposing=20,
    )

    print()
    print("EKSPERYMENT WYKONANY")
    print("-" * 78)

    print(
        "PIERWSZA SPRZECZNOŚĆ:",
        (
            result.first_contradiction_at
            if result.first_contradiction_at is not None
            else "NIE WYSTĄPIŁA"
        ),
    )

    print(
        "PIERWSZA PRZEWAGA SPRZECIWU:",
        (
            result.first_opposition_stronger_at
            if result.first_opposition_stronger_at is not None
            else "NIE WYSTĄPIŁA"
        ),
    )

    # ========================================================
    # 2. KONTROLOWANA INTERPRETACJA
    # ========================================================
    #
    # To NIE jest odpowiedź Gemini.
    #
    # Celowo tworzymy interpretację zawierającą:
    #
    # - prawdziwe ustalenie eksperymentalne,
    # - prawdziwe ustalenie o saturacji,
    # - fałszywą niewiadomą,
    # - rzeczywistą niewiadomą,
    # - hipotezy wymagające dalszych testów.
    #
    # Dzięki temu badamy sam ReasoningValidator.
    # ========================================================

    interpretation = ExperimentInterpretation(
        hypothesis_status=HypothesisStatus.REJECTED,

        reasoning=(
            "Hipoteza o przewadze skumulowanej siły "
            "wielu przeciętnych dowodów przeciwnych "
            "została obalona, ponieważ w wykonanym "
            "eksperymencie siła sprzeciwu ani razu "
            "nie przewyższyła siły poparcia."
        ),

        new_findings=[
            (
                "Sprzeczność pojawiła się już przy N=1."
            ),
            (
                "Siła sprzeciwu wykazuje saturację "
                "od N=3."
            ),
        ],

        remaining_unknowns=[
            (
                "Nie wiadomo, jaki minimalny próg "
                "sprzeciwu jest wymagany do wykrycia "
                "SPRZECZNOŚCI."
            ),
            (
                "Nie wiadomo, dlaczego wskaźnik "
                "pewności zachowuje się w ten sposób."
            ),
        ],

        alternative_explanations=[
            (
                "Klasyfikacja SPRZECZNOŚĆ może być "
                "wyzwalana przez próg siły sprzeciwu."
            ),
            (
                "Mechanizm agregacji może posiadać "
                "dodatkową regułę niewidoczną "
                "w samych obserwacjach eksperymentu."
            ),
        ],

        next_experiment_question=(
            "Co dokładnie decyduje o wykryciu "
            "sprzeczności przez TruthEngine?"
        ),

        next_experiment=(
            "Przeprowadzić serię kontrolowanych prób "
            "ze stałym dowodem wspierającym oraz "
            "pojedynczym dowodem przeciwnym o stopniowo "
            "zmienianej wiarygodności i dla każdej próby "
            "zapisać klasyfikację, siłę poparcia, "
            "siłę sprzeciwu oraz flagę sprzeczności."
        ),

        cannot_conclude_yet=[
            (
                "Nie można jeszcze ustalić pełnej "
                "reguły matematycznej odpowiedzialnej "
                "za zachowanie TruthEngine."
            )
        ],

        confidence=0.90,
    )

    # ========================================================
    # 3. WALIDACJA
    # ========================================================

    validator = ReasoningValidator()

    report = validator.validate_experiment_interpretation(
        interpretation=interpretation,
        result=result,
    )

    # ========================================================
    # 4. TWARDE FAKTY
    # ========================================================

    print()
    print("=" * 78)
    print("TWARDE FAKTY DOSTĘPNE WALIDATOROWI")
    print("=" * 78)

    for number, fact in enumerate(
        report.hard_facts,
        start=1,
    ):
        print()
        print("-" * 78)
        print(f"FAKT {number}")
        print("-" * 78)

        print("NAZWA:", fact.name)
        print("WARTOŚĆ:", fact.value)
        print("ŹRÓDŁO:", fact.source)
        print("OPIS:", fact.description)

    # ========================================================
    # 5. OCENA TWIERDZEŃ
    # ========================================================

    print()
    print("=" * 78)
    print("OCENA TWIERDZEŃ")
    print("=" * 78)

    for number, issue in enumerate(
        report.issues,
        start=1,
    ):
        print()
        print("-" * 78)
        print(f"TWIERDZENIE {number}")
        print("-" * 78)

        print(
            "ŹRÓDŁO TWIERDZENIA:",
            issue.source,
        )

        print(
            "POZIOM:",
            issue.level.value,
        )

        print()
        print("TREŚĆ:")
        print(issue.statement)

        print()
        print("UZASADNIENIE:")
        print(issue.reason)

        if issue.related_fact is not None:
            print()
            print(
                "POWIĄZANY FAKT:",
                issue.related_fact,
            )

    # ========================================================
    # 6. AUTOMATYCZNA KONTROLA WYNIKU
    # ========================================================

    false_unknowns = report.false_unknowns
    conflicts = report.conflicts
    hypotheses = report.hypotheses
    unverifiable = report.unverifiable

    system_fact_available = any(
        fact.name
        == "truth.any_two_sided_evidence_test"
        for fact in report.hard_facts
    )

    saturation_fact_available = any(
        fact.name
        == "truth.quantity_saturation"
        for fact in report.hard_facts
    )

    contradiction_observation_detected = any(
        issue.source == "new_findings"
        and issue.level == ValidationLevel.OBSERVATION
        and issue.related_fact == "first_contradiction_at"
        for issue in report.issues
    )

    saturation_supported = any(
        issue.source == "new_findings"
        and issue.level == ValidationLevel.SUPPORTED
        and issue.related_fact == "truth.quantity_saturation"
        for issue in report.issues
    )

    detected_false_unknown = any(
        issue.level == ValidationLevel.FALSE_UNKNOWN
        for issue in report.issues
    )

    # ========================================================
    # 7. RAPORT KONTROLNY
    # ========================================================

    print()
    print("=" * 78)
    print("KONTROLA KLUCZOWA")
    print("=" * 78)
    print()

    print(
        "SAMOWIEDZA O SŁABYM DOWODZIE "
        "PRZECIWNYM DOSTĘPNA:",
        "TAK" if system_fact_available else "NIE",
    )

    print(
        "SAMOWIEDZA O SATURACJI DOSTĘPNA:",
        "TAK" if saturation_fact_available else "NIE",
    )

    print(
        "OBSERWACJA SPRZECZNOŚCI PRZY N=1 "
        "ROZPOZNANA:",
        (
            "TAK"
            if contradiction_observation_detected
            else "NIE"
        ),
    )

    print(
        "SATURACJA ROZPOZNANA JAKO "
        "WSPARTA WIEDZĄ:",
        "TAK" if saturation_supported else "NIE",
    )

    print(
        "WYKRYTO FAŁSZYWĄ NIEWIADOMĄ:",
        "TAK" if detected_false_unknown else "NIE",
    )

    print(
        "LICZBA FAŁSZYWYCH NIEWIADOMYCH:",
        len(false_unknowns),
    )

    print(
        "LICZBA SPRZECZNOŚCI Z WIEDZĄ:",
        len(conflicts),
    )

    print(
        "LICZBA HIPOTEZ:",
        len(hypotheses),
    )

    print(
        "LICZBA TWIERDZEŃ NIEWERYFIKOWALNYCH:",
        len(unverifiable),
    )

    print(
        "STATUS HIPOTEZY ZGODNY Z DANYMI:",
        (
            "TAK"
            if report.hypothesis_status_consistent
            else "NIE"
        ),
    )

    print(
        "BEZPIECZNE DO PAMIĘCI:",
        "TAK" if report.safe_for_memory else "NIE",
    )

    # ========================================================
    # 8. WARUNKI ZALICZENIA TESTU
    # ========================================================

    conditions = {
        (
            "SystemKnowledge dostarczył test "
            "dwustronnych dowodów"
        ): system_fact_available,

        (
            "SystemKnowledge dostarczył wiedzę "
            "o saturacji"
        ): saturation_fact_available,

        (
            "Walidator rozpoznał obserwację N=1"
        ): contradiction_observation_detected,

        (
            "Walidator rozpoznał potwierdzoną saturację"
        ): saturation_supported,

        (
            "Walidator wykrył fałszywą niewiadomą"
        ): detected_false_unknown,

        (
            "Interpretacja nie została dopuszczona "
            "bezwarunkowo do pamięci"
        ): not report.safe_for_memory,
    }

    print()
    print("=" * 78)
    print("WARUNKI ZALICZENIA")
    print("=" * 78)

    for description, passed in conditions.items():
        print(
            f"- {description}: "
            f"{'TAK' if passed else 'NIE'}"
        )

    test_passed = all(
        conditions.values()
    )

    # ========================================================
    # 9. WERDYKT
    # ========================================================

    print()
    print("=" * 78)

    if test_passed:
        print(
            "WERDYKT: FENIKS ODRÓŻNIŁ NIEWIEDZĘ "
            "MODELU OD WŁASNEJ ZWERYFIKOWANEJ WIEDZY"
        )
    else:
        print(
            "WERDYKT: WALIDATOR NIE PRZESZEDŁ "
            "PEŁNEJ KONTROLI"
        )

    print("=" * 78)


if __name__ == "__main__":
    main()