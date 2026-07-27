from core.experiment_interpreter import GeminiExperimentInterpreter
from google.genai.errors import ServerError


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self):
        self.calls = []

    def generate_content(self, model, contents, config):
        self.calls.append(model)

        if model == "gemini-3.5-flash":
            raise ServerError(
                503,
                {
                    "error": {
                        "code": 503,
                        "message": "Temporary overload",
                        "status": "UNAVAILABLE",
                    }
                },
                None,
            )

        return FakeResponse(
            """{
              "hypothesis_status":"OBALONA",
              "reasoning":"Bieżące dane nie potwierdzają hipotezy.",
              "new_findings":["Ustalenie testowe."],
              "remaining_unknowns":[],
              "alternative_explanations":[],
              "next_experiment_question":"Co zbadać dalej?",
              "next_experiment":"Wykonać następny eksperyment.",
              "cannot_conclude_yet":["Nie ustalono przyczyny."],
              "confidence":0.9
            }"""
        )


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


class DummyResult:
    name = "fallback_test"
    observations = []
    first_contradiction_at = None
    first_opposition_stronger_at = None
    maximum_n_tested = 0


def check(label, condition, failures):
    ok = bool(condition)
    print(f"{label}: {'TAK' if ok else 'NIE'}")
    if not ok:
        failures.append(label)


def main():
    failures = []
    print("=" * 90)
    print("TEST KONTROLOWANEGO FALLBACKU GEMINI W FENIKSIE")
    print("=" * 90)

    interpreter = GeminiExperimentInterpreter(
        model="gemini-3.5-flash",
        fallback_model="gemini-3.6-flash",
    )
    interpreter.client = FakeClient()

    result = interpreter.interpret(
        hypothesis="Hipoteza testowa",
        result=DummyResult(),
    )

    calls = interpreter.client.models.calls

    check("Najpierw użyto modelu podstawowego",
          calls[0] == "gemini-3.5-flash", failures)
    check("Po 503 użyto modelu zapasowego",
          calls == ["gemini-3.5-flash", "gemini-3.6-flash"], failures)
    check("Fallback został jawnie odnotowany",
          interpreter.last_fallback_used is True, failures)
    check("Zapamiętano faktycznie użyty model",
          interpreter.last_model_used == "gemini-3.6-flash", failures)
    check("Zachowano błąd modelu podstawowego",
          bool(interpreter.last_primary_error), failures)
    check("Odpowiedź fallbacku przeszła walidację",
          result.hypothesis_status.value == "OBALONA", failures)

    print("=" * 90)
    if failures:
        print("WERDYKT: FALLBACK NIE DZIAŁA POPRAWNIE")
        for item in failures:
            print("-", item)
        raise SystemExit(1)

    print("WERDYKT: KONTROLOWANY FALLBACK 3.5 -> 3.6 DZIAŁA")
    print("=" * 90)


if __name__ == "__main__":
    main()
