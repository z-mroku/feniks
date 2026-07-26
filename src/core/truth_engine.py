from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class KnowledgeType(Enum):
    """
    Typ epistemiczny informacji.

    Wartości są po polsku, ponieważ FENIKS
    komunikuje wyniki swojej analizy
    w języku polskim.
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


@dataclass
class Evidence:
    """
    Dowód wspierający albo podważający twierdzenie.
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
        if not self.description.strip():
            raise ValueError(
                "Opis dowodu nie może być pusty."
            )

        if not self.source.strip():
            raise ValueError(
                "Źródło dowodu nie może być puste."
            )

        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError(
                "Wiarygodność dowodu musi mieścić się "
                "w zakresie od 0.0 do 1.0."
            )


@dataclass
class Claim:
    """
    Twierdzenie znajdujące się
    w systemie wiedzy FENIKSA.
    """

    content: str
    knowledge_type: KnowledgeType

    source: str = "nieznane"
    source_type: SourceType = SourceType.UNKNOWN

    evidence: List[Evidence] = field(
        default_factory=list
    )

    # Zachowane dla zgodności ze starszym kodem.
    # Nie jest już głównym wynikiem analizy.
    confidence: float = 0.0

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )

    notes: List[str] = field(
        default_factory=list
    )

    def __post_init__(self):
        if not self.content.strip():
            raise ValueError(
                "Twierdzenie nie może być puste."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Pewność początkowa twierdzenia musi "
                "mieścić się w zakresie od 0.0 do 1.0."
            )


@dataclass
class TruthAssessment:
    """
    Wynik analizy twierdzenia.

    Rozdziela trzy różne pojęcia:

    1. siłę poparcia twierdzenia,
    2. siłę sprzeciwu wobec twierdzenia,
    3. pewność samej klasyfikacji.

    Pewność klasyfikacji NIE oznacza
    prawdopodobieństwa, że twierdzenie jest prawdziwe.
    """

    claim: Claim

    classification: KnowledgeType

    support_strength: float
    opposition_strength: float
    classification_confidence: float

    supporting_evidence: int
    opposing_evidence: int

    explanation: str

    requires_more_evidence: bool = False
    contradiction_detected: bool = False

    @property
    def confidence(self) -> float:
        """
        Zachowuje zgodność ze starszym kodem.

        Dawne pole assessment.confidence zwraca teraz
        pewność klasyfikacji, a nie siłę poparcia.
        """

        return self.classification_confidence


