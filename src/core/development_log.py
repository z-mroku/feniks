from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class DevelopmentStatus(Enum):
    """
    Stan wpisu w Rejestrze Rozwoju FENIKSA.
    """

    DISCOVERED = "WYKRYTO"
    ANALYZING = "W ANALIZIE"
    PLANNED = "ZAPLANOWANO"
    IMPLEMENTED = "WDROŻONO"
    TESTED = "PRZETESTOWANO"
    RESOLVED = "ROZWIĄZANO"
    REJECTED = "ODRZUCONO"


class DevelopmentCategory(Enum):
    """
    Kategoria wykrytego problemu lub ulepszenia.
    """

    LOGIC = "LOGIKA"
    TRUTH = "SILNIK PRAWDY"
    MEMORY = "PAMIĘĆ"
    IDENTITY = "TOŻSAMOŚĆ"
    CONSTITUTION = "KONSTYTUCJA"
    GUARDIAN = "STRAŻNIK"
    LANGUAGE = "JĘZYK"
    ARCHITECTURE = "ARCHITEKTURA"
    SECURITY = "BEZPIECZEŃSTWO"
    PERFORMANCE = "WYDAJNOŚĆ"
    OTHER = "INNE"


@dataclass
class DevelopmentEntry:
    """
    Pojedynczy zapis rozwoju FENIKSA.

    Przechowuje nie tylko informację o zmianie,
    lecz również przyczynę, dowody, rezultat
    i kwestie pozostające do rozwiązania.
    """

    title: str
    description: str
    category: DevelopmentCategory

    status: DevelopmentStatus = DevelopmentStatus.DISCOVERED

    discovered_by: str = "FENIKS"

    evidence: List[str] = field(default_factory=list)
    changes: List[str] = field(default_factory=list)
    test_results: List[str] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )

    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )

    def touch(self) -> None:
        """
        Aktualizuje czas ostatniej zmiany wpisu.
        """
        self.updated_at = datetime.now().isoformat(
            timespec="seconds"
        )


class DevelopmentLog:
    """
    Rejestr Rozwoju FENIKS OS.

    Jego zadaniem jest zachowanie historii:

    PROBLEM
        ↓
    DOWODY
        ↓
    ANALIZA
        ↓
    ZMIANA
        ↓
    TEST
        ↓
    WYNIK
        ↓
    NIERozwiązane KWESTIE

    Rejestr ma w przyszłości umożliwić FENIKSOWI
    analizowanie własnej historii rozwoju.
    """

    def __init__(self):
        self.entries: List[DevelopmentEntry] = []

    def register(
        self,
        title: str,
        description: str,
        category: DevelopmentCategory,
        discovered_by: str = "FENIKS",
    ) -> DevelopmentEntry:
        """
        Rejestruje nowe odkrycie, problem albo
        propozycję ulepszenia.
        """

        entry = DevelopmentEntry(
            title=title,
            description=description,
            category=category,
            discovered_by=discovered_by,
        )

        self.entries.append(entry)

        return entry

    def add_evidence(
        self,
        entry: DevelopmentEntry,
        evidence: str,
    ) -> None:
        """
        Dodaje dowód uzasadniający wpis.
        """

        entry.evidence.append(evidence)
        entry.touch()

    def add_change(
        self,
        entry: DevelopmentEntry,
        change: str,
    ) -> None:
        """
        Zapisuje zmianę wprowadzoną w systemie.
        """

        entry.changes.append(change)
        entry.touch()

    def add_test_result(
        self,
        entry: DevelopmentEntry,
        result: str,
    ) -> None:
        """
        Zapisuje rezultat testu.
        """

        entry.test_results.append(result)
        entry.touch()

    def add_unresolved(
        self,
        entry: DevelopmentEntry,
        issue: str,
    ) -> None:
        """
        Zapisuje problem, którego jeszcze nie rozwiązano.
        """

        entry.unresolved.append(issue)
        entry.touch()

    def change_status(
        self,
        entry: DevelopmentEntry,
        status: DevelopmentStatus,
    ) -> None:
        """
        Zmienia stan wpisu.
        """

        entry.status = status
        entry.touch()

    def history(self) -> List[DevelopmentEntry]:
        """
        Zwraca kopię całej historii rozwoju.
        """

        return self.entries.copy()

    def unresolved_entries(self) -> List[DevelopmentEntry]:
        """
        Zwraca wpisy zawierające nierozwiązane kwestie.
        """

        return [
            entry
            for entry in self.entries
            if entry.unresolved
        ]

    def find_by_category(
        self,
        category: DevelopmentCategory,
    ) -> List[DevelopmentEntry]:
        """
        Wyszukuje wpisy należące do danej kategorii.
        """

        return [
            entry
            for entry in self.entries
            if entry.category == category
        ]

    def stats(self) -> dict:
        """
        Podstawowe dane o historii rozwoju.
        """

        return {
            "liczba_wpisow": len(self.entries),
            "nierozwiazane": len(
                self.unresolved_entries()
            ),
            "rozwiazane": len(
                [
                    entry
                    for entry in self.entries
                    if entry.status
                    == DevelopmentStatus.RESOLVED
                ]
            ),
        }