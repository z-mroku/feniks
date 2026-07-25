from core.feniks import Feniks


feniks = Feniks()

print("=" * 70)
print(feniks.start())
print("=" * 70)

print("\nREJESTR ROZWOJU FENIKSA")
print("-" * 70)

# Rejestrujemy pierwsze rzeczywiste doświadczenie rozwojowe.
wpis = feniks.register_first_development_experience()

print(f"\nTYTUŁ:")
print(wpis.title)

print(f"\nKATEGORIA:")
print(wpis.category.value)

print(f"\nSTATUS:")
print(wpis.status.value)

print(f"\nWYKRYTO PRZEZ:")
print(wpis.discovered_by)

print(f"\nOPIS:")
print(wpis.description)

print("\nDOWODY:")
if wpis.evidence:
    for numer, dowod in enumerate(wpis.evidence, start=1):
        print(f"{numer}. {dowod}")
else:
    print("Brak zapisanych dowodów.")

print("\nWPROWADZONE ZMIANY:")
if wpis.changes:
    for numer, zmiana in enumerate(wpis.changes, start=1):
        print(f"{numer}. {zmiana}")
else:
    print("Brak zapisanych zmian.")

print("\nWYNIKI TESTÓW:")
if wpis.test_results:
    for numer, wynik in enumerate(wpis.test_results, start=1):
        print(f"{numer}. {wynik}")
else:
    print("Brak wyników testów.")

print("\nNIEROZWIĄZANE KWESTIE:")
if wpis.unresolved:
    for numer, problem in enumerate(wpis.unresolved, start=1):
        print(f"{numer}. {problem}")
else:
    print("Brak nierozwiązanych kwestii.")

print("\n" + "=" * 70)
print("HISTORIA ROZWOJU")
print("=" * 70)

historia = feniks.development_history()

print(f"Liczba zapisanych doświadczeń: {len(historia)}")

for numer, element in enumerate(historia, start=1):
    print(
        f"{numer}. {element.title} "
        f"[{element.status.value}]"
    )

print("\n" + "=" * 70)
print("STAN FENIKSA")
print("=" * 70)

for klucz, wartosc in feniks.status().items():

    if isinstance(wartosc, bool):
        wartosc = "TAK" if wartosc else "NIE"

    print(
        f"- {klucz.replace('_', ' ').upper()}: "
        f"{wartosc}"
    )