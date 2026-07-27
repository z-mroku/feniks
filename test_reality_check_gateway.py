from google.genai.errors import ServerError

from model_of_others.intent_hypothesis import IntentHypothesis
from perception.perception import PerceptionEngine
from perception.reality_check import (
    RealityCheck,
    RealityCheckExecutionState,
)
from senses.text import TextSense


def check(label: str, condition: bool) -> None:
    status = "TAK" if condition else "NIE"
    print(f"{label}: {status}")

    if not condition:
        raise AssertionError(label)


def make_server_error() -> ServerError:
    return ServerError(
        503,
        {
            "error": {
                "code": 503,
                "message": "TESTOWA NIEDOSTĘPNOŚĆ MODELU",
                "status": "UNAVAILABLE",
            }
        },
    )


def main() -> None:
    print("=" * 90)
    print("TEST REALITYCHECK -> MODELGATEWAY -> KONTROLOWANE UNAVAILABLE")
    print("=" * 90)

    raw = (
        "Aurel, kurde, powiedz mi co my właściwie teraz "
        "budujemy, bo nie chcę zrobić z FENIKSA "
        "kolejnego głupiego chatbota"
    )

    perception = PerceptionEngine().perceive(
        TextSense().receive(raw)
    )

    hypothesis = IntentHypothesis(
        interpretation=(
            "Użytkownik prawdopodobnie chce doprecyzować "
            "kierunek rozwoju FENIKSA."
        ),
        confidence=0.85,
        evidence=(
            "Użytkownik pyta, co właściwie teraz budujemy.",
            "Użytkownik mówi, że nie chce zrobić z FENIKSA "
            "kolejnego głupiego chatbota.",
        ),
        alternatives=(
            "Użytkownik może kwestionować aktualny "
            "kierunek prac.",
        ),
        uncertainty=(
            "Sama wypowiedź nie daje bezpośredniego "
            "dostępu do wewnętrznej intencji człowieka."
        ),
    )

    reality_check = RealityCheck(
        model="test-primary",
        fallback_model="test-fallback",
    )

    attempted_models: list[str] = []

    def always_unavailable(
        model: str,
        prompt: str,
    ) -> str:
        attempted_models.append(model)
        raise make_server_error()

    # Zastępujemy wyłącznie transport do modelu.
    # Cała logika RealityCheck i ModelGateway pozostaje
    # rzeczywiście wykonywana.
    reality_check._generate = always_unavailable

    execution = reality_check.check(
        perception=perception,
        hypothesis=hypothesis,
    )

    print()
    print("ETAP 1 - DROGA WYKONANIA")
    print("-" * 90)

    check(
        "Najpierw użyto modelu podstawowego",
        attempted_models
        and attempted_models[0] == "test-primary",
    )

    check(
        "Po 503 użyto modelu zapasowego",
        attempted_models == [
            "test-primary",
            "test-fallback",
        ],
    )

    check(
        "Wykonano dokładnie dwie próby modelowe",
        len(attempted_models) == 2,
    )

    print()
    print("ETAP 2 - BRAK FAŁSZYWEGO WYNIKU POZNAWCZEGO")
    print("-" * 90)

    check(
        "Stan wykonania to UNAVAILABLE",
        execution.state
        is RealityCheckExecutionState.UNAVAILABLE,
    )

    check(
        "Właściwość unavailable jest prawdziwa",
        execution.unavailable,
    )

    check(
        "Właściwość checked jest fałszywa",
        not execution.checked,
    )

    check(
        "Nie powstał RealityCheckResult",
        execution.result is None,
    )

    check(
        "Nie wskazano modelu jako skutecznie użytego",
        execution.model_used is None,
    )

    print()
    print("ETAP 3 - AUDYT AWARII")
    print("-" * 90)

    check(
        "Zapisano użycie fallbacku",
        execution.fallback_used,
    )

    check(
        "Zachowano błąd modelu podstawowego",
        bool(execution.primary_error),
    )

    check(
        "Zachowano błąd modelu zapasowego",
        bool(execution.fallback_error),
    )

    check(
        "RealityCheck pamięta błąd primary",
        bool(reality_check.last_primary_error),
    )

    check(
        "RealityCheck pamięta błąd fallback",
        bool(reality_check.last_fallback_error),
    )

    print()
    print("ETAP 4 - UCZCIWOŚĆ LICZNIKÓW")
    print("-" * 90)

    stats = reality_check.stats()

    check(
        "Odnotowano jedną próbę kontroli",
        stats["liczba_prob"] == 1,
    )

    check(
        "Nie odnotowano wykonanej kontroli",
        stats["liczba_kontroli"] == 0,
    )

    check(
        "Gateway odnotował jedno wywołanie",
        stats["gateway"]["liczba_wywolan"] == 1,
    )

    check(
        "Gateway odnotował próbę fallbacku",
        stats["gateway"]["liczba_fallbackow"] == 1,
    )

    check(
        "Gateway odnotował niedostępność",
        stats["gateway"]["liczba_niedostepnosci"] == 1,
    )

    print()
    print("=" * 90)
    print(
        "WERDYKT: AWARIA PRIMARY + FALLBACK NIE TWORZY "
        "FAŁSZYWEGO WYNIKU REALITYCHECK"
    )
    print("=" * 90)
    print(
        "FENIKS wie, że kontroli nie przeprowadzono. "
        "Nie myli niedostępności infrastruktury "
        "z wiedzą o rzeczywistości."
    )


if __name__ == "__main__":
    main()