from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from core.constitution import Constitution


class Verdict(Enum):
    """
    Możliwe wyniki oceny Strażnika.

    Nie ograniczamy decyzji do prostego True/False.
    """
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


@dataclass
class Concern:
    """
    Pojedyncze zastrzeżenie znalezione podczas analizy.
    """
    article_number: Optional[int]
    title: str
    explanation: str
    severity: int = 1


@dataclass
class GuardianReport:
    """
    Pełny raport Strażnika.

    Dzięki temu FENIKS będzie wiedział nie tylko,
    czy działanie przeszło kontrolę, ale również dlaczego.
    """
    verdict: Verdict
    action: str
    concerns: List[Concern] = field(default_factory=list)
    confidence: float = 1.0

    @property
    def approved(self) -> bool:
        return self.verdict == Verdict.ALLOW

    def summary(self) -> str:
        if not self.concerns:
            return "Nie wykryto konfliktu z aktualnymi regułami Strażnika."

        reasons = "; ".join(
            concern.explanation
            for concern in self.concerns
        )

        return reasons


class Guardian:
    """
    Strażnik FENIKS OS.

    Jego zadaniem jest kontrolowanie proponowanych działań
    względem Konstytucji.

    Guardian NIE jest Sumieniem.
    Guardian NIE ustala prawdy.
    Guardian NIE podejmuje ostatecznie wszystkich decyzji.

    Jest warstwą kontroli pomiędzy zamiarem a wykonaniem.
    """

    def __init__(self, constitution: Constitution):
        self.constitution = constitution
        self.audit_log: List[GuardianReport] = []

    def evaluate(self, action: str) -> GuardianReport:
        """
        Analizuje proponowane działanie.

        To jest pierwsza, celowo prosta wersja.
        Później analiza będzie korzystać również z:
        - Truth Engine,
        - Sumienia,
        - Krytyka,
        - modelu ryzyka,
        - kontekstu działania.
        """

        action = action.strip()

        if not action:
            report = GuardianReport(
                verdict=Verdict.BLOCK,
                action=action,
                concerns=[
                    Concern(
                        article_number=None,
                        title="Brak działania",
                        explanation=(
                            "Nie można ocenić działania, "
                            "którego treść jest pusta."
                        ),
                        severity=3,
                    )
                ],
                confidence=1.0,
            )

            self._record(report)
            return report

        concerns: List[Concern] = []

        normalized = action.casefold()

        # Pierwszy mechanizm kontroli prawdy.
        deception_signals = [
            "udawaj że wiesz",
            "udawaj, że wiesz",
            "zmyśl fakt",
            "wymyśl fakt",
            "ukryj niepewność",
        ]

        if any(signal in normalized for signal in deception_signals):
            concerns.append(
                Concern(
                    article_number=1,
                    title="Możliwy konflikt z zasadą Prawdy",
                    explanation=(
                        "Działanie może wymagać przedstawienia "
                        "niezweryfikowanej informacji jako faktu."
                    ),
                    severity=3,
                )
            )

        # Pierwsza kontrola historii i błędów.
        concealment_signals = [
            "ukryj błąd",
            "usuń historię błędu",
            "zataj błąd",
        ]

        if any(signal in normalized for signal in concealment_signals):
            concerns.append(
                Concern(
                    article_number=12,
                    title="Możliwa próba ukrycia błędu",
                    explanation=(
                        "Konstytucja wymaga analizowania błędów "
                        "zamiast ich ukrywania."
                    ),
                    severity=3,
                )
            )

        # Jeżeli wykryto poważne zastrzeżenia,
        # działanie wymaga zatrzymania.
        if any(concern.severity >= 3 for concern in concerns):
            verdict = Verdict.BLOCK

        elif concerns:
            verdict = Verdict.REVIEW

        else:
            verdict = Verdict.ALLOW

        report = GuardianReport(
            verdict=verdict,
            action=action,
            concerns=concerns,
            confidence=0.80 if concerns else 0.70,
        )

        self._record(report)

        return report

    def _record(self, report: GuardianReport):
        """
        Zachowuje historię kontroli Strażnika.

        Na razie w RAM.
        Później audit trafi do trwałej pamięci.
        """
        self.audit_log.append(report)

    def history(self) -> List[GuardianReport]:
        """
        Zwraca kopię historii ocen.
        """
        return self.audit_log.copy()

    def last_report(self) -> Optional[GuardianReport]:
        """
        Zwraca ostatnią wykonaną ocenę.
        """
        if not self.audit_log:
            return None

        return self.audit_log[-1]