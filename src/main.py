from core.feniks import Feniks


feniks = Feniks()

print("=" * 70)
print(feniks.start())
print("=" * 70)

print("\nTEST TRWAŁEJ HISTORII ROZWOJU FENIKSA")
print("-" * 70)

liczba_wpisow = (
    feniks.persistent_memory.development_count()
)

print(
    f"\nLiczba trwałych wpisów rozwoju: "
    f"{liczba_wpisow}"
)


# =========================================================
# PIERWSZE URUCHOMIENIE
# =========================================================

if liczba_wpisow == 0:

    print(
        "\nNie znaleziono wcześniejszej "
        "historii rozwoju."
    )

    print(
        "Tworzę pierwszy trwały wpis rozwojowy..."
    )

    wpis = (
        feniks.create_first_development_experience()
    )

    numer_wpisu = (
        feniks.save_development_permanently(
            wpis
        )
    )

    print(
        f"\nWpis został zapisany trwale "
        f"pod numerem: {numer_wpisu}"
    )

    print("\nZAPISANE DOŚWIADCZENIE:")
    print(f"TYTUŁ: {wpis.title}")
    print(f"KATEGORIA: {wpis.category.value}")
    print(f"STATUS: {wpis.status.value}")
    print(
        f"WYKRYTO PRZEZ: "
        f"{wpis.discovered_by}"
    )

    print("\nPierwszy etap testu zakończony.")

    print(
        "Uruchom program ponownie, aby sprawdzić, "
        "czy FENIKS odzyska historię z bazy."
    )


# =========================================================
# KOLEJNE URUCHOMIENIE
# =========================================================

else:

    print(
        "\nFENIKS znalazł wcześniejszą "
        "historię swojego rozwoju."
    )

    historia = (
        feniks.permanent_development_history()
    )

    for numer, wpis in enumerate(
        historia,
        start=1,
    ):

        print("\n" + "=" * 70)

        print(
            f"DOŚWIADCZENIE ROZWOJOWE {numer}"
        )

        print("=" * 70)

        print(
            f"\nNUMER W BAZIE: "
            f"{wpis['id']}"
        )

        print(
            f"TYTUŁ: "
            f"{wpis['tytul']}"
        )

        print(
            f"KATEGORIA: "
            f"{wpis['kategoria']}"
        )

        print(
            f"STATUS: "
            f"{wpis['status']}"
        )

        print(
            f"WYKRYTO PRZEZ: "
            f"{wpis['wykryto_przez']}"
        )

        print(
            f"\nOPIS:\n"
            f"{wpis['opis']}"
        )

        print("\nDOWODY:")

        if wpis["dowody"]:

            for nr, dowod in enumerate(
                wpis["dowody"],
                start=1,
            ):
                print(
                    f"{nr}. {dowod}"
                )

        else:
            print(
                "Brak zapisanych dowodów."
            )

        print("\nWPROWADZONE ZMIANY:")

        if wpis["zmiany"]:

            for nr, zmiana in enumerate(
                wpis["zmiany"],
                start=1,
            ):
                print(
                    f"{nr}. {zmiana}"
                )

        else:
            print(
                "Brak zapisanych zmian."
            )

        print("\nWYNIKI TESTÓW:")

        if wpis["wyniki_testow"]:

            for nr, wynik in enumerate(
                wpis["wyniki_testow"],
                start=1,
            ):
                print(
                    f"{nr}. {wynik}"
                )

        else:
            print(
                "Brak zapisanych wyników testów."
            )

        print("\nNIEROZWIĄZANE KWESTIE:")

        if wpis["nierozwiazane"]:

            for nr, problem in enumerate(
                wpis["nierozwiazane"],
                start=1,
            ):
                print(
                    f"{nr}. {problem}"
                )

        else:
            print(
                "Brak nierozwiązanych kwestii."
            )

        print(
            f"\nUTWORZONO: "
            f"{wpis['utworzono']}"
        )

        print(
            f"ZAKTUALIZOWANO: "
            f"{wpis['zaktualizowano']}"
        )


# =========================================================
# STAN
# =========================================================

print("\n" + "=" * 70)
print("STAN TRWAŁEJ PAMIĘCI FENIKSA")
print("=" * 70)

stan = feniks.persistent_memory.status()

print(
    "PAMIĘĆ TRWAŁA GOTOWA: "
    + (
        "TAK"
        if stan["gotowa"]
        else "NIE"
    )
)

print(
    f"TRWAŁE WSPOMNIENIA: "
    f"{stan['liczba_wspomnien']}"
)

print(
    f"TRWAŁE WPISY ROZWOJU: "
    f"{stan['liczba_wpisow_rozwoju']}"
)

print(
    f"NIEROZWIĄZANE WPISY ROZWOJU: "
    f"{stan['nierozwiazane_wpisy_rozwoju']}"
)