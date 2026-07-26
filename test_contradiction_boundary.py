import sys
from pathlib import Path


# ============================================================
# ŚCIEŻKA PROJEKTU
# ============================================================

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ============================================================
# IMPORTY FENIKSA
# ============================================================

from core.truth_engine import (
    Claim,
    Evidence,
    KnowledgeType,
    SourceType,
    TruthEngine,
)


# ============================================================
# KONFIGURACJA EKSPERYMENTU
# ============================================================

SUPPORT_RELIABILITY = 0.95

OPPOSITION_RELIABILITIES = [
    0.0,
    0.1,
    0.01,
    0.001,
    0.0001,
    0.00001,
    0.000001,
    0.0000001,
    0.00000001,
]


# ============================================================
# POMOCNICZE TWORZENIE TWIERDZENIA
# ============================================================

def new_claim() -> Claim:
    return Claim(
        content=(
            "Kontrolne twierdzenie eksperymentu "
            "granicy sprzeczności."
        ),
        knowledge_type=KnowledgeType.UNKNOWN,
        source="ContradictionBoundaryExperiment",
        source_type=SourceType.SYSTEM,
    )


# ============================================================
# POMOCNICZE TWORZENIE DOWODU
# ============================================================

def new_evidence(
    reliability: float,
    supports: bool,
    name: str,
) -> Evidence:
    return Evidence(
        description=name,
        source="ContradictionBoundaryExperiment",
        source_type=SourceType.SYSTEM,
        reliability=reliability,
        supports_claim=supports,
    )


# ============================================================
# POJEDYNCZA PRÓBA
# ============================================================

def run_trial(
    opposition_reliability: float,
) -> dict:
    engine = TruthEngine()

    claim = new_claim()

    engine.add_evidence(
        claim,
        new_evidence(
            reliability=SUPPORT_RELIABILITY,
            supports=True,
            name="Mocny dowód wspierający",
        ),
    )

    engine.add_evidence(
        claim,
        new_evidence(
            reliability=opposition_reliability,
            supports=False,
            name="Kontrolowany dowód przeciwny",
        ),
    )

    result = engine.assess(claim)

    return {
        "input_reliability": opposition_reliability,
        "classification": result.classification.value,
        "support_strength": result.support_strength,
        "opposition_strength": result.opposition_strength,
        "confidence": result.classification_confidence,
        "contradiction": result.contradiction_detected,
        "supporting_evidence": result.supporting_evidence,
        "opposing_evidence": result.opposing_evidence,
    }


# ============================================================
# GŁÓWNY EKSPERYMENT
# ============================================================

