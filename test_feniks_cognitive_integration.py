from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)
from core.experiment_runner import (
    ExperimentResult,
    ExperimentRunner,
)
from core.reasoning_validator import (
    ReasoningValidator,
    ValidationLevel,
)
from core.system_knowledge import (
    SystemEvidenceType,
    SystemKnowledge,
)


def print_header(title: str) -> None:
    print()
    print("=" * 86)
    print(title)
    print("=" * 86)


def check(
    name: str,
    condition: bool,
    failures: list[str],
) -> None:
    status = "TAK" if condition else "NIE"
    print(f"{name}: {status}")

    if not condition:
        failures.append(name)


def build_test_interpretation() -> ExperimentInterpretation:
    """
    Kontrolowana interpretacja zawierająca celowo:

    - poprawną obserwację,
    - poprawne ustalenie o saturacji,
    - fałszywą niewiadomą dotyczącą progu,
    - fałszywą niewiadomą dotyczącą confidence,
    - błędną hipotezę o progu,
    - błędną hipotezę o ukrytej regule.

    Dzięki temu sprawdzamy, czy ReasoningValidator
    rzeczywiście wykorzystuje samowiedzę FENIKSA.
    """

    return ExperimentInterpretation(
        hypothesis_status=HypothesisStatus.REJECTED,
        reasoning=(
            "W badanym zakresie sprzeciw nie przewyższył "
            "poparcia, dlatego pierwotna hipoteza została "
            "odrzucona."
        ),
        new_findings=[
            "Sprzeczność pojawiła się już przy N=1.",
            "Siła sprzeciwu wykazuje saturację od N=3.",
        ],
        remaining_unknowns=[
            (
                "Nie wiadomo, jaki minimalny próg sprzeciwu "
                "jest wymagany do wykrycia SPRZECZNOŚCI."
            ),
            (
                "Nie wiadomo, dlaczego wskaźnik pewności "
                "zachowuje się w ten sposób."
            ),
        ],
        alternative_explanations=[
            (
                "Klasyfikacja SPRZECZNOŚĆ może być "
                "wyzwalana przez próg siły sprzeciwu."
            ),
            (
                "Mechanizm agregacji może posiadać "
                "dodatkową niewidoczną regułę."
            ),
        ],
        next_experiment_question=(
            "Jak zachowuje się TruthEngine "
            "w kolejnych kontrolowanych warunkach?"
        ),
        next_experiment=(
            "Przeprowadzić kolejny deterministyczny "
            "eksperyment diagnostyczny."
        ),
        cannot_conclude_yet=[
            (
                "Nie należy wyprowadzać wniosków "
                "poza zakres wykonanych testów."
            ),
        ],
        confidence=0.95,
    )


