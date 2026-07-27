import os
from core.reasoning_provider import GeminiReasoningProvider, ReasoningMode


def check(label, value):
    print(f"{label}: {'TAK' if value else 'NIE'}")
    if not value:
        raise AssertionError(label)


def main():
    print("=" * 90)
    print("TEST PRODUKCYJNEGO GEMINI REASONING PROVIDER FENIKSA")
    print("=" * 90)

    provider = GeminiReasoningProvider()

    result = provider.analyze(
        title="Czy wcześniejsza wiedza może zastąpić bieżące dowody?",
        description=(
            "FENIKS ma ocenić problem bez przyjmowania historii "
            "jako automatycznego dowodu."
        ),
        evidence=[
            "Bieżące dane nie zawierają wyniku eksperymentu rozstrzygającego problem."
        ],
        unknowns=[
            "Nie wiadomo jeszcze, jaki będzie wynik kontrolowanego eksperymentu."
        ],
        history=[
            "Wcześniejszy rekord sugerował określony wynik, ale jest tylko kontekstem."
        ],
        mode=ReasoningMode.DIAGNOSIS,
    )

    print("Model podstawowy:", provider.model)
    print("Model zapasowy:", provider.fallback_model)
    print("Model faktycznie użyty:", provider.last_model_used)
    print("Fallback:", "TAK" if provider.last_fallback_used else "NIE")

    if provider.last_primary_error:
        print("Błąd modelu podstawowego:", provider.last_primary_error[:220])

    check(
        "Faktycznie użyty model jest znany",
        provider.last_model_used in {provider.model, provider.fallback_model},
    )
    check(
        "Pewność mieści się w zakresie 0-1",
        0.0 <= result.confidence <= 1.0,
    )
    check(
        "Provider zachował niewiadome lub granice wnioskowania",
        bool(result.unknowns or result.cannot_conclude_yet),
    )
    check(
        "Provider zwrócił kryterium rozstrzygnięcia",
        bool(result.conclusion_rule.strip()),
    )

    if provider.last_fallback_used:
        check(
            "Fallback użył modelu zapasowego",
            provider.last_model_used == provider.fallback_model,
        )
        check(
            "Zachowano przyczynę awarii modelu podstawowego",
            bool(provider.last_primary_error),
        )

    print("=" * 90)
    print("WERDYKT: PRODUKCYJNY REASONING PROVIDER DZIAŁA")
    print("=" * 90)


if __name__ == "__main__":
    main()
