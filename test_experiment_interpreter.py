import sys

sys.path.insert(0, "src")

from core.experiment_runner import ExperimentRunner
from core.experiment_interpreter import (
    GeminiExperimentInterpreter,
    HypothesisStatus,
)


print("=" * 78)
print("TEST INTERPRETACJI RZECZYWISTEGO EKSPERYMENTU FENIKSA")
print("=" * 78)


# ============================================================
# 1. HIPOTEZA POSTAWIONA PRZED EKSPERYMENTEM
# ============================================================

hypothesis = (
    "W obecnym Silniku Prawdy skumulowana siła wielu "
    "przeciętnych dowodów o przeciwnym zwrocie przewyższa "
    "pojedynczy dowód o wysokiej jakości, co prowadzi "
    "do zmiany końcowej klasyfikacji."
)

print("\nHIPOTEZA PIERWOTNA:")
print(hypothesis)


# ============================================================
# 2. RZECZYWISTY EKSPERYMENT
# ============================================================

print("\n" + "=" * 78)
print("WYKONYWANIE EKSPERYMENTU")
print("=" * 78)

runner = ExperimentRunner()

result = runner.run_quantity_vs_quality(
    strong_support_reliability=0.95,
    opposing_reliability=0.50,
    max_opposing=20,
)

print("\nEKSPERYMENT ZAKOŃCZONY.")

print(
    "PIERWSZA SPRZECZNOŚĆ:",
    result.first_contradiction_at,
)

print(
    "PIERWSZA PRZEWAGA SPRZECIWU:",
    (
        result.first_opposition_stronger_at
        if result.first_opposition_stronger_at is not None
        else "NIE WYSTĄPIŁA"
    ),
)


# ============================================================
# 3. TWARDE USTALENIA PROGRAMU
# ============================================================

baseline = result.observations[0]
n1 = result.observations[1]
last = result.observations[-1]

contradiction_at_one = (
    result.first_contradiction_at == 1
)

opposition_never_stronger = (
    result.first_opposition_stronger_at is None
)

classification_changed_at_one = (
    baseline.classification
    != n1.classification
)

support_still_stronger_at_end = (
    last.support_strength
    >
    last.opposition_strength
)

opposition_saturated = all(
    observation.opposition_strength
    == result.observations[3].opposition_strength
    for observation in result.observations[3:]
)


print("\n" + "=" * 78)
print("TWARDE USTALENIA PROGRAMU")
print("=" * 78)

print(
    "\nSPRZECZNOŚĆ POJAWIŁA SIĘ PRZY N=1:",
    "TAK" if contradiction_at_one else "NIE",
)

print(
    "SIŁA SPRZECIWU NIGDY NIE PRZEWYŻSZYŁA POPARCIA:",
    "TAK" if opposition_never_stronger else "NIE",
)

print(
    "KLASYFIKACJA ZMIENIŁA SIĘ PRZY N=1:",
    "TAK" if classification_changed_at_one else "NIE",
)

print(
    "PRZY N=20 POPARCIE NADAL SILNIEJSZE OD SPRZECIWU:",
    "TAK" if support_still_stronger_at_end else "NIE",
)

print(
    "SIŁA SPRZECIWU PRZESTAŁA ROSNĄĆ OD N=3:",
    "TAK" if opposition_saturated else "NIE",
)


# ============================================================
# 4. INTERPRETACJA GEMINI
# ============================================================

print("\n" + "=" * 78)
print("INTERPRETACJA ZEWNĘTRZNEJ WARSTWY ROZUMOWANIA")
print("=" * 78)

interpreter = GeminiExperimentInterpreter()

interpretation = interpreter.interpret(
    hypothesis=hypothesis,
    result=result,
)


print("\nSTATUS HIPOTEZY:")
print(
    interpretation.hypothesis_status.value
)

print("\nUZASADNIENIE:")
print(
    interpretation.reasoning
)


print("\nNOWE USTALENIA:")

for item in interpretation.new_findings:
    print(f"- {item}")


print("\nPOZOSTAŁE NIEWIADOME:")

for item in interpretation.remaining_unknowns:
    print(f"- {item}")


print("\nALTERNATYWNE WYJAŚNIENIA:")

if interpretation.alternative_explanations:
    for item in interpretation.alternative_explanations:
        print(f"- {item}")
else:
    print("- BRAK")


print("\nNASTĘPNE PYTANIE EKSPERYMENTALNE:")
print(
    interpretation.next_experiment_question
)


print("\nPROPONOWANY NASTĘPNY EKSPERYMENT:")
print(
    interpretation.next_experiment
)


print("\nCZEGO NADAL NIE WOLNO UZNAĆ ZA USTALONE:")

for item in interpretation.cannot_conclude_yet:
    print(f"- {item}")


print(
    "\nPEWNOŚĆ INTERPRETACJI:",
    f"{interpretation.confidence * 100:.1f}%",
)


# ============================================================
# 5. KONTROLA ZGODNOŚCI INTERPRETACJI Z DANYMI
# ============================================================

print("\n" + "=" * 78)
print("KONTROLA ZGODNOŚCI INTERPRETACJI Z DANYMI")
print("=" * 78)


# Pierwotna hipoteza mówiła, że sprzeciw
# PRZEWYŻSZY mocny dowód.
#
# Eksperyment tego nie wykazał.
#
# Dlatego interpretacja nie powinna uznać
# pierwotnej hipotezy za potwierdzoną.

incorrect_confirmation = (
    opposition_never_stronger
    and interpretation.hypothesis_status
    == HypothesisStatus.CONFIRMED
)


# Sprawdzamy, czy Gemini nie przemyciło
# propozycji naprawy na etapie interpretacji.

interpretation_text = " ".join(
    [
        interpretation.reasoning,
        *interpretation.new_findings,
        *interpretation.remaining_unknowns,
        *interpretation.alternative_explanations,
        interpretation.next_experiment_question,
        interpretation.next_experiment,
        *interpretation.cannot_conclude_yet,
    ]
).casefold()


repair_terms = [
    "należy wdrożyć",
    "należy zmienić algorytm",
    "trzeba zmienić algorytm",
    "zaimplementować poprawkę",
    "wdrożyć próg",
    "zastosować tłumienie",
    "zmodyfikować algorytm",
]


repair_detected = any(
    term in interpretation_text
    for term in repair_terms
)


print(
    "\nMODEL UZNAŁ HIPOTEZĘ ZA POTWIERDZONĄ "
    "MIMO BRAKU PRZEWAGI SPRZECIWU:",
    "TAK" if incorrect_confirmation else "NIE",
)

print(
    "MODEL PRZESKOCZYŁ DO NAPRAWY ALGORYTMU:",
    "TAK" if repair_detected else "NIE",
)


# ============================================================
# 6. KOŃCOWY WERDYKT TESTU
# ============================================================

logic_ok = (
    not incorrect_confirmation
    and not repair_detected
)


print("\n" + "=" * 78)

if logic_ok:
    print(
        "WERDYKT: INTERPRETACJA PRZESZŁA "
        "PODSTAWOWĄ KONTROLĘ LOGICZNĄ"
    )
else:
    print(
        "WERDYKT: INTERPRETACJA NIE PRZESZŁA "
        "KONTROLI LOGICZNEJ"
    )

print("=" * 78)