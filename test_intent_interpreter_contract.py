# -*- coding: utf-8 -*-

import json
import os

from google.genai.errors import ServerError

from communication.intent import (
    IntentExecutionState,
    IntentInterpreter,
)
from infrastructure.model_gateway import ModelGateway
from perception.perception import PerceptionEngine
from senses.text import TextSense


# Test kontraktu nie powinien zależeć od prawdziwego klucza API.
os.environ.setdefault("GEMINI_API_KEY", "test-contract-key")


def check(description: str, condition: bool) -> None:
    print(
        f"{description}: "
        f"{'TAK' if condition else 'NIE'}"
    )

    if not condition:
        raise AssertionError(description)


def server_error(code: int, message: str) -> ServerError:
    return ServerError(
        code,
        {
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


def build_perception():
    raw = (
        "Aurel, kurde, powiedz mi co my właściwie teraz "
        "budujemy, bo nie chcę zrobić z FENIKSA "
        "kolejnego głupiego chatbota."
    )

    event = TextSense().receive(raw)

    return PerceptionEngine().perceive(event)


def valid_analysis_json() -> str:
    """
    Buduje prawidłowy JSON testowy.

    Nie składamy JSON-u ręcznie jako wieloliniowego tekstu,
    ponieważ test ma sprawdzać kontrakt IntentInterpreter,
    a nie przypadkowe błędy składni ręcznie pisanego JSON-u.

    json.dumps gwarantuje poprawną składnię JSON.
    ensure_ascii=False zachowuje polskie znaki w UTF-8.
    """

    payload = {
        "interpretation": (
            "Użytkownik prawdopodobnie chce doprecyzować "
            "kierunek rozwoju FENIKSA."
        ),
        "confidence": 0.88,
        "evidence": [
            "Użytkownik pyta, co obecnie jest budowane.",
            (
                "Użytkownik mówi, że nie chce kolejnego "
                "głupiego chatbota."
            ),
        ],
        "alternatives": [
            (
                "Użytkownik może również wyrażać sprzeciw "
                "wobec aktualnego kierunku prac."
            ),
        ],
        "uncertainty": (
            "Nie można bezpośrednio obserwować intencji "
            "człowieka."
        ),
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
    )


class ControlledIntentInterpreter(IntentInterpreter):
    """
    Interpreter testowy.

    Nie wykonuje prawdziwych wywołań Gemini.

    Pozwala dokładnie kontrolować zachowanie modeli,
    zachowując prawdziwy IntentInterpreter
    i prawdziwy ModelGateway.
    """

    def __init__(
        self,
        behavior,
        gateway=None,
    ) -> None:
        super().__init__(
            model="primary",
            fallback_model="fallback",
            gateway=gateway or ModelGateway(),
        )

        self.behavior = behavior
        self.model_calls = []

    def _generate(
        self,
        model: str,
        prompt: str,
    ) -> str:
        self.model_calls.append(model)

        return self.behavior(
            model,
            prompt,
        )


def print_header(title: str) -> None:
    print()
    print(title)
    print("-" * 90)


def test_primary_success(perception) -> None:
    print_header(
        "TEST 1 - PRIMARY SUCCESS"
    )

    gateway = ModelGateway()

    def behavior(model, prompt):
        return valid_analysis_json()

    interpreter = ControlledIntentInterpreter(
        behavior=behavior,
        gateway=gateway,
    )

    result = interpreter.interpret(
        perception
    )

    check(
        "Interpretacja została wykonana",
        result.interpreted,
    )

    check(
        "Stan to INTERPRETED",
        result.state
        is IntentExecutionState.INTERPRETED,
    )

    check(
        "Powstała hipoteza intencji",
        result.hypothesis is not None,
    )

    check(
        "Hipoteza nadal jest hipotezą",
        (
            result.hypothesis is not None
            and result.hypothesis.is_hypothesis
        ),
    )

    check(
        "Użyto primary",
        result.model_used == "primary",
    )

    check(
        "Fallback nie został użyty",
        not result.fallback_used,
    )

    check(
        "Wykonano jedno wywołanie modelu",
        interpreter.model_calls
        == ["primary"],
    )

    check(
        "Licznik prób wzrósł",
        interpreter.attempt_count == 1,
    )

    check(
        "Licznik wykonanych analiz wzrósł",
        interpreter.analysis_count == 1,
    )

    check(
        "Gateway policzył jedno wywołanie",
        gateway.stats()["liczba_wywolan"]
        == 1,
    )


def test_primary_503_fallback_success(
    perception,
) -> None:
    print_header(
        "TEST 2 - PRIMARY 503 -> FALLBACK SUCCESS"
    )

    gateway = ModelGateway()

    def behavior(model, prompt):
        if model == "primary":
            raise server_error(
                503,
                "Primary chwilowo niedostępny.",
            )

        return valid_analysis_json()

    interpreter = ControlledIntentInterpreter(
        behavior=behavior,
        gateway=gateway,
    )

    result = interpreter.interpret(
        perception
    )

    check(
        "Interpretacja została wykonana",
        result.interpreted,
    )

    check(
        "Powstała hipoteza intencji",
        result.hypothesis is not None,
    )

    check(
        "Użyto fallback",
        result.model_used == "fallback",
    )

    check(
        "Fallback został jawnie zapisany",
        result.fallback_used,
    )

    check(
        "Zachowano błąd primary",
        bool(result.primary_error),
    )

    check(
        "Brak błędu fallback",
        result.fallback_error is None,
    )

    check(
        "Kolejność modeli jest prawidłowa",
        interpreter.model_calls
        == ["primary", "fallback"],
    )

    check(
        "Wykonana analiza została policzona",
        interpreter.analysis_count == 1,
    )

    check(
        "Gateway policzył fallback",
        gateway.stats()["liczba_fallbackow"]
        == 1,
    )


def test_both_503(perception) -> None:
    print_header(
        "TEST 3 - PRIMARY 503 -> FALLBACK 503"
    )

    gateway = ModelGateway()

    def behavior(model, prompt):
        raise server_error(
            503,
            f"Model {model} chwilowo niedostępny.",
        )

    interpreter = ControlledIntentInterpreter(
        behavior=behavior,
        gateway=gateway,
    )

    result = interpreter.interpret(
        perception
    )

    check(
        "Stan to UNAVAILABLE",
        result.state
        is IntentExecutionState.UNAVAILABLE,
    )

    check(
        "Właściwość unavailable jest prawdziwa",
        result.unavailable,
    )

    check(
        "Interpretacja nie została wykonana",
        not result.interpreted,
    )

    check(
        "Nie powstała hipoteza intencji",
        result.hypothesis is None,
    )

    check(
        "Nie wskazano skutecznie użytego modelu",
        result.model_used is None,
    )

    check(
        "Zapisano próbę fallbacku",
        result.fallback_used,
    )

    check(
        "Zachowano błąd primary",
        bool(result.primary_error),
    )

    check(
        "Zachowano błąd fallback",
        bool(result.fallback_error),
    )

    check(
        "Próbowano obu modeli",
        interpreter.model_calls
        == ["primary", "fallback"],
    )

    check(
        "Próba interpretacji została policzona",
        interpreter.attempt_count == 1,
    )

    check(
        "Niewykonana analiza nie została policzona",
        interpreter.analysis_count == 0,
    )

    check(
        "Gateway odnotował niedostępność",
        gateway.stats()[
            "liczba_niedostepnosci"
        ]
        == 1,
    )


def test_non_503_error(perception) -> None:
    print_header(
        "TEST 4 - BŁĄD INNY NIŻ 503"
    )

    gateway = ModelGateway()

    def behavior(model, prompt):
        raise server_error(
            500,
            "Kontrolowany błąd testowy.",
        )

    interpreter = ControlledIntentInterpreter(
        behavior=behavior,
        gateway=gateway,
    )

    propagated = False

    try:
        interpreter.interpret(
            perception
        )

    except ServerError as error:
        propagated = error.code == 500

    check(
        "Błąd został propagowany",
        propagated,
    )

    check(
        "Fallback nie maskował innego błędu",
        interpreter.model_calls
        == ["primary"],
    )

    check(
        "Próba została policzona",
        interpreter.attempt_count == 1,
    )

    check(
        "Nie zapisano wykonanej analizy",
        interpreter.analysis_count == 0,
    )

    check(
        "Gateway nie policzył fallbacku",
        gateway.stats()["liczba_fallbackow"]
        == 0,
    )


def main() -> None:
    print("=" * 90)

    print(
        "PEŁNY TEST KONTRAKTU INTENTINTERPRETER"
    )

    print("=" * 90)

    perception = build_perception()

    test_primary_success(
        perception
    )

    test_primary_503_fallback_success(
        perception
    )

    test_both_503(
        perception
    )

    test_non_503_error(
        perception
    )

    print()
    print("=" * 90)

    print(
        "WERDYKT: INTENTINTERPRETER ODDZIELA "
        "HIPOTEZĘ INTENCJI OD STANU INFRASTRUKTURY"
    )

    print("=" * 90)

    print(
        "Niedostępność modeli nie tworzy fałszywej "
        "hipotezy intencji człowieka."
    )


if __name__ == "__main__":
    main()