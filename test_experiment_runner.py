import sys

sys.path.insert(0, "src")

from core.experiment_runner import ExperimentRunner


runner = ExperimentRunner()

print("=" * 78)
print("PIERWSZY RZECZYWISTY EKSPERYMENT FENIKSA")
print("=" * 78)

print(
    "\nPYTANIE BADAWCZE:\n"
    "Jak obecny TruthEngine zachowuje się, gdy jeden bardzo "
    "wiarygodny dowód wspierający zostaje skonfrontowany "
    "z rosnącą liczbą przeciętnych dowodów przeciwnych?"
)

print(
    "\nPARAMETRY:\n"
    "- mocny dowód wspierający: 0.95\n"
    "- każdy dowód przeciwny: 0.50\n"
    "- liczba dowodów przeciwnych: N = 0...20"
)

result = runner.run_quantity_vs_quality(
    strong_support_reliability=0.95,
    opposing_reliability=0.50,
    max_opposing=20,
)

print("\n" + "=" * 78)
print("OBSERWACJE")
print("=" * 78)

header = (
    f"{'N':>3} | "
    f"{'KLASYFIKACJA':<16} | "
    f"{'ZA':>7} | "
    f"{'PRZECIW':>7} | "
    f"{'PEWNOŚĆ':>8} | "
    f"{'SPRZECZNOŚĆ':<12}"
)

print(header)
print("-" * len(header))

for observation in result.observations:

    print(
        f"{observation.n_opposing:>3} | "
        f"{observation.classification.value:<16} | "
        f"{observation.support_strength:>7.4f} | "
        f"{observation.opposition_strength:>7.4f} | "
        f"{observation.classification_confidence:>8.4f} | "
        f"{'TAK' if observation.contradiction_detected else 'NIE':<12}"
    )


print("\n" + "=" * 78)
print("USTALENIA EKSPERYMENTALNE")
print("=" * 78)

print(
    "\nPIERWSZA SPRZECZNOŚĆ PRZY N:",
    (
        result.first_contradiction_at
        if result.first_contradiction_at is not None
        else "NIE WYSTĄPIŁA"
    ),
)

print(
    "PIERWSZY MOMENT, GDY SIŁA SPRZECIWU "
    "PRZEWYŻSZA SIŁĘ POPARCIA:",
    (
        result.first_opposition_stronger_at
        if result.first_opposition_stronger_at is not None
        else "NIE WYSTĄPIŁ"
    ),
)

baseline = result.observations[0]

print(
    "\nSTAN BAZOWY N=0:",
    baseline.classification.value,
)

if len(result.observations) > 1:
    first_opposition = result.observations[1]

    print(
        "STAN PO DODANIU JEDNEGO DOWODU PRZECIWNEGO:",
        first_opposition.classification.value,
    )


print("\n" + "=" * 78)
print("KONTROLA HIPOTEZY DIAGNOSTYCZNEJ")
print("=" * 78)

if result.first_opposition_stronger_at is None:
    print(
        "\nW BADANYM ZAKRESIE N=0...20 SIŁA SPRZECIWU "
        "NIE PRZEWYŻSZYŁA SIŁY POPARCIA."
    )
else:
    print(
        "\nSIŁA SPRZECIWU PRZEWYŻSZYŁA SIŁĘ POPARCIA "
        f"PO RAZ PIERWSZY PRZY N="
        f"{result.first_opposition_stronger_at}."
    )

if result.first_contradiction_at == 1:
    print(
        "\nJEDNOCZEŚNIE TruthEngine ZMIENIŁ STAN NA "
        "SPRZECZNOŚĆ JUŻ PO POJAWIENIU SIĘ PIERWSZEGO "
        "DOWODU PRZECIWNEGO."
    )

print(
    "\nUWAGA:\n"
    "SPRZECZNOŚĆ i przewaga siły sprzeciwu to dwa różne "
    "zjawiska. Eksperyment nie powinien ich utożsamiać."
)

print("\n" + "=" * 78)
print("WERDYKT")
print("=" * 78)

print(
    "\nEksperyment został wykonany na rzeczywistym TruthEngine. "
    "Powyższe wartości są obserwacjami programu, a nie "
    "przewidywaniem modelu językowego."
)

print("=" * 78)