def main():
    print("=" * 86)
    print("EKSPERYMENT GRANICZNY SPRZECZNOŚCI FENIKSA")
    print("=" * 86)

    print()
    print("PYTANIE BADAWCZE:")
    print(
        "Czy obecny TruthEngine wykrywa SPRZECZNOŚĆ "
        "dla dowolnie małych PRZEBADANYCH dodatnich "
        "wartości wiarygodności dowodu przeciwnego?"
    )

    print()
    print("WARUNKI:")
    print(
        f"- wiarygodność dowodu wspierającego: "
        f"{SUPPORT_RELIABILITY}"
    )
    print(
        "- dokładnie jeden dowód wspierający"
    )
    print(
        "- dokładnie jeden dowód przeciwny"
    )
    print(
        "- zmieniana jest wyłącznie wiarygodność "
        "dowodu przeciwnego"
    )

    results = []

    for reliability in OPPOSITION_RELIABILITIES:
        results.append(
            run_trial(reliability)
        )

    # ========================================================
    # TABELA OBSERWACJI
    # ========================================================

    print()
    print("=" * 86)
    print("RZECZYWISTE OBSERWACJE TRUTHENGINE")
    print("=" * 86)

    header = (
        f"{'WEJŚCIE':>12} | "
        f"{'KLASYFIKACJA':<16} | "
        f"{'ZA':>9} | "
        f"{'PRZECIW':>9} | "
        f"{'PEWNOŚĆ':>9} | "
        f"{'SPRZECZNOŚĆ':<12}"
    )

    print(header)
    print("-" * len(header))

    for result in results:
        print(
            f"{result['input_reliability']:>12.8f} | "
            f"{result['classification']:<16} | "
            f"{result['support_strength']:>9.6f} | "
            f"{result['opposition_strength']:>9.6f} | "
            f"{result['confidence']:>9.6f} | "
            f"{'TAK' if result['contradiction'] else 'NIE':<12}"
        )

    # ========================================================
    # ANALIZA DETERMINISTYCZNA
    # ========================================================

    zero_result = next(
        result
        for result in results
        if result["input_reliability"] == 0.0
    )

    positive_results = [
        result
        for result in results
        if result["input_reliability"] > 0.0
    ]

    positive_with_contradiction = [
        result
        for result in positive_results
        if result["contradiction"]
    ]

    positive_without_contradiction = [
        result
        for result in positive_results
        if not result["contradiction"]
    ]

    smallest_tested_positive = min(
        result["input_reliability"]
        for result in positive_results
    )

    smallest_tested_positive_result = next(
        result
        for result in positive_results
        if (
            result["input_reliability"]
            == smallest_tested_positive
        )
    )

    all_positive_triggered = (
        len(positive_without_contradiction) == 0
    )

    zero_triggered = zero_result["contradiction"]

    # ========================================================
    # USTALENIA
    # ========================================================

    print()
    print("=" * 86)
    print("USTALENIA EKSPERYMENTALNE")
    print("=" * 86)

    print()
    print(
        "SPRZECZNOŚĆ DLA WIARYGODNOŚCI 0.0:",
        "TAK" if zero_triggered else "NIE",
    )

    print(
        "WSZYSTKIE PRZEBADANE DODATNIE WARTOŚCI "
        "WYWOŁAŁY SPRZECZNOŚĆ:",
        "TAK" if all_positive_triggered else "NIE",
    )

    print(
        "NAJMNIEJSZA PRZEBADANA DODATNIA "
        "WIARYGODNOŚĆ:",
        smallest_tested_positive,
    )

    print(
        "SPRZECZNOŚĆ DLA NAJMNIEJSZEJ "
        "PRZEBADANEJ WARTOŚCI:",
        (
            "TAK"
            if smallest_tested_positive_result[
                "contradiction"
            ]
            else "NIE"
        ),
    )

    print(
        "SIŁA SPRZECIWU DLA NAJMNIEJSZEJ "
        "PRZEBADANEJ WARTOŚCI:",
        smallest_tested_positive_result[
            "opposition_strength"
        ],
    )

    # ========================================================
    # UCZCIWA INTERPRETACJA
    # ========================================================

    print()
    print("=" * 86)
    print("GRANICA TEGO, CO WOLNO UZNAĆ ZA FAKT")
    print("=" * 86)

    print()

    if all_positive_triggered:
        print(
            "FAKT:"
        )
        print(
            "W tym eksperymencie każda PRZEBADANA "
            "dodatnia wartość wiarygodności dowodu "
            "przeciwnego wywołała SPRZECZNOŚĆ."
        )

        print()
        print(
            "Najmniejsza przebadana dodatnia wartość "
            f"wynosiła {smallest_tested_positive}."
        )

    else:
        print(
            "FAKT:"
        )
        print(
            "Nie wszystkie przebadane dodatnie "
            "wartości wiarygodności dowodu przeciwnego "
            "wywołały SPRZECZNOŚĆ."
        )

        print()
        print(
            "Wartości bez wykrytej sprzeczności:"
        )

        for result in positive_without_contradiction:
            print(
                "-",
                result["input_reliability"],
            )

    print()
    print(
        "NIE WOLNO JESZCZE UZNAĆ ZA FAKT:"
    )

    print(
        "Każda matematycznie możliwa wartość "
        "wiarygodności większa od zera zawsze "
        "wywołuje SPRZECZNOŚĆ."
    )

    print()
    print(
        "Powód: eksperyment sprawdza skończony zbiór "
        "wartości, a nie wszystkie liczby rzeczywiste "
        "większe od zera."
    )

    # ========================================================
    # DODATKOWA KONTROLA SEMANTYKI ZERA
    # ========================================================

    print()
    print("=" * 86)
    print("KONTROLA SZCZEGÓLNEGO PRZYPADKU 0.0")
    print("=" * 86)

    print()
    print(
        "DOWÓD PRZECIWNY ZOSTAŁ DODANY DO SILNIKA:",
        (
            "TAK"
            if zero_result["opposing_evidence"] >= 1
            else "NIE"
        ),
    )

    print(
        "JEGO WIARYGODNOŚĆ:",
        zero_result["input_reliability"],
    )

    print(
        "ZMierzona SIŁA SPRZECIWU:",
        zero_result["opposition_strength"],
    )

    print(
        "SPRZECZNOŚĆ:",
        "TAK" if zero_result["contradiction"] else "NIE",
    )

    print()
    print(
        "Ten przypadek jest ważny, ponieważ pozwala "
        "odróżnić samą OBECNOŚĆ obiektu Evidence "
        "od dodatniej siły dowodu."
    )

    # ========================================================
    # WERDYKT
    # ========================================================

    print()
    print("=" * 86)

    if (
        all_positive_triggered
        and not zero_triggered
    ):
        print(
            "WERDYKT: W BADANYM ZAKRESIE GRANICA "
            "SPRZECZNOŚCI LEŻY POMIĘDZY 0.0 "
            "A NAJMNIEJSZĄ PRZEBADANĄ DODATNIĄ "
            "WARTOŚCIĄ."
        )

    elif (
        all_positive_triggered
        and zero_triggered
    ):
        print(
            "WERDYKT: TRUTHENGINE WYKRYWA "
            "SPRZECZNOŚĆ NAWET DLA DOWODU "
            "PRZECIWNEGO O WIARYGODNOŚCI 0.0."
        )

    else:
        print(
            "WERDYKT: EKSPERYMENT UJAWNIŁ "
            "GRANICĘ LUB NIEJEDNOLITE ZACHOWANIE, "
            "KTÓRE WYMAGA DALSZEGO BADANIA."
        )

    print("=" * 86)


if __name__ == "__main__":
    main()