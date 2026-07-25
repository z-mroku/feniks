from core.feniks import Feniks
from core.truth_engine import (
    Claim,
    Evidence,
    KnowledgeType,
    SourceType,
)


feniks = Feniks()

print("=" * 60)
print(feniks.start())
print("=" * 60)


def show_assessment(number, assessment):
    print(f"\nTEST {number}")
    print(f"TWIERDZENIE: {assessment.claim.content}")
    print(
        f"KLASYFIKACJA: "
        f"{assessment.classification.value.upper()}"
    )
    print(
        f"PEWNOŚĆ: "
        f"{assessment.confidence:.0%}"
    )
    print(
        f"DOWODY ZA: "
        f"{assessment.supporting_evidence}"
    )
    print(
        f"DOWODY PRZECIW: "
        f"{assessment.opposing_evidence}"
    )
    print(
        f"SPRZECZNOŚĆ: "
        f"{assessment.contradiction_detected}"
    )
    print(
        f"POTRZEBA WIĘCEJ DOWODÓW: "
        f"{assessment.requires_more_evidence}"
    )
    print(
        f"UZASADNIENIE: "
        f"{assessment.explanation}"
    )


# ---------------------------------------------------------
# TEST 1
# Twierdzenie bez żadnych dowodów
# ---------------------------------------------------------

claim_1 = Claim(
    content="Jutro będzie padał deszcz.",
    knowledge_type=KnowledgeType.HYPOTHESIS,
    source="test",
    source_type=SourceType.USER,
)

feniks.register_claim(claim_1)

assessment_1 = feniks.assess_claim(claim_1)

show_assessment(1, assessment_1)


# ---------------------------------------------------------
# TEST 2
# Twierdzenie posiadające mocne poparcie
# ---------------------------------------------------------

claim_2 = Claim(
    content="Testowy moduł Truth Engine został uruchomiony.",
    knowledge_type=KnowledgeType.HYPOTHESIS,
    source="FENIKS",
    source_type=SourceType.SYSTEM,
)

feniks.register_claim(claim_2)

feniks.add_evidence(
    claim_2,
    Evidence(
        description=(
            "Program wykonuje kod Truth Engine "
            "i zwraca wynik jego analizy."
        ),
        source="runtime",
        source_type=SourceType.SYSTEM,
        reliability=0.98,
        supports_claim=True,
    ),
)

feniks.add_evidence(
    claim_2,
    Evidence(
        description=(
            "Instancja TruthEngine istnieje "
            "w działającym rdzeniu FENIKSA."
        ),
        source="runtime",
        source_type=SourceType.SYSTEM,
        reliability=0.95,
        supports_claim=True,
    ),
)

assessment_2 = feniks.assess_claim(claim_2)

show_assessment(2, assessment_2)


# ---------------------------------------------------------
# TEST 3
# Dowody wzajemnie sprzeczne
# ---------------------------------------------------------

claim_3 = Claim(
    content="Eksperymentalny czujnik wykrył obiekt.",
    knowledge_type=KnowledgeType.HYPOTHESIS,
    source="test",
    source_type=SourceType.SENSOR,
)

feniks.register_claim(claim_3)

feniks.add_evidence(
    claim_3,
    Evidence(
        description="Czujnik A zgłosił wykrycie obiektu.",
        source="sensor_A",
        source_type=SourceType.SENSOR,
        reliability=0.90,
        supports_claim=True,
    ),
)

feniks.add_evidence(
    claim_3,
    Evidence(
        description="Czujnik B nie potwierdził obecności obiektu.",
        source="sensor_B",
        source_type=SourceType.SENSOR,
        reliability=0.85,
        supports_claim=False,
    ),
)

assessment_3 = feniks.assess_claim(claim_3)

show_assessment(3, assessment_3)


print("\n" + "=" * 60)
print("STAN FENIKSA")

for key, value in feniks.status().items():
    print(f"- {key}: {value}")