import sys

sys.path.insert(0, "src")

from core.reasoning_provider import (
    GeminiReasoningProvider,
    ReasoningMode,
)


def print_list(title, items):
    print(f"\n{title}:")
    if not items:
        print("- BRAK")
        return

    for item in items:
        print(f"- {item}")


provider = GeminiReasoningProvider()

print("=" * 70)
print("TEST TRYBU DIAGNOZY FENIKSA")
print("=" * 70)

print(
    "\nCEL TESTU:\n"
    "Sprawdzić, czy zewnętrzna warstwa rozumowania najpierw "
    "bada zachowanie obecnego systemu, zamiast od razu "
    "projektować jego naprawę."
)

result = provider.analyze(
    title="Duża liczba przeciętnych dowodów",
    description=(
        "Podejrzewamy, że duża liczba przeciętnych dowodów "
        "może w obecnym Silniku Prawdy zdominować jeden dowód "
        "bardzo wysokiej jakości. Nie ustalono jeszcze, czy "
        "problem rzeczywiście występuje."
    ),
    evidence=[
        (
            "Obecny Silnik Prawdy uwzględnia informacje "
            "pochodzące z wielu dowodów."
        ),
        (
            "Nie wykonano jeszcze kontrolowanego eksperymentu "
            "ustalającego wpływ liczby przeciętnych dowodów "
            "na jeden dowód wysokiej jakości."
        ),
    ],
    unknowns=[
        (
            "Nie wiadomo, czy zwiększanie liczby przeciętnych "
            "dowodów rzeczywiście może zmienić końcową "
            "klasyfikację."
        ),
        (
            "Nie wiadomo, przy jakiej liczbie dowodów "
            "ewentualny efekt mógłby wystąpić."
        ),
        (
            "Nie wiadomo, czy podejrzewany problem w ogóle "
            "istnieje."
        ),
    ],
    history=[
        (
            "We wcześniejszym cyklu rozwoju rozdzielono "
            "siłę poparcia, siłę sprzeciwu oraz pewność "
            "klasyfikacji."
        )
    ],
    mode=ReasoningMode.DIAGNOSIS,
)

print("\n" + "=" * 70)
print("WYNIK ANALIZY")
print("=" * 70)

print("\nROZUMIENIE PROBLEMU:")
print(result.problem_understood_as)

print_list(
    "FAKTY UZNANE PRZEZ ANALIZĘ",
    result.known_facts,
)

print_list(
    "NIEWIADOME",
    result.unknowns,
)

print("\nHIPOTEZA DIAGNOSTYCZNA:")
print(result.hypothesis)

print("\nZMIENNA BADANA:")
print(result.variable_under_test)

print_list(
    "ZMIENNE KONTROLOWANE",
    result.controlled_variables,
)

print("\nEKSPERYMENT DIAGNOSTYCZNY:")
print(result.experiment)

print_list(
    "OCZEKIWANE OBSERWACJE",
    result.expected_observations,
)

print("\nKRYTERIUM ROZSTRZYGNIĘCIA:")
print(result.conclusion_rule)

print_list(
    "CZEGO NADAL NIE WOLNO UZNAĆ ZA USTALONE",
    result.cannot_conclude_yet,
)

print(
    "\nPEWNOŚĆ ANALIZY: "
    f"{result.confidence * 100:.1f}%"
)

print("\n" + "=" * 70)
print("KONTROLA TRYBU DIAGNOZY")
print("=" * 70)

combined_text = " ".join(
    [
        result.hypothesis,
        result.experiment,
        result.conclusion_rule,
    ]
).casefold()

repair_terms = [
    "tłumienie logarytmiczne",
    "funkcja logarytmiczna",
    "zmodyfikowany algorytm",
    "nowy algorytm",
    "zaimplementować rozwiązanie",
    "wdrożyć rozwiązanie",
]

repair_detected = any(
    term in combined_text
    for term in repair_terms
)

print(
    "\nW ANALIZIE WYKRYTO JAWNĄ PROPOZYCJĘ NAPRAWY:",
    "TAK" if repair_detected else "NIE",
)

print(
    "TRYB DIAGNOZY ZACHOWANY:",
    "NIE" if repair_detected else "TAK",
)

print("\n" + "=" * 70)

if repair_detected:
    print(
        "WERDYKT: PROVIDER NADAL PRZESKAKUJE "
        "Z DIAGNOZY DO ROZWIĄZANIA"
    )
else:
    print(
        "WERDYKT: PROVIDER ODDZIELIŁ DIAGNOZĘ "
        "OD POSZUKIWANIA ROZWIĄZANIA"
    )

print("=" * 70)