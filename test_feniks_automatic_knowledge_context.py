from core.cognitive_cycle import CognitiveCycle
from core.experiment_interpreter import ExperimentInterpretation, HypothesisStatus
from core.feniks import Feniks

class OldStyleInterpreter:
    def interpret(self, hypothesis, result):
        return ExperimentInterpretation(
            hypothesis_status=HypothesisStatus.REJECTED,
            reasoning="Kontrolowana interpretacja.",
            new_findings=["Ustalenie testowe."],
            remaining_unknowns=[],
            alternative_explanations=[],
            next_experiment_question="Co dalej?",
            next_experiment="Następny test.",
            cannot_conclude_yet=[],
            confidence=0.9,
        )

class ContextAwareInterpreter(OldStyleInterpreter):
    supports_prior_knowledge_context = True
    def __init__(self):
        self.received_context = None
    def interpret(self, hypothesis, result, prior_knowledge_context=""):
        self.received_context = prior_knowledge_context
        return super().interpret(hypothesis, result)

class FakeRecord: pass
class FakeContext:
    def __init__(self, text):
        self.records = (FakeRecord(),)
        self.text = text
    def as_text(self):
        return self.text
class FakeRelevantResult:
    def __init__(self, context):
        self.context = context

def check(name, condition, failures):
    ok = bool(condition)
    print(f"{name}: {'TAK' if ok else 'NIE'}")
    if not ok: failures.append(name)

def main():
    failures = []
    print("=" * 90)
    print("TEST AUTOMATYCZNEGO KONTEKSTU WIEDZY W CYKLU POZNAWCZYM FENIKSA")
    print("=" * 90)

    old_cycle = CognitiveCycle(interpreter=OldStyleInterpreter())
    old_result = old_cycle.run_quantity_vs_quality(
        hypothesis="Hipoteza regresyjna", max_opposing=2,
        prior_knowledge_context="Kontekst testowy")
    check("Stary interpreter nadal działa", old_result is not None, failures)
    check("Wynik zachowuje kontekst dla audytu",
          old_result.prior_knowledge_context == "Kontekst testowy", failures)

    aware = ContextAwareInterpreter()
    result = CognitiveCycle(interpreter=aware).run_quantity_vs_quality(
        hypothesis="Nowa hipoteza", max_opposing=2,
        prior_knowledge_context="WCZEŚNIEJSZA WIEDZA")
    check("Nowy interpreter otrzymał kontekst",
          aware.received_context == "WCZEŚNIEJSZA WIEDZA", failures)
    check("Hipoteza pozostała czysta", result.hypothesis == "Nowa hipoteza", failures)

    feniks = Feniks()
    controlled = ContextAwareInterpreter()
    feniks.cognitive_cycle.interpreter = controlled
    calls = []
    def fake_recall(problem, limit=5):
        calls.append((problem, limit))
        return FakeRelevantResult(FakeContext(
            "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA: rekord testowy"))
    feniks.recall_relevant_knowledge = fake_recall
    feniks_result = feniks.run_cognitive_cycle(
        hypothesis="Czy pamięć pomaga w nowym problemie?",
        max_opposing=2, knowledge_limit=3)

    check("Feniks sam wywołał przypominanie",
          calls == [("Czy pamięć pomaga w nowym problemie?", 3)], failures)
    check("Wiedza trafiła do interpretera osobnym kanałem",
          "rekord testowy" in controlled.received_context, failures)
    check("Wynik zachował użyty kontekst",
          feniks_result.prior_knowledge_context == controlled.received_context, failures)
    check("Hipoteza nie została zanieczyszczona pamięcią",
          feniks_result.hypothesis == "Czy pamięć pomaga w nowym problemie?", failures)

    print("=" * 90)
    if failures:
        print("WERDYKT: TEST NIEZALICZONY")
        for item in failures: print("-", item)
        raise SystemExit(1)
    print("WERDYKT: FENIKS AUTOMATYCZNIE UŻYWA WCZEŚNIEJSZEJ WIEDZY JAKO KONTEKSTU")
    print("=" * 90)

if __name__ == "__main__":
    main()