def main() -> None:
    failures: list[str] = []

    print_header(
        "TEST INTEGRACJI POZNAWCZEGO RDZENIA FENIKSA"
    )

    # ==================================================
    # ETAP 1
    # SYSTEM KNOWLEDGE
    # ==================================================

    print()
    print("ETAP 1 - SAMOWIEDZA SYSTEMU")
    print("-" * 86)

    knowledge = SystemKnowledge()
    facts = knowledge.inspect_truth_engine()

    execution_facts = knowledge.execution_facts()
    code_facts = knowledge.code_inspection_facts()

    print(f"Liczba wszystkich faktów: {len(facts)}")
    print(
        "Fakty z wykonania kodu: "
        f"{len(execution_facts)}"
    )
    print(
        "Fakty z inspekcji kodu: "
        f"{len(code_facts)}"
    )

    check(
        "SystemKnowledge utworzył fakty",
        len(facts) > 0,
        failures,
    )

    check(
        "Istnieją fakty z wykonania kodu",
        len(execution_facts) > 0,
        failures,
    )

    check(
        "Istnieją fakty z inspekcji kodu",
        len(code_facts) > 0,
        failures,
    )

    contradiction_rule = knowledge.get(
        "truth.contradiction_rule"
    )

    check(
        "FENIKS zna regułę SPRZECZNOŚCI",
        contradiction_rule is not None,
        failures,
    )

    if contradiction_rule is not None:
        check(
            "Reguła SPRZECZNOŚCI nie używa progu siły",
            (
                contradiction_rule.value.get(
                    "uses_strength_threshold"
                )
                is False
            ),
            failures,
        )

    zero_reliability = knowledge.get(
        "truth.zero_reliability_evidence"
    )

    check(
        "FENIKS zna zachowanie dowodu o reliability=0.0",
        zero_reliability is not None,
        failures,
    )

    if zero_reliability is not None:
        check(
            "Dowód przeciwny 0.0 wywołuje SPRZECZNOŚĆ",
            (
                zero_reliability.value.get(
                    "contradiction_detected"
                )
                is True
            ),
            failures,
        )

    # ==================================================
    # ETAP 2
    # EXPERIMENT RUNNER
    # ==================================================

    print()
    print("ETAP 2 - RZECZYWISTY EKSPERYMENT")
    print("-" * 86)

    runner = ExperimentRunner()

    result: ExperimentResult = (
        runner.run_quantity_vs_quality(
            strong_support_reliability=0.95,
            opposing_reliability=0.50,
            max_opposing=4,
        )
    )

    print(
        "Liczba obserwacji: "
        f"{len(result.observations)}"
    )

    print(
        "Pierwsza sprzeczność: "
        f"{result.first_contradiction_at}"
    )

    print(
        "Pierwsza przewaga sprzeciwu: "
        f"{result.first_opposition_stronger_at}"
    )

    check(
        "ExperimentRunner utworzył 5 obserwacji",
        len(result.observations) == 5,
        failures,
    )

    check(
        "Pierwsza SPRZECZNOŚĆ wystąpiła przy N=1",
        result.first_contradiction_at == 1,
        failures,
    )

    check(
        "Sprzeciw nie przewyższył poparcia",
        result.first_opposition_stronger_at is None,
        failures,
    )

    # ==================================================
    # ETAP 3
    # KONTROLOWANA INTERPRETACJA
    # ==================================================

    print()
    print("ETAP 3 - INTERPRETACJA KANDYDUJĄCA")
    print("-" * 86)

    interpretation = build_test_interpretation()

    print(
        "Status hipotezy: "
        f"{interpretation.hypothesis_status.value}"
    )

    print(
        "Liczba nowych ustaleń: "
        f"{len(interpretation.new_findings)}"
    )

    print(
        "Liczba deklarowanych niewiadomych: "
        f"{len(interpretation.remaining_unknowns)}"
    )

    print(
        "Liczba alternatywnych wyjaśnień: "
        f"{len(interpretation.alternative_explanations)}"
    )

    # ==================================================
    # ETAP 4
    # REASONING VALIDATOR
    # ==================================================

    print()
    print("ETAP 4 - WALIDACJA INTERPRETACJI")
    print("-" * 86)

    validator = ReasoningValidator(
        system_knowledge=knowledge
    )

    report = (
        validator.validate_experiment_interpretation(
            interpretation=interpretation,
            result=result,
        )
    )

    print(
        "Liczba twardych faktów: "
        f"{len(report.hard_facts)}"
    )

    print(
        "Liczba ocenionych twierdzeń: "
        f"{len(report.issues)}"
    )

    print(
        "Fałszywe niewiadome: "
        f"{len(report.false_unknowns)}"
    )

    print(
        "Sprzeczności z wiedzą: "
        f"{len(report.conflicts)}"
    )

    print(
        "Nieweryfikowalne: "
        f"{len(report.unverifiable)}"
    )

    print(
        "Bezpieczne do pamięci: "
        f"{report.safe_for_memory}"
    )

    # ==================================================
    # ETAP 5
    # SPRAWDZENIE POŁĄCZEŃ
    # ==================================================

    print()
    print("ETAP 5 - KONTROLA POŁĄCZEŃ RDZENIA")
    print("-" * 86)

    contradiction_observation = any(
        issue.level == ValidationLevel.OBSERVATION
        and issue.related_fact
        == "first_contradiction_at"
        for issue in report.issues
    )

    saturation_supported = any(
        issue.level == ValidationLevel.SUPPORTED
        and issue.related_fact
        == "truth.quantity_saturation"
        for issue in report.issues
    )

    threshold_false_unknown = any(
        issue.level == ValidationLevel.FALSE_UNKNOWN
        and issue.related_fact
        == "truth.contradiction_rule"
        for issue in report.issues
    )

    confidence_false_unknown = any(
        issue.level == ValidationLevel.FALSE_UNKNOWN
        and issue.related_fact
        == "truth.contradiction_confidence_rule"
        for issue in report.issues
    )

    threshold_conflict = any(
        issue.level == ValidationLevel.CONFLICT
        and issue.related_fact
        == "truth.contradiction_rule"
        for issue in report.issues
    )

    hidden_rule_conflict = any(
        issue.level == ValidationLevel.CONFLICT
        and issue.related_fact
        == "truth.quantity_component"
        for issue in report.issues
    )

    check(
        (
            "Validator wykorzystał obserwację "
            "ExperimentRunner"
        ),
        contradiction_observation,
        failures,
    )

    check(
        (
            "Validator wykorzystał wykonaniową "
            "samowiedzę o saturacji"
        ),
        saturation_supported,
        failures,
    )

    check(
        (
            "Validator wykorzystał wiedzę z kodu "
            "o regule SPRZECZNOŚCI"
        ),
        threshold_false_unknown,
        failures,
    )

    check(
        (
            "Validator wykorzystał wiedzę z kodu "
            "o mechanizmie confidence"
        ),
        confidence_false_unknown,
        failures,
    )

    check(
        "Błędna hipoteza o progu została odrzucona",
        threshold_conflict,
        failures,
    )

    check(
        (
            "Hipoteza o niewidocznej regule "
            "została skonfrontowana z samowiedzą"
        ),
        hidden_rule_conflict,
        failures,
    )

    check(
        "Interpretacja nie została wpuszczona do pamięci",
        report.safe_for_memory is False,
        failures,
    )

    # ==================================================
    # ETAP 6
    # HIERARCHIA ŹRÓDEŁ
    # ==================================================

    print()
    print("ETAP 6 - HIERARCHIA WIEDZY")
    print("-" * 86)

    origins = {
        fact.origin
        for fact in report.hard_facts
    }

    check(
        "Raport zawiera fakty eksperymentalne",
        "EKSPERYMENT" in origins,
        failures,
    )

    check(
        "Raport zawiera fakty z wykonania kodu",
        "WYKONANIE_KODU" in origins,
        failures,
    )

    check(
        "Raport zawiera fakty z inspekcji kodu",
        "INSPEKCJA_KODU" in origins,
        failures,
    )

    code_inspection_present = any(
        fact.evidence_type
        == SystemEvidenceType.CODE_INSPECTION
        for fact in knowledge.all_facts()
    )

    check(
        "SystemKnowledge rozróżnia inspekcję od wykonania",
        code_inspection_present,
        failures,
    )

    # ==================================================
    # WERDYKT
    # ==================================================

    print_header("WERDYKT INTEGRACJI")

    if failures:
        print("TEST INTEGRACYJNY: NIEZALICZONY")
        print()
        print("NIEZALICZONE WARUNKI:")

        for failure in failures:
            print(f"- {failure}")

        print()
        print(
            "Nie integrujemy jeszcze tych modułów "
            "z głównym Feniksem."
        )

        raise SystemExit(1)

    print("TEST INTEGRACYJNY: ZALICZONY")
    print()
    print(
        "ŁAŃCUCH POZNAWCZY DZIAŁA:"
    )
    print()
    print(
        "SystemKnowledge"
        " -> ExperimentRunner"
        " -> ReasoningValidator"
        " -> zweryfikowany raport"
    )
    print()
    print(
        "FENIKS potrafi odróżnić:"
    )
    print(
        "- obserwację eksperymentalną,"
    )
    print(
        "- fakt uzyskany przez wykonanie kodu,"
    )
    print(
        "- fakt wynikający z inspekcji kodu,"
    )
    print(
        "- interpretację wymagającą walidacji."
    )
    print()
    print(
        "Możemy przejść do integracji "
        "z główną klasą Feniks."
    )


if __name__ == "__main__":
    main()