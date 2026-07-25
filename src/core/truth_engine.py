from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class KnowledgeType(Enum):
    """
    Typ epistemiczny informacji.

    Wartości są po polsku, ponieważ FENIKS komunikuje
    wyniki swojej analizy w języku polskim.
    """

    FACT = "FAKT"
    EVIDENCE = "DOWÓD"
    INFERENCE = "WNIOSEK"
    HYPOTHESIS = "HIPOTEZA"
    OPINION = "OPINIA"
    UNKNOWN = "NIEUSTALONE"
    CONTRADICTION = "SPRZECZNOŚĆ"


class SourceType(Enum):
    """
    Rodzaj źródła informacji.
    """

    SYSTEM = "SYSTEM"
    CREATOR = "TWÓRCA"
    USER = "UŻYTKOWNIK"
    DOCUMENT = "DOKUMENT"
    DATABASE = "BAZA DANYCH"
    SENSOR = "CZUJNIK"
    MODEL = "MODEL"
    EXTERNAL = "ŹRÓDŁO ZEWNĘTRZNE"
    UNKNOWN = "NIEZNANE"


@dataclass(frozen=True)
class Evidence:
    """
    Pojedynczy dowód wspierający albo podważający twierdzenie.
    """

    description: str
    source: str
    source_type: SourceType = SourceType.UNKNOWN

    reliability: float = 0.5
    supports_claim: bool = True

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )

    def __post_init__(self):
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError(
                "Wiarygodność dowodu musi mieścić się "
                "w zakresie od 0.0 do 1.0."
            )


@dataclass
class Claim:
    """
    Twierdzenie znajdujące się w systemie wiedzy FENIKSA.
    """

    content: str
    knowledge_type: KnowledgeType

    source: str = "nieznane"
    source_type: SourceType = SourceType.UNKNOWN

    evidence: List[Evidence] = field(default_factory=list)

    confidence: float = 0.0

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )

    notes: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.content.strip():
            raise ValueError(
                "Twierdzenie nie może być puste."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Pewność twierdzenia musi mieścić się "
                "w zakresie od 0.0 do 1.0."
            )


@dataclass
class TruthAssessment:
    """
    Wynik analizy twierdzenia.
    """

    claim: Claim

    classification: KnowledgeType
    confidence: float

    supporting_evidence: int
    opposing_evidence: int

    explanation: str

    requires_more_evidence: bool = False
    contradiction_detected: bool = False


