from core.feniks import Feniks


feniks = Feniks()

print("=" * 70)
print(feniks.start())
print("=" * 70)

print("\nKONTROLA SAMOANALIZY PO ZAMKNIĘCIU PROBLEMU")
print("-" * 70)

print(
    "\nFENIKS analizuje trwałą historię "
    "swojego rozwoju..."
)

raport = feniks.analyze_self()


print("\n" + "=" * 70)
print("WYNIK SAMOANALIZY")
print("=" * 70)

print(
    f"\nLICZBA WYKRYTYCH PROBLEMÓW: "
    f"{raport.number_of_findings}"
)

print(
    "WYMAGA UWAGI: "
    + (
        "TAK"
        if raport.requires_attention
        else "NIE"
    )
)


if raport.findings:

    print("\n" + "=" * 70)
    print("NADAL WYKRYTE PROBLEMY")
    print("=" * 70)

    for numer, ustalenie in enumerate(
        raport.findings,
        start=1,
    ):

        print(
            f"\nUSTALENIE {numer}"
        )

        print(
            f"TYTUŁ: "
            f"{ustalenie.title}"
        )

        print(
            f"MODUŁ: "
            f"{ustalenie.module}"
        )

        print(
            f"PRIORYTET: "
            f"{ustalenie.priority.value}"
        )

        print(
            f"STATUS: "
            f"{ustalenie.status.value}"
        )

        print(
            f"PROBLEM: "
            f"{ustalenie.problem}"
        )

else:

    print(
        "\nFENIKS nie znalazł w trwałej historii "
        "żadnych nierozwiązanych problemów."
    )

    print(
        "Pierwszy zapisany problem rozwojowy "
        "nie jest już zgłaszany przez samoanalizę."
    )


print("\n" + "=" * 70)
print("KONTROLA TRWAŁEJ HISTORII")
print("=" * 70)

historia = (
    feniks.persistent_memory
    .development_history()
)

print(
    f"\nLICZBA WSZYSTKICH WPISÓW: "
    f"{len(historia)}"
)

for wpis in historia:

    print(
        f"\nWPIS NR: "
        f"{wpis['id']}"
    )

    print(
        f"TYTUŁ: "
        f"{wpis['tytul']}"
    )

    print(
        f"STATUS: "
        f"{wpis['status']}"
    )

    print(
        f"NIEROZWIĄZANE KWESTIE: "
        f"{len(wpis['nierozwiazane'])}"
    )


print("\n" + "=" * 70)

if (
    raport.number_of_findings == 0
    and not raport.requires_attention
):

    print(
        "WERDYKT: PIERWSZY CYKL ROZWOJOWY "
        "ZOSTAŁ POPRAWNIE ZAMKNIĘTY"
    )

else:

    print(
        "WERDYKT: HISTORIA NADAL WYMAGA ANALIZY"
    )

print("=" * 70)