from core.feniks import Feniks


feniks = Feniks()

print("=" * 70)
print(feniks.start())
print("=" * 70)

print("\nTEST NOWEJ SAMOANALIZY")
print("-" * 70)

# =========================================================
# 1. STAN PRZED TESTEM
# =========================================================

historia_przed = feniks.permanent_development_history()
nierozwiazane_przed = feniks.unresolved_permanent_development()

print(f"\nWSZYSTKIE WPISY PRZED TESTEM: {len(historia_przed)}")
print(f"NIEROZWIĄZANE PRZED TESTEM: {len(nierozwiazane_przed)}")


# =========================================================
# 2. SAMOANALIZA
# =========================================================

raport = feniks.analyze_self()

print("\n" + "=" * 70)
print("WYNIK SAMOANALIZY")
print("=" * 70)

print(f"\nLICZBA USTALEŃ: {raport.number_of_findings}")
print(
    "WYMAGA UWAGI: "
    + ("TAK" if raport.requires_attention else "NIE")
)


# =========================================================
# 3. ODNALEZIENIE PROBLEMÓW NR 2 I NR 3
# =========================================================

problem_2 = next(
    (
        finding
        for finding in raport.findings
        if finding.source_entry_id == 2
    ),
    None,
)

problem_3 = next(
    (
        finding
        for finding in raport.findings
        if finding.source_entry_id == 3
    ),
    None,
)

if problem_2 is None:
    raise RuntimeError(
        "Samoanaliza nie znalazła problemu nr 2."
    )

if problem_3 is None:
    raise RuntimeError(
        "Samoanaliza nie znalazła problemu nr 3."
    )


# =========================================================
# 4. PROBLEM NR 2
# =========================================================

print("\n" + "=" * 70)
print("PROBLEM NR 2")
print("=" * 70)

print(f"\nTYTUŁ:\n{problem_2.title}")

print(
    f"\nPROBLEM:\n"
    f"{problem_2.problem}"
)

print(
    f"\nPROPONOWANY NASTĘPNY KROK:\n"
    f"{problem_2.proposed_next_step}"
)


# =========================================================
# 5. PROBLEM NR 3
# =========================================================

print("\n" + "=" * 70)
print("PROBLEM NR 3")
print("=" * 70)

print(f"\nTYTUŁ:\n{problem_3.title}")

print(
    f"\nPROBLEM:\n"
    f"{problem_3.problem}"
)

print(
    f"\nPROPONOWANY NASTĘPNY KROK:\n"
    f"{problem_3.proposed_next_step}"
)


# =========================================================
# 6. TEST RÓŻNICOWANIA
# =========================================================

krok_2 = (
    problem_2.proposed_next_step
    or ""
)

krok_3 = (
    problem_3.proposed_next_step
    or ""
)

rozne_kroki = (
    krok_2.casefold()
    != krok_3.casefold()
)

problem_2_dotyczy_testow_dowodow = (
    "różnych poziomach" in krok_2.casefold()
    and "wiarygodności" in krok_2.casefold()
)

problem_3_dotyczy_samoanalizy = (
    "kilku różnych nierozwiązanych problemach"
    in krok_3.casefold()
    and "zamiast jednej odpowiedzi"
    in krok_3.casefold()
)


print("\n" + "=" * 70)
print("TEST RÓŻNICOWANIA")
print("=" * 70)

print(
    "\nRÓŻNE PROBLEMY OTRZYMAŁY RÓŻNE KROKI: "
    + ("TAK" if rozne_kroki else "NIE")
)

print(
    "PROBLEM NR 2 OTRZYMAŁ TEST WIARYGODNOŚCI DOWODÓW: "
    + (
        "TAK"
        if problem_2_dotyczy_testow_dowodow
        else "NIE"
    )
)

print(
    "PROBLEM NR 3 OTRZYMAŁ TEST SAMOANALIZY: "
    + (
        "TAK"
        if problem_3_dotyczy_samoanalizy
        else "NIE"
    )
)


# =========================================================
# 7. SPRAWDZENIE, CZY TEST NIE ZMIENIŁ BAZY
# =========================================================

historia_po = feniks.permanent_development_history()
nierozwiazane_po = feniks.unresolved_permanent_development()

baza_bez_zmian = (
    len(historia_przed) == len(historia_po)
    and len(nierozwiazane_przed) == len(nierozwiazane_po)
)


print("\n" + "=" * 70)
print("KONTROLA PAMIĘCI")
print("=" * 70)

print(
    f"\nWSZYSTKIE WPISY PO TEŚCIE: "
    f"{len(historia_po)}"
)

print(
    f"NIEROZWIĄZANE PO TEŚCIE: "
    f"{len(nierozwiazane_po)}"
)

print(
    "BAZA POZOSTAŁA BEZ ZMIAN: "
    + ("TAK" if baza_bez_zmian else "NIE")
)


# =========================================================
# 8. WERDYKT
# =========================================================

test_zaliczony = (
    raport.number_of_findings == 2
    and rozne_kroki
    and problem_2_dotyczy_testow_dowodow
    and problem_3_dotyczy_samoanalizy
    and baza_bez_zmian
)


print("\n" + "=" * 70)

if test_zaliczony:
    print(
        "WERDYKT: NOWA SAMOANALIZA "
        "PRZESZŁA TEST PORÓWNAWCZY"
    )
else:
    print(
        "WERDYKT: NOWA SAMOANALIZA "
        "WYMAGA DALSZEJ ANALIZY"
    )

print("=" * 70)