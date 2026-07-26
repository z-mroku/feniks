from core.feniks import Feniks
from core.system_knowledge import SystemEvidenceType


def check(
    name: str,
    condition: bool,
    failures: list[str],
) -> None:
    status = "TAK" if condition else "NIE"
    print(f"{name}: {status}")

    if not condition:
        failures.append(name)


def main() -> None:
    failures: list[str] = []

    print("=" * 86)
    print("TEST INTEGRACJI GŁÓWNEGO RDZENIA FENIKSA")
    print("=" * 86)

    # ==================================================
    # ETAP 1 - UTWORZENIE FENIKSA
    # ==================================================

    print()
    print("ETAP 1 - URUCHOMIENIE GŁÓWNEGO RDZENIA")
    print("-" * 86)

    feniks = Feniks()

    check(
        "Feniks został utworzony",
        feniks is not None,
        failures,
    )

    check(
        "Identity jest dostępne",
        feniks.identity is not None,
        failures,
    )

    check(
        "Constitution jest dostępna",
        feniks.constitution is not None,
        failures,
    )

    check(
        "Guardian jest dostępny",
        feniks.guardian is not None,
        failures,
    )

    check(
        "Memory jest dostępna",
        feniks.memory is not None,
        failures,
    )

    check(
        "PersistentMemory jest dostępna",
        feniks.persistent_memory is not None,
        failures,
    )

    check(
        "TruthEngine jest dostępny",
        feniks.truth_engine is not None,
        failures,
    )

    check(
        "DevelopmentLog jest dostępny",
        feniks.development_log is not None,
        failures,
    )

    check(
        "SelfAnalysis jest dostępna",
        feniks.self_analysis is not None,
        failures,
    )

    # ==================================================
    # ETAP 2 - NOWY RDZEŃ POZNAWCZY
    # ==================================================

    print()
    print("ETAP 2 - POZNAWCZY RDZEŃ DIAGNOSTYCZNY")
    print("-" * 86)

    check(
        "SystemKnowledge jest częścią Feniksa",
        feniks.system_knowledge is not None,
        failures,
    )

    check(
        "ExperimentRunner jest częścią Feniksa",
        feniks.experiment_runner is not None,
        failures,
    )

    check(
        "ReasoningValidator jest częścią Feniksa",
        feniks.reasoning_validator is not None,
        failures,
    )

    check(
        "Validator korzysta z SystemKnowledge Feniksa",
        (
            feniks.reasoning_validator.system_knowledge
            is feniks.system_knowledge
        ),
        failures,
    )

    # ==================================================
    # ETAP 3 - SAMOWIEDZA PRZEZ GŁÓWNY RDZEŃ
    # ==================================================

    print()
    print("ETAP 3 - SAMOWIEDZA URUCHAMIANA PRZEZ FENIKSA")
    print("-" * 86)

    facts = feniks.inspect_system_knowledge()

    print(f"Liczba faktów systemowych: {len(facts)}")

    check(
        "Feniks uzyskał fakty systemowe",
        len(facts) > 0,
        failures,
    )

    execution_facts = feniks.system_execution_facts()
    code_facts = feniks.system_code_facts()

    check(
        "Feniks posiada fakty z wykonania kodu",
        len(execution_facts) > 0,
        failures,
    )

    check(
        "Feniks posiada fakty z inspekcji kodu",
        len(code_facts) > 0,
        failures,
    )

    code_inspection_present = any(
        fact.evidence_type
        == SystemEvidenceType.CODE_INSPECTION
        for fact in feniks.system_facts()
    )

    check(
        "Feniks rozróżnia inspekcję kodu",
        code_inspection_present,
        failures,
    )

    # ==================================================
    # ETAP 4 - EKSPERYMENT PRZEZ GŁÓWNY RDZEŃ
    # ==================================================

    print()
    print("ETAP 4 - EKSPERYMENT URUCHAMIANY PRZEZ FENIKSA")
    print("-" * 86)

    result = feniks.run_quantity_vs_quality_experiment(
        strong_support_reliability=0.95,
        opposing_reliability=0.50,
        max_opposing=4,
    )

    check(
        "Eksperyment utworzył 5 obserwacji",
        len(result.observations) == 5,
        failures,
    )

    check(
        "Sprzeczność pojawiła się przy N=1",
        result.first_contradiction_at == 1,
        failures,
    )

    check(
        "Sprzeciw nie przewyższył poparcia",
        result.first_opposition_stronger_at is None,
        failures,
    )

    check(
        "Feniks zachował eksperyment w historii sesji",
        len(feniks.experiment_history()) == 1,
        failures,
    )

    # ==================================================
    # ETAP 5 - STARE FUNKCJE
    # ==================================================

    print()
    print("ETAP 5 - KONTROLA ZGODNOŚCI WSTECZNEJ")
    print("-" * 86)

    start_result = feniks.start()

    check(
        "Feniks nadal się uruchamia",
        isinstance(start_result, str)
        and len(start_result) > 0,
        failures,
    )

    check(
        "Pamięć robocza nadal działa",
        feniks.memory.count() >= 1,
        failures,
    )

    check(
        "Tożsamość nadal działa",
        feniks.who_am_i() is not None,
        failures,
    )

    check(
        "Konstytucja nadal działa",
        feniks.read_constitution() is not None,
        failures,
    )

    # ==================================================
    # ETAP 6 - STATUS
    # ==================================================

    print()
    print("ETAP 6 - SAMOOBSERWACJA STANU")
    print("-" * 86)

    status = feniks.status()

    required_status_keys = [
        "samowiedza_systemowa_zaladowana",
        "fakty_systemowe",
        "fakty_z_wykonania_kodu",
        "fakty_z_inspekcji_kodu",
        "runner_eksperymentow_zaladowany",
        "wykonane_eksperymenty",
        "walidator_rozumowania_zaladowany",
    ]

    for key in required_status_keys:
        check(
            f"Status zawiera: {key}",
            key in status,
            failures,
        )

    check(
        "Status widzi wykonany eksperyment",
        status.get("wykonane_eksperymenty") == 1,
        failures,
    )

    check(
        "Status widzi fakty systemowe",
        status.get("fakty_systemowe") == len(facts),
        failures,
    )

    # ==================================================
    # WERDYKT
    # ==================================================

    print()
    print("=" * 86)
    print("WERDYKT")
    print("=" * 86)

    if failures:
        print("TEST GŁÓWNEGO RDZENIA: NIEZALICZONY")
        print()
        print("NIEZALICZONE WARUNKI:")

        for failure in failures:
            print(f"- {failure}")

        raise SystemExit(1)

    print("TEST GŁÓWNEGO RDZENIA: ZALICZONY")
    print()
    print(
        "SystemKnowledge, ExperimentRunner i "
        "ReasoningValidator są częścią głównego Feniksa."
    )
    print()
    print(
        "Dotychczasowe podstawowe funkcje rdzenia "
        "pozostały dostępne."
    )
    print()
    print(
        "Możemy przejść do następnego etapu integracji."
    )


if __name__ == "__main__":
    main()