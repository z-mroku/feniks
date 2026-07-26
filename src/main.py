from core.feniks import Feniks
from core.truth_engine import (
    Claim,
    Evidence,
    KnowledgeType,
    SourceType,
)


feniks = Feniks()

print("=" * 70)
print(feniks.start())
print("=" * 70)

print("\nTEST NOWEGO SILNIKA PRAWDY")
print("-" * 70)


def pokaz_wynik(numer, ocena):
    """
    Czytelnie wyświetla wynik analizy.
    """

    print("\n" + "=" * 70)
    print(f"TEST {numer}")
    print("=" * 70)

    print(
        f"\nTWIERDZENIE:\n"
        f"{ocena.claim.content}"
    )

    print(
        f"\nKLASYFIKACJA:\n"
        f"{ocena.classification.value}"
    )

    print(
        f"\nSIŁA POPARCIA:\n"
        f"{ocena.support_strength * 100:.1f}%"
    )

    print(
        f"\nSIŁA SPRZECIWU:\n"
        f"{ocena.opposition_strength * 100:.1f}%"
    )

    print(
        f"\nPEWNOŚĆ KLASYFIKACJI:\n"
        f"{ocena.classification_confidence * 100:.1f}%"
    )

    print(
        f"\nDOWODY ZA:\n"
        f"{ocena.supporting_evidence}"
    )

    print(
        f"\nDOWODY PRZECIW:\n"
        f"{ocena.opposing_evidence}"
    )

    print(
        "\nSPRZECZNOŚĆ:\n"
        + (
            "TAK"
            if ocena.contradiction_detected
            else "NIE"
        )
    )

    print(
        "\nPOTRZEBA WIĘCEJ DOWODÓW:\n"
        + (
            "TAK"
            if ocena.requires_more_evidence
            else "NIE"
        )
    )

    print(
        f"\nUZASADNIENIE:\n"
        f"{ocena.explanation}"
    )


# =========================================================
# TEST 1
# BRAK DOWODÓW
# =========================================================

twierdzenie_1 = Claim(
    content="Jutro będzie padał deszcz.",
    knowledge_type=KnowledgeType.UNKNOWN,
)

feniks.register_claim(
    twierdzenie_1
)

ocena_1 = feniks.assess_claim(
    twierdzenie_1
)

pokaz_wynik(
    1,
    ocena_1,
)


# =========================================================
# TEST 2
# DWA MOCNE DOWODY WSPIERAJĄCE
# =========================================================

twierdzenie_2 = Claim(
    content=(
        "Testowy moduł Silnika Prawdy "
        "został uruchomiony."
    ),
    knowledge_type=KnowledgeType.UNKNOWN,
)

feniks.register_claim(
    twierdzenie_2
)

feniks.add_evidence(
    twierdzenie_2,
    Evidence(
        description=(
            "Program uruchomił kod modułu "
            "Silnika Prawdy."
        ),
        source="FENIKS",
        source_type=SourceType.SYSTEM,
        reliability=0.98,
        supports_claim=True,
    ),
)

feniks.add_evidence(
    twierdzenie_2,
    Evidence(
        description=(
            "Test otrzymał wynik analizy "
            "z Silnika Prawdy."
        ),
        source="test systemowy",
        source_type=SourceType.SYSTEM,
        reliability=0.95,
        supports_claim=True,
    ),
)

ocena_2 = feniks.assess_claim(
    twierdzenie_2
)

pokaz_wynik(
    2,
    ocena_2,
)


# =========================================================
# TEST 3
# MOCNY DOWÓD ZA I MOCNY DOWÓD PRZECIW
# =========================================================

twierdzenie_3 = Claim(
    content=(
        "Eksperymentalny czujnik "
        "wykrył obiekt."
    ),
    knowledge_type=KnowledgeType.UNKNOWN,
)

feniks.register_claim(
    twierdzenie_3
)

feniks.add_evidence(
    twierdzenie_3,
    Evidence(
        description=(
            "Czujnik A zgłosił obecność obiektu."
        ),
        source="czujnik A",
        source_type=SourceType.SENSOR,
        reliability=0.90,
        supports_claim=True,
    ),
)

feniks.add_evidence(
    twierdzenie_3,
    Evidence(
        description=(
            "Niezależny czujnik B "
            "nie potwierdził obecności obiektu."
        ),
        source="czujnik B",
        source_type=SourceType.SENSOR,
        reliability=0.88,
        supports_claim=False,
    ),
)

ocena_3 = feniks.assess_claim(
    twierdzenie_3
)

pokaz_wynik(
    3,
    ocena_3,
)


# =========================================================
# TEST 4
# SŁABY DOWÓD ZA I BARDZO MOCNY DOWÓD PRZECIW
# =========================================================

twierdzenie_4 = Claim(
    content=(
        "Eksperymentalny system działa poprawnie."
    ),
    knowledge_type=KnowledgeType.UNKNOWN,
)

feniks.register_claim(
    twierdzenie_4
)

feniks.add_evidence(
    twierdzenie_4,
    Evidence(
        description=(
            "Jeden wstępny test zakończył się "
            "wynikiem pozytywnym."
        ),
        source="test wstępny",
        source_type=SourceType.SYSTEM,
        reliability=0.35,
        supports_claim=True,
    ),
)

feniks.add_evidence(
    twierdzenie_4,
    Evidence(
        description=(
            "Test kontrolny wykazał błąd systemu."
        ),
        source="test kontrolny",
        source_type=SourceType.SYSTEM,
        reliability=0.98,
        supports_claim=False,
    ),
)

ocena_4 = feniks.assess_claim(
    twierdzenie_4
)

pokaz_wynik(
    4,
    ocena_4,
)


# =========================================================
# STAN SILNIKA
# =========================================================

print("\n" + "=" * 70)
print("STAN SILNIKA PRAWDY")
print("=" * 70)

statystyki = feniks.truth_engine.stats()

print(
    f"ZAREJESTROWANE TWIERDZENIA: "
    f"{statystyki['registered_claims']}"
)

print(
    f"WYKONANE ANALIZY: "
    f"{statystyki['assessments']}"
)

print(
    f"WYKRYTE SPRZECZNOŚCI: "
    f"{statystyki['contradictions']}"
)

print(
    f"NIEROZSTRZYGNIĘTE: "
    f"{statystyki['unresolved']}"
)

print("\n" + "=" * 70)
print("TEST SILNIKA PRAWDY ZAKOŃCZONY")
print("=" * 70)