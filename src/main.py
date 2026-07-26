from core.feniks import Feniks


feniks = Feniks()

print("=" * 70)
print(feniks.start())
print("=" * 70)

print("\nSAMOANALIZA FENIKSA")
print("-" * 70)

print(
    "\nFENIKS analizuje trwałą historię "
    "swojego rozwoju..."
)

raport = feniks.analyze_self()

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


if raport.number_of_findings == 0:

    print(
        "\nNie znaleziono nierozwiązanych "
        "problemów wymagających analizy."
    )

else:

    for numer, ustalenie in enumerate(
        raport.findings,
        start=1,
    ):

        print("\n" + "=" * 70)
        print(
            f"USTALENIE SAMOANALIZY {numer}"
        )
        print("=" * 70)

        print(
            f"\nTYTUŁ:\n"
            f"{ustalenie.title}"
        )

        print(
            f"\nMODUŁ:\n"
            f"{ustalenie.module}"
        )

        print(
            f"\nPRIORYTET:\n"
            f"{ustalenie.priority.value}"
        )

        print(
            f"\nSTATUS:\n"
            f"{ustalenie.status.value}"
        )

        print(
            f"\nŹRÓDŁOWY WPIS HISTORII:\n"
            f"{ustalenie.source_entry_id}"
        )

        print(
            f"\nWYKRYTY PROBLEM:\n"
            f"{ustalenie.problem}"
        )

        print("\nPODSTAWA ANALIZY:")

        if ustalenie.evidence:

            for nr, dowod in enumerate(
                ustalenie.evidence,
                start=1,
            ):
                print(
                    f"{nr}. {dowod}"
                )

        else:
            print(
                "Brak zapisanej podstawy analizy."
            )

        print("\nCZEGO JESZCZE NIE WIEM:")

        if ustalenie.unknowns:

            for nr, niewiadoma in enumerate(
                ustalenie.unknowns,
                start=1,
            ):
                print(
                    f"{nr}. {niewiadoma}"
                )

        else:
            print(
                "Nie wykryto dodatkowych "
                "braków informacji."
            )

        print("\nPROPONOWANY NASTĘPNY KROK:")

        if ustalenie.proposed_next_step:
            print(
                ustalenie.proposed_next_step
            )
        else:
            print(
                "Nie przygotowano propozycji."
            )


print("\n" + "=" * 70)
print("STAN MODUŁU SAMOANALIZY")
print("=" * 70)

statystyki = feniks.self_analysis.stats()

print(
    "MODUŁ SAMOANALIZY GOTOWY: "
    + (
        "TAK"
        if statystyki["modul_gotowy"]
        else "NIE"
    )
)

print(
    f"RAPORTY W BIEŻĄCEJ SESJI: "
    f"{statystyki['liczba_raportow']}"
)

print(
    f"USTALENIA W BIEŻĄCEJ SESJI: "
    f"{statystyki['liczba_ustalen']}"
)

print("\n" + "=" * 70)
print("SAMOANALIZA ZAKOŃCZONA")
print("=" * 70)