import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.system_knowledge import SystemKnowledge


print("=" * 78)
print("TEST SAMOWIEDZY FENIKSA")
print("=" * 78)

knowledge = SystemKnowledge()
facts = knowledge.inspect_truth_engine()

for fact in facts:
    print()
    print(f"KLUCZ: {fact.key}")
    print(f"OPIS: {fact.description}")
    print(f"WARTOŚĆ: {fact.value}")

print()
print("=" * 78)
print("KONTROLA KLUCZOWEJ REGUŁY")
print("=" * 78)

two_sided = knowledge.get(
    "truth.any_two_sided_evidence_test"
)

quantity = knowledge.get(
    "truth.quantity_saturation"
)

two_sided_ok = (
    two_sided is not None
    and two_sided.value["classification"]
    == "SPRZECZNOŚĆ"
    and two_sided.value["contradiction_detected"]
    is True
)

saturation_ok = (
    quantity is not None
    and quantity.value["saturation_at"] == 3
)

print()
print(
    "BARDZO SŁABY DOWÓD PRZECIWNY "
    "WYWOŁAŁ SPRZECZNOŚĆ:",
    "TAK" if two_sided_ok else "NIE",
)

print(
    "SATURACJA WPŁYWU LICZBY DOWODÓW "
    "OD N=3:",
    "TAK" if saturation_ok else "NIE",
)

print()
print("=" * 78)

if two_sided_ok and saturation_ok:
    print(
        "WERDYKT: FENIKS POTRAFI USTALIĆ "
        "WYBRANE REGUŁY WŁASNEGO SILNIKA "
        "PRZEZ JEGO RZECZYWISTE WYKONANIE"
    )
else:
    print(
        "WERDYKT: SAMOWIEDZA NIE ZGADZA SIĘ "
        "Z OCZEKIWANYM ZACHOWANIEM SILNIKA"
    )

print("=" * 78)