class TruthEngine:
    """
    Silnik Prawdy FENIKS OS.

    Nie ogłasza arbitralnie, że coś jest prawdą.

    Oddzielnie analizuje:

    - siłę dowodów ZA,
    - siłę dowodów PRZECIW,
    - występowanie sprzeczności,
    - pewność klasyfikacji,
    - potrzebę dalszych dowodów.

    Dzięki temu silne poparcie nie jest mylone
    z wysoką pewnością prawdziwości, jeżeli
    jednocześnie istnieją mocne dowody przeciwne.
    """

    def __init__(self):
        self.claims: List[Claim] = []
        self.assessments: List[
            TruthAssessment
        ] = []

    def register_claim(
        self,
        claim: Claim,
    ) -> Claim:
        """
        Rejestruje twierdzenie w Silniku Prawdy.
        """

        self.claims.append(
            claim
        )

        return claim

    def add_evidence(
        self,
        claim: Claim,
        evidence: Evidence,
    ) -> None:
        """
        Dodaje dowód dotyczący konkretnego twierdzenia.
        """

        claim.evidence.append(
            evidence
        )

    def assess(
        self,
        claim: Claim,
    ) -> TruthAssessment:
        """
        Analizuje aktualny stan wiedzy
        dotyczącej twierdzenia.
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

        support_strength = (
            self._calculate_side_strength(
                supporting
            )
        )

        opposition_strength = (
            self._calculate_side_strength(
                opposing
            )
        )

        contradiction_detected = (
            bool(supporting)
            and bool(opposing)
        )

        classification = (
            self._classify(
                supporting=supporting,
                opposing=opposing,
                support_strength=support_strength,
                opposition_strength=opposition_strength,
            )
        )

        classification_confidence = (
            self._calculate_classification_confidence(
                classification=classification,
                supporting=supporting,
                opposing=opposing,
                support_strength=support_strength,
                opposition_strength=opposition_strength,
                initial_confidence=claim.confidence,
            )
        )

        explanation = (
            self._build_explanation(
                classification=classification,
                support_strength=support_strength,
                opposition_strength=opposition_strength,
            )
        )

        requires_more_evidence = (
            self._requires_more_evidence(
                classification=classification,
                classification_confidence=(
                    classification_confidence
                ),
            )
        )

        assessment = TruthAssessment(
            claim=claim,
            classification=classification,

            support_strength=round(
                support_strength,
                4,
            ),

            opposition_strength=round(
                opposition_strength,
                4,
            ),

            classification_confidence=round(
                classification_confidence,
                4,
            ),

            supporting_evidence=len(
                supporting
            ),

            opposing_evidence=len(
                opposing
            ),

            explanation=explanation,

            requires_more_evidence=(
                requires_more_evidence
            ),

            contradiction_detected=(
                contradiction_detected
            ),
        )

        self.assessments.append(
            assessment
        )

        return assessment

    # =====================================================
    # SIŁA STRONY
    # =====================================================

    def _calculate_side_strength(
        self,
        evidence_list: List[Evidence],
    ) -> float:
        """
        Oblicza siłę jednej strony sporu:
        ZA albo PRZECIW.

        Bierze pod uwagę:

        - średnią wiarygodność dowodów,
        - liczbę niezależnych zapisanych dowodów.

        Trzy dowody osiągają maksymalny
        współczynnik ilościowy tej wersji.

        Wynik mieści się w zakresie 0.0-1.0.
        """

        if not evidence_list:
            return 0.0

        total_reliability = sum(
            evidence.reliability
            for evidence in evidence_list
        )

        average_reliability = (
            total_reliability
            / len(evidence_list)
        )

        quantity_factor = min(
            len(evidence_list) / 3.0,
            1.0,
        )

        strength = (
            average_reliability * 0.85
            + quantity_factor * 0.15
        )

        return self._clamp(
            strength
        )

    # =====================================================
    # KLASYFIKACJA
    # =====================================================

    def _classify(
        self,
        supporting: List[Evidence],
        opposing: List[Evidence],
        support_strength: float,
        opposition_strength: float,
    ) -> KnowledgeType:
        """
        Ustala typ epistemiczny twierdzenia.

        Sama obecność dowodów po obu stronach
        oznacza SPRZECZNOŚĆ.

        W kolejnych wersjach mechanizm ten może
        zostać rozszerzony o ocenę istotności
        bardzo słabych dowodów.
        """

        if supporting and opposing:
            return KnowledgeType.CONTRADICTION

        if not supporting and not opposing:
            return KnowledgeType.UNKNOWN

        if supporting and not opposing:
            return self._classify_supported_claim(
                support_strength
            )

        if opposing and not supporting:
            return KnowledgeType.UNKNOWN

        return KnowledgeType.UNKNOWN

    def _classify_supported_claim(
        self,
        support_strength: float,
    ) -> KnowledgeType:
        """
        Klasyfikuje twierdzenie posiadające
        wyłącznie dowody wspierające.

        Progi są jawne i eksperymentalne.
        """

        if support_strength >= 0.90:
            return KnowledgeType.FACT

        if support_strength >= 0.70:
            return KnowledgeType.INFERENCE

        return KnowledgeType.HYPOTHESIS

    # =====================================================
    # PEWNOŚĆ KLASYFIKACJI
    # =====================================================

    def _calculate_classification_confidence(
        self,
        classification: KnowledgeType,
        supporting: List[Evidence],
        opposing: List[Evidence],
        support_strength: float,
        opposition_strength: float,
        initial_confidence: float,
    ) -> float:
        """
        Oblicza pewność KLASYFIKACJI.

        Nie odpowiada na pytanie:
        "Jak bardzo twierdzenie jest prawdziwe?"

        Odpowiada na pytanie:
        "Jak mocno dostępne dane uzasadniają
        przypisanie tej klasyfikacji?"
        """

        # ---------------------------------------------
        # BRAK DOWODÓW
        # ---------------------------------------------

        if not supporting and not opposing:

            if initial_confidence > 0.0:
                return self._clamp(
                    initial_confidence * 0.25
                )

            return 0.0

        # ---------------------------------------------
        # SPRZECZNOŚĆ
        # ---------------------------------------------

        if classification == KnowledgeType.CONTRADICTION:

            weaker_side = min(
                support_strength,
                opposition_strength,
            )

            stronger_side = max(
                support_strength,
                opposition_strength,
            )

            if stronger_side == 0.0:
                balance = 0.0
            else:
                balance = (
                    weaker_side
                    / stronger_side
                )

            evidence_presence = min(
                (
                    len(supporting)
                    + len(opposing)
                )
                / 4.0,
                1.0,
            )

            confidence = (
                weaker_side * 0.50
                + balance * 0.30
                + evidence_presence * 0.20
            )

            return self._clamp(
                confidence
            )

        # ---------------------------------------------
        # TYLKO DOWODY WSPIERAJĄCE
        # ---------------------------------------------

        if supporting and not opposing:

            quantity_factor = min(
                len(supporting) / 3.0,
                1.0,
            )

            confidence = (
                support_strength * 0.85
                + quantity_factor * 0.15
            )

            return self._clamp(
                confidence
            )

        # ---------------------------------------------
        # TYLKO DOWODY PRZECIWNE
        # ---------------------------------------------

        if opposing and not supporting:

            quantity_factor = min(
                len(opposing) / 3.0,
                1.0,
            )

            confidence = (
                opposition_strength * 0.85
                + quantity_factor * 0.15
            )

            return self._clamp(
                confidence
            )

        return 0.0

    # =====================================================
    # WYJAŚNIENIE
    # =====================================================

    def _build_explanation(
        self,
        classification: KnowledgeType,
        support_strength: float,
        opposition_strength: float,
    ) -> str:
        """
        Buduje polskie wyjaśnienie wyniku.
        """

        if classification == KnowledgeType.CONTRADICTION:
            return (
                "Wykryto dowody zarówno wspierające, "
                "jak i podważające twierdzenie. "
                "Siła poparcia i siła sprzeciwu zostały "
                "obliczone oddzielnie. Pewność klasyfikacji "
                "opisuje pewność wykrycia stanu sprzeczności, "
                "a nie prawdopodobieństwo prawdziwości "
                "twierdzenia."
            )

        if classification == KnowledgeType.UNKNOWN:

            if (
                support_strength == 0.0
                and opposition_strength == 0.0
            ):
                return (
                    "Brak dowodów pozwalających "
                    "potwierdzić lub podważyć twierdzenie."
                )

            if opposition_strength > 0.0:
                return (
                    "Dostępne dowody podważają twierdzenie. "
                    "Nie ma obecnie wystarczającej podstawy, "
                    "aby traktować je jako ustalony fakt."
                )

            return (
                "Dostępne informacje nie pozwalają "
                "na wiarygodne ustalenie stanu twierdzenia."
            )

        if classification == KnowledgeType.FACT:
            return (
                "Dostępne dowody silnie wspierają "
                "twierdzenie i nie zapisano dowodów "
                "przeciwnych. Klasyfikacja FAKT odnosi się "
                "wyłącznie do aktualnego stanu dostępnych "
                "dowodów i może zostać zmieniona po "
                "pojawieniu się nowych informacji."
            )

        if classification == KnowledgeType.INFERENCE:
            return (
                "Dostępne dowody wspierają twierdzenie, "
                "ale ich łączna siła nie uzasadnia jeszcze "
                "klasyfikacji FAKT."
            )

        if classification == KnowledgeType.HYPOTHESIS:
            return (
                "Istnieją dowody wspierające twierdzenie, "
                "jednak ich obecna siła jest zbyt mała, "
                "aby uznać twierdzenie za ustalony fakt "
                "lub silny wniosek."
            )

        return (
            "Klasyfikacja została wykonana "
            "na podstawie dostępnych dowodów."
        )

    # =====================================================
    # POTRZEBA DALSZYCH DOWODÓW
    # =====================================================

    def _requires_more_evidence(
        self,
        classification: KnowledgeType,
        classification_confidence: float,
    ) -> bool:
        """
        Określa, czy FENIKS powinien poszukiwać
        dalszych dowodów.
        """

        if classification in {
            KnowledgeType.UNKNOWN,
            KnowledgeType.HYPOTHESIS,
            KnowledgeType.CONTRADICTION,
        }:
            return True

        if classification_confidence < 0.75:
            return True

        return False

    # =====================================================
    # NARZĘDZIA
    # =====================================================

    def _clamp(
        self,
        value: float,
    ) -> float:
        """
        Ogranicza wartość do zakresu 0.0-1.0.
        """

        return max(
            0.0,
            min(value, 1.0),
        )

    # =====================================================
    # WYSZUKIWANIE PROBLEMÓW
    # =====================================================

    def find_contradictions(
        self,
    ) -> List[TruthAssessment]:
        """
        Zwraca analizy, w których
        wykryto sprzeczność.
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
        Zwraca twierdzenia wymagające
        dalszych dowodów.
        """

        return [
            assessment
            for assessment in self.assessments
            if assessment.requires_more_evidence
        ]

    # =====================================================
    # STATYSTYKI
    # =====================================================

    def stats(self) -> dict:
        """
        Podstawowa samoobserwacja Silnika Prawdy.
        """

        return {
            "registered_claims":
                len(self.claims),

            "assessments":
                len(self.assessments),

            "contradictions":
                len(
                    self.find_contradictions()
                ),

            "unresolved":
                len(
                    self.unresolved_claims()
                ),
        }