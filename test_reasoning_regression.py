from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)
from core.experiment_runner import ExperimentRunner
from core.reasoning_validator import (
    ReasoningValidator,
    ValidationLevel,
)
from core.system_knowledge import SystemKnowledge


def main():
    print("=" * 78)
    print("TEST REGRESYJNY SAMOWIEDZY FENIKSA")
    print("=" * 78)

    knowledge = SystemKnowledge()
    knowledge.inspect_truth_engine()

    runner = ExperimentRunner()

    result = runner.run_quantity_vs_quality(
        strong_support_reliability=0.95,
        opposing_reliability=0.50,
        max_opposing=4,
    )

    interpretation = ExperimentInterpretation(
        hypothesis_status=HypothesisStatus.REJECTED,
        reasoning=(
            "Sprzeciw nie przewyzszyl poparcia, "
            "wiec pierwotna hipoteza zostala obalona."
        ),
        new_findings=[
            "Sprzecznosc pojawila sie juz przy N=1.",
            "Sila sprzeciwu wykazuje saturacje od N=3.",
        ],
        remaining_unknowns=[
            (
                "Nie wiadomo, jaki minimalny prog sprzeciwu "
                "jest wymagany do wykrycia SPRZECZNOSCI."
            ),
            (
                "Nie wiadomo, dlaczego wskaznik pewnosci "
                "zachowuje sie w ten sposob."
            ),
        ],
        alternative_explanations=[
            (
                "Klasyfikacja SPRZECZNOSC moze byc "
                "wyzwalana przez prog sily sprzeciwu."
            ),
            (
                "Mechanizm agregacji moze posiadac "
                "dodatkowa regule niewidoczna w samych "
                "obserwacjach eksperymentu."
            ),
        ],
        next_experiment_question=(
            "Jak zachowuje sie TruthEngine w kolejnych "
            "kontrolowanych warunkach?"
        ),
        next_experiment=(
            "Przeprowadzic kolejny deterministyczny "
            "eksperyment diagnostyczny."
        ),
        cannot_conclude_yet=[
            (
                "Nie nalezy wyprowadzac wnioskow poza "
                "zakres wykonanych testow."
            ),
        ],
        confidence=0.95,
    )

    validator = ReasoningValidator(
        system_knowledge=knowledge
    )

    report = validator.validate_experiment_interpretation(
        interpretation=interpretation,
        result=result,
    )

    false_unknowns = report.false_unknowns
    conflicts = report.conflicts
    unverifiable = report.unverifiable

    confidence_false_unknown = any(
        issue.level == ValidationLevel.FALSE_UNKNOWN
        and issue.related_fact
        == "truth.contradiction_confidence_rule"
        for issue in report.issues
    )

    threshold_false_unknown = any(
        issue.level == ValidationLevel.FALSE_UNKNOWN
        and issue.related_fact
        == "truth.contradiction_rule"
        for issue in report.issues
    )

    saturation_supported = any(
        issue.related_fact == "truth.quantity_saturation"
        and issue.level == ValidationLevel.SUPPORTED
        for issue in report.issues
    )

    contradiction_observed = any(
        issue.related_fact == "first_contradiction_at"
        and issue.level == ValidationLevel.OBSERVATION
        for issue in report.issues
    )

    checks = [
        (
            "Wykryto falszywa niewiadoma o confidence",
            confidence_false_unknown,
        ),
        (
            "Wykryto falszywa niewiadoma o progu",
            threshold_false_unknown,
        ),
        (
            "Saturacja pozostala wsparta wiedza",
            saturation_supported,
        ),
        (
            "Sprzecznosc przy N=1 pozostala obserwacja",
            contradiction_observed,
        ),
        (
            "Sa dokladnie 2 falszywe niewiadome",
            len(false_unknowns) == 2,
        ),
        (
            "Sa dokladnie 2 sprzecznosci z wiedza",
            len(conflicts) == 2,
        ),
        (
            "Nie ma twierdzen nieweryfikowalnych",
            len(unverifiable) == 0,
        ),
        (
            "Interpretacja nie jest bezpieczna do pamieci",
            report.safe_for_memory is False,
        ),
    ]

    print()
    print("KONTROLA REGRESJI")
    print("-" * 78)

    failed = []

    for name, passed in checks:
        status = "TAK" if passed else "NIE"
        print(f"{name}: {status}")

        if not passed:
            failed.append(name)

    print()
    print("=" * 78)

    if failed:
        print("WERDYKT: TEST REGRESYJNY NIEZALICZONY")
        print("=" * 78)

        print()
        print("NIEZALICZONE WARUNKI:")

        for name in failed:
            print(f"- {name}")

        raise SystemExit(1)

    print(
        "WERDYKT: KLUCZOWA SAMOWIEDZA FENIKSA "
        "JEST CHRONIONA TESTEM REGRESYJNYM"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()