from dataclasses import dataclass
from enum import Enum
from typing import Optional

from core.cognitive_cycle import (
    CognitiveCycleDecision,
    CognitiveCycleResult,
)
from core.persistent_memory import PersistentMemory


class KnowledgeGateDecision(Enum):
    """
    Decyzja Bramy Wiedzy.

    REJECTED:
        Kandydat nie spełnia warunków przyjęcia.

    ADMITTED:
        Zweryfikowana wiedza została dopuszczona
        i zapisana do trwałej pamięci.
    """

    REJECTED = "ODRZUCONO"
    ADMITTED = "DOPUSZCZONO_DO_WIEDZY"


@dataclass
class KnowledgeAdmissionResult:
    """
    Wynik działania Bramy Wiedzy.

    Sam wynik bramy pozostaje oddzielony
    od wyniku cyklu poznawczego.
    """

    decision: KnowledgeGateDecision

    admitted: bool

    reason: str

    memory_id: Optional[int] = None


class KnowledgeGate:
    """
    Brama pomiędzy cyklem poznawczym
    a trwałą pamięcią FENIKSA.

    Brama nie tworzy wiedzy.

    Sprawdza, czy rezultat wcześniejszego,
    zwalidowanego procesu poznawczego może
    zostać dopuszczony do trwałej pamięci.

    Model językowy nie podejmuje decyzji
    o zapisie.
    """

    KNOWLEDGE_CATEGORY = "ZWERYFIKOWANA_WIEDZA"

    def __init__(
        self,
        persistent_memory: PersistentMemory,
    ):
        self.persistent_memory = persistent_memory

    def admit(
        self,
        cycle_result: CognitiveCycleResult,
        title: str,
    ) -> KnowledgeAdmissionResult:
        """
        Próbuje dopuścić wynik cyklu poznawczego
        do trwałej pamięci.

        Każdy warunek jest sprawdzany ponownie
        w samej Bramie Wiedzy.
        """

        if not title.strip():
            raise ValueError(
                "Tytuł wiedzy nie może być pusty."
            )

        rejection_reason = self._rejection_reason(
            cycle_result
        )

        if rejection_reason is not None:
            return KnowledgeAdmissionResult(
                decision=KnowledgeGateDecision.REJECTED,
                admitted=False,
                reason=rejection_reason,
                memory_id=None,
            )

        content = self._build_content(
            cycle_result
        )

        metadata = self._build_metadata(
            cycle_result
        )

        memory_id = self.persistent_memory.save(
            category=self.KNOWLEDGE_CATEGORY,
            title=title,
            content=content,
            source="FENIKS_KNOWLEDGE_GATE",
            metadata=metadata,
        )

        cycle_result.admitted_to_memory = True

        return KnowledgeAdmissionResult(
            decision=KnowledgeGateDecision.ADMITTED,
            admitted=True,
            reason=(
                "Kandydat przeszedł Bramę Wiedzy "
                "i został zapisany w trwałej pamięci."
            ),
            memory_id=memory_id,
        )

    def _rejection_reason(
        self,
        cycle_result: CognitiveCycleResult,
    ) -> Optional[str]:
        """
        Sprawdza wszystkie warunki dopuszczenia.

        Nie polega wyłącznie na jednym polu
        safe_for_memory.
        """

        if (
            cycle_result.decision
            != CognitiveCycleDecision.CANDIDATE_FOR_KNOWLEDGE
        ):
            return (
                "Cykl poznawczy nie zakończył się "
                "statusem KANDYDAT_DO_WIEDZY."
            )

        report = cycle_result.validation_report

        if report.safe_for_memory is not True:
            return (
                "Walidator nie uznał interpretacji "
                "za bezpieczną."
            )

        if report.false_unknowns:
            return (
                "Raport zawiera fałszywe niewiadome."
            )

        if report.conflicts:
            return (
                "Raport zawiera sprzeczności "
                "ze zweryfikowaną wiedzą."
            )

        if report.unverifiable:
            return (
                "Raport zawiera twierdzenia "
                "nieweryfikowalne."
            )

        if not cycle_result.experiment_result.observations:
            return (
                "Cykl nie zawiera rzeczywistych "
                "obserwacji eksperymentalnych."
            )

        return None

    def _build_content(
        self,
        cycle_result: CognitiveCycleResult,
    ) -> str:
        """
        Buduje treść trwałego rekordu wiedzy.

        Nie zapisujemy samej swobodnej wypowiedzi
        interpretera. Zachowujemy kontekst,
        w którym powstała.
        """

        interpretation = cycle_result.interpretation
        experiment = cycle_result.experiment_result

        findings = "\n".join(
            f"- {finding}"
            for finding in interpretation.new_findings
        )

        if not findings:
            findings = "- Brak nowych ustaleń."

        cannot_conclude = "\n".join(
            f"- {item}"
            for item in interpretation.cannot_conclude_yet
        )

        if not cannot_conclude:
            cannot_conclude = "- Brak."

        return (
            "HIPOTEZA:\n"
            f"{cycle_result.hypothesis}\n\n"

            "STATUS HIPOTEZY:\n"
            f"{interpretation.hypothesis_status.value}\n\n"

            "UZASADNIENIE INTERPRETACJI:\n"
            f"{interpretation.reasoning}\n\n"

            "ZWERYFIKOWANE USTALENIA:\n"
            f"{findings}\n\n"

            "GRANICE WNIOSKOWANIA:\n"
            f"{cannot_conclude}\n\n"

            "DANE EKSPERYMENTALNE:\n"
            f"Liczba obserwacji: "
            f"{len(experiment.observations)}\n"
            f"Pierwsza sprzeczność: "
            f"{experiment.first_contradiction_at}\n"
            f"Pierwsza przewaga sprzeciwu: "
            f"{experiment.first_opposition_stronger_at}\n\n"

            "POCHODZENIE:\n"
            "ExperimentRunner -> Interpreter -> "
            "ReasoningValidator -> KnowledgeGate"
        )

    def _build_metadata(
        self,
        cycle_result: CognitiveCycleResult,
    ) -> dict:
        """
        Zachowuje maszynowo czytelne pochodzenie
        przyjętej wiedzy.
        """

        interpretation = cycle_result.interpretation
        report = cycle_result.validation_report
        experiment = cycle_result.experiment_result

        return {
            "knowledge_status": "ADMITTED",

            "cycle_decision":
                cycle_result.decision.value,

            "validation_safe_for_memory":
                report.safe_for_memory,

            "false_unknowns":
                len(report.false_unknowns),

            "conflicts":
                len(report.conflicts),

            "unverifiable":
                len(report.unverifiable),

            "hypothesis_status":
                interpretation.hypothesis_status.value,

            "interpretation_confidence":
                interpretation.confidence,

            "experiment_name":
                experiment.name,

            "observation_count":
                len(experiment.observations),

            "first_contradiction_at":
                experiment.first_contradiction_at,

            "first_opposition_stronger_at":
                experiment.first_opposition_stronger_at,

            "provenance": [
                "ExperimentRunner",
                "ExperimentInterpreter",
                "ReasoningValidator",
                "KnowledgeGate",
            ],
        }