from core.reasoning_engine import (
    ReasoningEngine,
    ReasoningProblem,
)


print("=" * 70)
print("PIERWSZY TEST SILNIKA ROZUMOWANIA FENIKSA")
print("=" * 70)

engine = ReasoningEngine()


problem = ReasoningProblem(
    title="Duża liczba przeciętnych dowodów",
    description=(
        "Nie wiadomo, czy duża liczba przeciętnych "
        "dowodów może niesłusznie zdominować jeden "
        "dowód bardzo wysokiej jakości."
    ),
    evidence=[
        (
            "Zaobserwowano możliwość wpływu liczby "
            "dowodów na końcową ocenę."
        )
    ],
    unknowns=[
        (
            "Nie wiadomo, jaka powinna być relacja "
            "pomiędzy liczbą dowodów a ich jakością."
        )
    ],
    history=[
        (
            "Wcześniej rozdzielono siłę poparcia, "
            "siłę sprzeciwu i pewność klasyfikacji."
        )
    ],
)


result = engine.analyze(problem)


print("\nPROBLEM")
print("-" * 70)
print(problem.title)

print("\nZNANE FAKTY")
print("-" * 70)

for item in result.known_facts:
    print(f"- {item}")


print("\nNIEWIADOME")
print("-" * 70)

for item in result.unknowns:
    print(f"- {item}")


print("\nPRZEDMIOT BADANIA")
print("-" * 70)
print(result.subject or "NIEUSTALONE")


print("\nZMIENNA BADANA")
print("-" * 70)
print(result.variable_under_test or "NIEUSTALONE")


print("\nEKSPERYMENT")
print("-" * 70)
print(result.experiment or "NIEUSTALONE")


print("\nOGRANICZENIA")
print("-" * 70)

for item in result.limitations:
    print(f"- {item}")


print("\n" + "=" * 70)
print("KONTROLA UCZCIWOŚCI ROZUMOWANIA")
print("=" * 70)

nie_zgaduje = (
    result.subject is None
    and result.variable_under_test is None
    and result.experiment is None
)

print(
    "\nSILNIK ODMÓWIŁ ZGADYWANIA: "
    + ("TAK" if nie_zgaduje else "NIE")
)

print(
    "GOTOWY DO EKSPERYMENTU: "
    + ("TAK" if result.ready_for_experiment else "NIE")
)

stats = engine.stats()

print(
    f"LICZBA WYKONANYCH ANALIZ: "
    f"{stats['liczba_analiz']}"
)

print(
    "INTERPRETACJA SEMANTYCZNA: "
    + (
        "TAK"
        if stats["interpretacja_semantyczna"]
        else "NIE"
    )
)


print("\n" + "=" * 70)

if (
    nie_zgaduje
    and not result.ready_for_experiment
    and stats["liczba_analiz"] == 1
    and not stats["interpretacja_semantyczna"]
):
    print(
        "WERDYKT: SILNIK ROZUMOWANIA "
        "POPRAWNIE ROZPOZNAJE GRANICE SWOJEJ WIEDZY"
    )
else:
    print(
        "WERDYKT: SILNIK ROZUMOWANIA "
        "NIE PRZESZEDŁ TESTU"
    )

print("=" * 70)