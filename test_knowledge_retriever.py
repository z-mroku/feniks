import gc
from pathlib import Path

from core.cognitive_cycle import CognitiveCycle
from core.experiment_interpreter import (
    ExperimentInterpretation,
    HypothesisStatus,
)
from core.experiment_runner import ExperimentRunner
from core.knowledge_gate import KnowledgeGate
from core.knowledge_retriever import KnowledgeRetriever
from core.persistent_memory import PersistentMemory
from core.reasoning_validator import ReasoningValidator
from core.system_knowledge import SystemKnowledge


TEST_DATABASE = Path("data") / "feniks_knowledge_retriever_test.db"


class ControlledCorrectInterpreter:
    """Deterministyczny interpreter bez Gemini i bez sieci."""

    def interpret(self, hypothesis, result):
        return ExperimentInterpretation(
            hypothesis_status=HypothesisStatus.REJECTED,
            reasoning=(
                "W przebadanym zakresie liczba przeciętnych dowodów "
                "przeciwnych nie doprowadziła do przewagi sprzeciwu "
                "nad poparciem."
            ),
            new_findings=[
                "Sprzeczność pojawiła się już przy N=1.",
                "Siła sprzeciwu wykazuje saturację od N=3.",
            ],
            remaining_unknowns=[],
            alternative_explanations=[],
            next_experiment_question=(
                "Czy wynik pozostanie taki sam dla innych "
                "poziomów wiarygodności?"
            ),
            next_experiment=(
                "Powtórzyć eksperyment dla innych kontrolowanych "
                "wartości wiarygodności."
            ),
            cannot_conclude_yet=[
                "Nie należy uogólniać wyniku poza zakres "
                "przebadanych parametrów."
            ],
            confidence=0.95,
        )


def check(name, condition, failures):
    passed = bool(condition)
    print(f"{name}: {'TAK' if passed else 'NIE'}")
    if not passed:
        failures.append(name)


def remove_database():
    gc.collect()
    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()


def admitted_metadata():
    return {
        "knowledge_status": "ADMITTED",
        "cycle_decision": "KANDYDAT_DO_WIEDZY",
        "validation_safe_for_memory": True,
        "false_unknowns": 0,
        "conflicts": 0,
        "unverifiable": 0,
        "hypothesis_status": "OBALONA",
        "interpretation_confidence": 0.95,
        "experiment_name": "test",
        "observation_count": 5,
        "first_contradiction_at": 1,
        "first_opposition_stronger_at": None,
        "provenance": [
            "ExperimentRunner",
            "ExperimentInterpreter",
            "ReasoningValidator",
            "KnowledgeGate",
        ],
    }


