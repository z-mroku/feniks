from google.genai.errors import ServerError

from model_of_others.intent_hypothesis import IntentHypothesis
from perception.perception import PerceptionEngine
from perception.reality_check import (
    EvidenceStatus,
    RealityCheck,
    RealityCheckExecutionState,
)
from senses.text import TextSense


def check(label: str, condition: bool) -> None:
    status = "TAK" if condition else "NIE"
    print(f"{label}: {status}")

    if not condition:
        raise AssertionError(label)


def server_error(code: int) -> ServerError:
    return ServerError(
        code,
        {
            "error": {
                "code": code,
                "message": f"TESTOWY BŁĄD {code}",
            }
        },
    )


def make_input():
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
            "Nie znamy bezpośrednio wewnętrznej intencji "
            "człowieka."
        ),
    )

    return perception, hypothesis


def valid_response() -> str:
    return """
{
  "assessments": [
    {
      "evidence": "Użytkownik pyta, co właściwie teraz budujemy.",
      "status": "UGRUNTOWANE",
      "explanation": "Treść pytania znajduje się bezpośrednio w wypowiedzi.",
      "confidence": 1.0
    },
    {
      "evidence": "Użytkownik mówi, że nie chce zrobić z FENIKSA kolejnego głupiego chatbota.",
      "status": "UGRUNTOWANE",
      "explanation": "Treść została wyrażona bezpośrednio przez użytkownika.",
      "confidence": 1.0
    }
  ]
}
"""


def test_primary_success() -> None:
    perception, hypothesis = make_input()

    reality = RealityCheck(
        model="primary",
        fallback_model="fallback",
    )

    calls = []

    def generate(model: str, prompt: str) -> str:
        calls.append(model)
        return valid_response()

    reality._generate = generate

    execution = reality.check(
        perception,
        hypothesis,
    )

    print()
    print("TEST 1 - PRIMARY SUCCESS")
    print("-" * 90)

    check(
        "Kontrola została wykonana",
        execution.state
        is RealityCheckExecutionState.CHECKED,
    )

    check(
        "Powstał wynik poznawczy",
        execution.result is not None,
    )

    check(
        "Użyto primary",
        execution.model_used == "primary",
    )

    check(
        "Fallback nie został użyty",
        not execution.fallback_used,
    )

    check(
        "Wykonano jedno wywołanie modelu",
        calls == ["primary"],
    )

    check(
        "Obie przesłanki zostały ocenione",
        len(execution.result.evidence) == 2,
    )

    check(
        "Status przesłanki jest prawidłowym enumem",
        execution.result.evidence[0].status
        is EvidenceStatus.GROUNDED,
    )

    check(
        "Licznik kontroli wzrósł",
        reality.stats()["liczba_kontroli"] == 1,
    )


def test_fallback_success() -> None:
    perception, hypothesis = make_input()

    reality = RealityCheck(
        model="primary",
        fallback_model="fallback",
    )

    calls = []

    def generate(model: str, prompt: str) -> str:
        calls.append(model)

        if model == "primary":
            raise server_error(503)

        return valid_response()

    reality._generate = generate

    execution = reality.check(
        perception,
        hypothesis,
    )

    print()
    print("TEST 2 - PRIMARY 503 -> FALLBACK SUCCESS")
    print("-" * 90)

    check(
        "Kontrola została wykonana",
        execution.checked,
    )

    check(
        "Powstał wynik poznawczy",
        execution.result is not None,
    )

    check(
        "Użyto fallback",
        execution.model_used == "fallback",
    )

    check(
        "Fallback został jawnie zapisany",
        execution.fallback_used,
    )

    check(
        "Zachowano błąd primary",
        bool(execution.primary_error),
    )

    check(
        "Brak błędu fallback",
        execution.fallback_error is None,
    )

    check(
        "Kolejność modeli jest prawidłowa",
        calls == ["primary", "fallback"],
    )

    check(
        "Kontrola została policzona",
        reality.stats()["liczba_kontroli"] == 1,
    )


def test_both_unavailable() -> None:
    perception, hypothesis = make_input()

    reality = RealityCheck(
        model="primary",
        fallback_model="fallback",
    )

    calls = []

    def generate(model: str, prompt: str) -> str:
        calls.append(model)
        raise server_error(503)

    reality._generate = generate

    execution = reality.check(
        perception,
        hypothesis,
    )

    print()
    print("TEST 3 - PRIMARY 503 -> FALLBACK 503")
    print("-" * 90)

    check(
        "Stan to UNAVAILABLE",
        execution.unavailable,
    )

    check(
        "Nie powstał wynik poznawczy",
        execution.result is None,
    )

    check(
        "Nie udawano skutecznie użytego modelu",
        execution.model_used is None,
    )

    check(
        "Zachowano błąd primary",
        bool(execution.primary_error),
    )

    check(
        "Zachowano błąd fallback",
        bool(execution.fallback_error),
    )

    check(
        "Próbowano obu modeli",
        calls == ["primary", "fallback"],
    )

    check(
        "Próba została policzona",
        reality.stats()["liczba_prob"] == 1,
    )

    check(
        "Niewykonana kontrola nie została policzona",
        reality.stats()["liczba_kontroli"] == 0,
    )


def test_non_503_propagates() -> None:
    perception, hypothesis = make_input()

    reality = RealityCheck(
        model="primary",
        fallback_model="fallback",
    )

    calls = []

    def generate(model: str, prompt: str) -> str:
        calls.append(model)
        raise server_error(500)

    reality._generate = generate

    propagated = False

    try:
        reality.check(
            perception,
            hypothesis,
        )
    except ServerError as exc:
        propagated = exc.code == 500

    print()
    print("TEST 4 - BŁĄD INNY NIŻ 503")
    print("-" * 90)

    check(
        "Błąd został propagowany",
        propagated,
    )

    check(
        "Fallback nie maskował innego błędu",
        calls == ["primary"],
    )

    check(
        "Nie zapisano wykonanej kontroli",
        reality.stats()["liczba_kontroli"] == 0,
    )


def main() -> None:
    print("=" * 90)
    print("PEŁNY TEST KONTRAKTU REALITYCHECK")
    print("=" * 90)

    test_primary_success()
    test_fallback_success()
    test_both_unavailable()
    test_non_503_propagates()

    print()
    print("=" * 90)
    print(
        "WERDYKT: REALITYCHECK ROZRÓŻNIA WYNIK POZNAWCZY "
        "OD STANU INFRASTRUKTURY"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()