class TruthEngine:
    """
    Silnik Prawdy FENIKS OS.

    Nie ogłasza arbitralnie, że coś jest prawdą.

    Analizuje:
    - treść twierdzenia,
    - źródło informacji,
    - dowody wspierające,
    - dowody przeciwne,
    - wiarygodność dowodów,
    - siłę dostępnych podstaw,
    - występowanie sprzeczności,
    - potrzebę zdobycia dalszych informacji.
    """

    def __init__(self):
        self.claims: List[Claim] = []
        self.assessments: List[TruthAssessment] = []

    def register_claim(self, claim: Claim) -> Claim:
        """
        Rejestruje twierdzenie w Silniku Prawdy.
        """

        self.claims.append(claim)
        return claim

    def add_evidence(
        self,
        claim: Claim,
        evidence: Evidence,
    ) -> None:
        """
        Dodaje dowód dotyczący konkretnego twierdzenia.
        """

        claim.evidence.append(evidence)

    def assess(self, claim: Claim) -> TruthAssessment:
        """
        Analizuje aktualny stan wiedzy dotyczącej twierdzenia.
        """

        supporting = [
            evidence
            for evidence in claim.evidence
            if evidence.supports_claim
        ]

        opposing = [
            evidence
            for evidence in claim.evidence
            if not evidence.supports_claim
        ]

        supporting_strength = sum(
            evidence.reliability
            for evidence in supporting
        )

        opposing_strength = sum(
            evidence.reliability
            for evidence in opposing
        )

        total_strength = (
            supporting_strength
            + opposing_strength
        )

        confidence = self._calculate_confidence(
            supporting=supporting,
            supporting_strength=supporting_strength,
            opposing_strength=opposing_strength,
            total_strength=total_strength,
            initial_confidence=claim.confidence,
        )

        contradiction_detected = (
            len(supporting) > 0
            and len(opposing) > 0
        )

        if contradiction_detected:

            classification = KnowledgeType.CONTRADICTION

            explanation = (
                "Wykryto dowody zarówno wspierające, "
                "jak i podważające twierdzenie. "
                "FENIKS nie powinien obecnie uznawać "
                "tego twierdzenia za ustalony fakt."
            )

        elif not claim.evidence:

            classification = KnowledgeType.UNKNOWN

            explanation = (
                "Brak dowodów pozwalających potwierdzić "
                "lub podważyć twierdzenie."
            )

        elif supporting and not opposing:

            classification = self._classify_supported_claim(
                confidence=confidence,
            )

            explanation = (
                "Dostępne dowody wspierają twierdzenie. "
                "Poziom pewności został obliczony na podstawie "
                "siły, jakości i liczby dostępnych dowodów."
            )

        elif opposing and not supporting:

            classification = KnowledgeType.UNKNOWN

            explanation = (
                "Dostępne dowody podważają twierdzenie. "
                "Nie powinno być obecnie traktowane jako fakt."
            )

        else:

            classification = KnowledgeType.UNKNOWN

            explanation = (
                "Nie udało się uzyskać wystarczającej "
                "podstawy do wiarygodnej klasyfikacji."
            )

        requires_more_evidence = (
            classification
            in {
                KnowledgeType.UNKNOWN,
                KnowledgeType.HYPOTHESIS,
                KnowledgeType.CONTRADICTION,
            }
        )

        assessment = TruthAssessment(
            claim=claim,
            classification=classification,
            confidence=round(confidence, 4),
            supporting_evidence=len(supporting),
            opposing_evidence=len(opposing),
            explanation=explanation,
            requires_more_evidence=requires_more_evidence,
            contradiction_detected=contradiction_detected,
        )

        self.assessments.append(assessment)

        return assessment

    def _calculate_confidence(
        self,
        supporting: List[Evidence],
        supporting_strength: float,
        opposing_strength: float,
        total_strength: float,
        initial_confidence: float,
    ) -> float:
        """
        Oblicza poziom pewności.

        Pewność zależy od:
        - bilansu dowodów ZA i PRZECIW,
        - średniej jakości dowodów wspierających,
        - liczby dowodów.

        Brak dowodu przeciwnego nie oznacza automatycznie
        stuprocentowej pewności.
        """

        if total_strength == 0:
            return initial_confidence

        evidence_balance = (
            supporting_strength / total_strength
        )

        if supporting:
            average_support_quality = (
                supporting_strength / len(supporting)
            )
        else:
            average_support_quality = 0.0

        # Trzy dobre dowody osiągają maksymalny
        # współczynnik ilościowy tej wersji algorytmu.
        evidence_quantity_factor = min(
            len(supporting) / 3.0,
            1.0,
        )

        confidence = (
            evidence_balance * 0.45
            + average_support_quality * 0.40
            + evidence_quantity_factor * 0.15
        )

        return max(
            0.0,
            min(confidence, 1.0),
        )

    def _classify_supported_claim(
        self,
        confidence: float,
    ) -> KnowledgeType:
        """
        Klasyfikuje twierdzenie na podstawie
        obliczonego poziomu pewności.

        Progi pozostają jawne i eksperymentalne.
        Będziemy je później kalibrować.
        """

        if confidence >= 0.90:
            return KnowledgeType.FACT

        if confidence >= 0.70:
            return KnowledgeType.INFERENCE

        return KnowledgeType.HYPOTHESIS

    def find_contradictions(
        self,
    ) -> List[TruthAssessment]:
        """
        Zwraca analizy, w których wykryto sprzeczność.
        """

        return [
            assessment
            for assessment in self.assessments
            if assessment.contradiction_detected
        ]

    def unresolved_claims(
        self,
    ) -> List[TruthAssessment]:
        """
        Zwraca twierdzenia wymagające dalszych dowodów.
        """

        return [
            assessment
            for assessment in self.assessments
            if assessment.requires_more_evidence
        ]

    def stats(self) -> dict:
        """
        Podstawowa samoobserwacja Silnika Prawdy.
        """

        return {
            "registered_claims": len(self.claims),
            "assessments": len(self.assessments),
            "contradictions": len(
                self.find_contradictions()
            ),
            "unresolved": len(
                self.unresolved_claims()
            ),
        }