def main():
    failures = []

    print("=" * 90)
    print("TEST BEZPIECZNEGO ODZYSKIWANIA WIEDZY FENIKSA")
    print("=" * 90)

    remove_database()

    memory = None

    try:
        memory = PersistentMemory(database_path=str(TEST_DATABASE))

        knowledge = SystemKnowledge()
        runner = ExperimentRunner()
        validator = ReasoningValidator(system_knowledge=knowledge)
        interpreter = ControlledCorrectInterpreter()

        cycle = CognitiveCycle(
            interpreter=interpreter,
            system_knowledge=knowledge,
            experiment_runner=runner,
            reasoning_validator=validator,
        )

        gate = KnowledgeGate(persistent_memory=memory)
        retriever = KnowledgeRetriever(persistent_memory=memory)

        print()
        print("ETAP 1 - UTWORZENIE PRAWDZIWEJ ZWERYFIKOWANEJ WIEDZY")
        print("-" * 90)

        cycle_result = cycle.run_quantity_vs_quality(
            hypothesis=(
                "Rosnąca liczba przeciętnych dowodów przeciwnych "
                "ostatecznie przewyższy jeden mocny dowód wspierający."
            ),
            strong_support_reliability=0.95,
            opposing_reliability=0.50,
            max_opposing=4,
        )

        admission = gate.admit(
            cycle_result=cycle_result,
            title="TruthEngine sprzeczność i saturacja",
        )

        check(
            "KnowledgeGate dopuścił prawdziwy rekord",
            admission.admitted is True,
            failures,
        )
        check(
            "Prawdziwy rekord ma ID",
            admission.memory_id is not None,
            failures,
        )

        valid_id = admission.memory_id

        print()
        print("ETAP 2 - WPROWADZENIE REKORDÓW-PUŁAPEK")
        print("-" * 90)

        base = admitted_metadata()

        fake_source_id = memory.save(
            category=KnowledgeGate.KNOWLEDGE_CATEGORY,
            title="TruthEngine fałszywe źródło",
            content="TruthEngine rekord podszywający się pod wiedzę.",
            source="RECZNY_WPIS",
            metadata=base,
        )

        wrong_status = dict(base)
        wrong_status["knowledge_status"] = "CANDIDATE"
        wrong_status_id = memory.save(
            category=KnowledgeGate.KNOWLEDGE_CATEGORY,
            title="TruthEngine błędny status",
            content="TruthEngine rekord bez statusu ADMITTED.",
            source="FENIKS_KNOWLEDGE_GATE",
            metadata=wrong_status,
        )

        conflict = dict(base)
        conflict["conflicts"] = 1
        conflict_id = memory.save(
            category=KnowledgeGate.KNOWLEDGE_CATEGORY,
            title="TruthEngine konflikt",
            content="TruthEngine rekord zawierający konflikt.",
            source="FENIKS_KNOWLEDGE_GATE",
            metadata=conflict,
        )

        ordinary_id = memory.save(
            category="ZWYKLE_WSPOMNIENIE",
            title="TruthEngine zwykłe wspomnienie",
            content="TruthEngine tekst spoza kategorii wiedzy.",
            source="FENIKS",
            metadata={},
        )

        check("Utworzono pułapkę ze złym źródłem", fake_source_id is not None, failures)
        check("Utworzono pułapkę ze złym statusem", wrong_status_id is not None, failures)
        check("Utworzono pułapkę z konfliktem", conflict_id is not None, failures)
        check("Utworzono zwykłe wspomnienie", ordinary_id is not None, failures)
        check("Baza zawiera łącznie 5 rekordów", memory.count() == 5, failures)

        print()
        print("ETAP 3 - WYSZUKIWANIE AKTYWNEJ PAMIĘCI")
        print("-" * 90)

        context = retriever.retrieve("TruthEngine")

        print("Liczba bezpiecznie odzyskanych rekordów:", context.count)

        check("Retriever znalazł wiedzę", context.found is True, failures)
        check("Retriever zwrócił dokładnie 1 rekord", context.count == 1, failures)
        check(
            "Odzyskany rekord jest rekordem z KnowledgeGate",
            context.records[0].memory_id == valid_id if context.records else False,
            failures,
        )
        check(
            "Nie przepuszczono rekordu ze złym źródłem",
            fake_source_id not in [r.memory_id for r in context.records],
            failures,
        )
        check(
            "Nie przepuszczono rekordu ze złym statusem",
            wrong_status_id not in [r.memory_id for r in context.records],
            failures,
        )
        check(
            "Nie przepuszczono rekordu z konfliktem",
            conflict_id not in [r.memory_id for r in context.records],
            failures,
        )
        check(
            "Nie przepuszczono zwykłego wspomnienia",
            ordinary_id not in [r.memory_id for r in context.records],
            failures,
        )

        print()
        print("ETAP 4 - KONTROLA KONTEKSTU POZNAWCZEGO")
        print("-" * 90)

        text = context.as_text()

        check(
            "Kontekst oznacza wiedzę jako wcześniejszą",
            "WCZEŚNIEJSZA ZWERYFIKOWANA WIEDZA" in text,
            failures,
        )
        check(
            "Kontekst ostrzega przed automatycznym rozstrzygnięciem",
            "Nie stanowią automatycznego rozstrzygnięcia" in text,
            failures,
        )
        check(
            "Kontekst zachowuje źródło",
            "FENIKS_KNOWLEDGE_GATE" in text,
            failures,
        )
        check(
            "Kontekst zachowuje pochodzenie",
            "ExperimentRunner -> ExperimentInterpreter -> ReasoningValidator -> KnowledgeGate"
            in text,
            failures,
        )

        print()
        print("ETAP 5 - ODCZYT CAŁEJ ZWERYFIKOWANEJ WIEDZY")
        print("-" * 90)

        all_verified = retriever.all_verified()

        check(
            "all_verified również zwraca tylko 1 bezpieczny rekord",
            all_verified.count == 1,
            failures,
        )
        check(
            "all_verified odrzuca rekordy-pułapki",
            (
                all_verified.records[0].memory_id == valid_id
                if all_verified.records
                else False
            ),
            failures,
        )

        print()
        print("ETAP 6 - PRZYPADKI BRZEGOWE")
        print("-" * 90)

        empty = retriever.retrieve("   ")
        missing = retriever.retrieve("FRAZA_KTOREJ_NIE_MA_987654321")

        check("Puste zapytanie niczego nie zwraca", empty.count == 0, failures)
        check("Nieznana fraza niczego nie zwraca", missing.count == 0, failures)

        limit_zero = retriever.retrieve("TruthEngine", limit=0)
        check("Limit 0 zwraca 0 rekordów", limit_zero.count == 0, failures)

        negative_limit_rejected = False
        try:
            retriever.retrieve("TruthEngine", limit=-1)
        except ValueError:
            negative_limit_rejected = True

        check(
            "Ujemny limit jest odrzucany",
            negative_limit_rejected,
            failures,
        )

        memory = None
        gc.collect()

    finally:
        memory = None
        gc.collect()
        remove_database()

    print()
    print("=" * 90)

    if failures:
        print("WERDYKT: TEST KNOWLEDGE RETRIEVER NIEZALICZONY")
        print("=" * 90)
        print()
        print("NIEZALICZONE WARUNKI:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("WERDYKT: KNOWLEDGE RETRIEVER BEZPIECZNIE ODZYSKUJE WIEDZĘ")
    print("=" * 90)
    print()
    print(
        "FENIKS potrafi odnaleźć wcześniej zweryfikowaną wiedzę, "
        "odrzucić rekordy podszywające się pod wiedzę i przygotować "
        "bezpieczny kontekst dla kolejnego procesu poznawczego."
    )


if __name__ == "__main__":
    main()
