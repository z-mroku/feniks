from core.feniks import Feniks


feniks = Feniks()

print("=" * 70)
print(feniks.start())
print("=" * 70)

print("\nTEST TRWAŁEJ PAMIĘCI FENIKSA")
print("-" * 70)

liczba_wpisow = feniks.persistent_memory.count()

print(
    f"\nLiczba wpisów znalezionych "
    f"w trwałej pamięci: {liczba_wpisow}"
)


if liczba_wpisow == 0:

    print("\nTo jest pierwsze uruchomienie testu.")
    print("Zapisuję pierwsze trwałe wspomnienie...")

    numer_wpisu = feniks.remember_permanently(
        category="ROZWÓJ",
        title="Pierwsze trwałe wspomnienie FENIKSA",
        content=(
            "FENIKS uruchomił swoją pierwszą trwałą "
            "pamięć SQLite. To wspomnienie powinno "
            "przetrwać zamknięcie i ponowne "
            "uruchomienie programu."
        ),
        source="FENIKS",
        metadata={
            "rodzaj": "test trwałości pamięci",
            "ważne": True,
        },
    )

    print(
        f"\nWspomnienie zostało zapisane "
        f"pod numerem: {numer_wpisu}"
    )

    print("\nTERAZ WAŻNE:")
    print(
        "Pierwszy etap testu został zakończony."
    )
    print(
        "Uruchom ten sam program jeszcze raz."
    )

else:

    print(
        "\nFENIKS został uruchomiony ponownie "
        "i znalazł wcześniejsze wspomnienia."
    )

    wspomnienia = feniks.recall_permanent(
        limit=10
    )

    print("\nODZYSKANE WSPOMNIENIA:")
    print("-" * 70)

    for wspomnienie in wspomnienia:

        print(
            f"\nNUMER: "
            f"{wspomnienie['id']}"
        )

        print(
            f"KATEGORIA: "
            f"{wspomnienie['kategoria']}"
        )

        print(
            f"TYTUŁ: "
            f"{wspomnienie['tytul']}"
        )

        print(
            f"TREŚĆ: "
            f"{wspomnienie['tresc']}"
        )

        print(
            f"ŹRÓDŁO: "
            f"{wspomnienie['zrodlo']}"
        )

        print(
            f"UTWORZONO: "
            f"{wspomnienie['utworzono']}"
        )

        print(
            f"METADANE: "
            f"{wspomnienie['metadane']}"
        )


print("\n" + "=" * 70)
print("STAN PAMIĘCI")
print("=" * 70)

stan = feniks.persistent_memory.status()

print(
    f"PAMIĘĆ TRWAŁA GOTOWA: "
    f"{'TAK' if stan['gotowa'] else 'NIE'}"
)

print(
    f"LICZBA TRWAŁYCH WSPOMNIEŃ: "
    f"{stan['liczba_wpisow']}"
)