from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.persistent_memory import PersistentMemory


class AnalysisPriority(Enum):
    """
    Priorytet problemu wykrytego podczas samoanalizy.
    """

    LOW = "NISKI"
    MEDIUM = "ŚREDNI"
    HIGH = "WYSOKI"
    CRITICAL = "KRYTYCZNY"


class AnalysisStatus(Enum):
    """
    Stan problemu z punktu widzenia samoanalizy.
    """

    OBSERVED = "ZAOBSERWOWANO"
    REQUIRES_ANALYSIS = "WYMAGA ANALIZY"
    PROPOSAL_READY = "PRZYGOTOWANO PROPOZYCJĘ DZIAŁANIA"


@dataclass
class SelfAnalysisFinding:
    """
    Pojedyncze ustalenie powstałe podczas samoanalizy.
    """

    title: str
    module: str
    problem: str

    priority: AnalysisPriority
    status: AnalysisStatus

    evidence: List[str] = field(
        default_factory=list
    )

    unknowns: List[str] = field(
        default_factory=list
    )

    proposed_next_step: Optional[str] = None
    source_entry_id: Optional[int] = None

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )


@dataclass
class SelfAnalysisReport:
    """
    Pełny raport samoanalizy FENIKSA.
    """

    findings: List[SelfAnalysisFinding]

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(
            timespec="seconds"
        )
    )

    @property
    def number_of_findings(self) -> int:
        return len(self.findings)

    @property
    def requires_attention(self) -> bool:
        return any(
            finding.status
            == AnalysisStatus.REQUIRES_ANALYSIS
            for finding in self.findings
        )

    def critical_findings(
        self,
    ) -> List[SelfAnalysisFinding]:
        """
        Zwraca problemy oznaczone jako krytyczne.
        """

        return [
            finding
            for finding in self.findings
            if finding.priority
            == AnalysisPriority.CRITICAL
        ]


class SelfAnalysis:
    """
    Moduł samoanalizy FENIKS OS.

    Nie zmienia samodzielnie kodu.

    Jego zadaniem jest:
    1. odczytać historię rozwoju,
    2. znaleźć nierozwiązane problemy,
    3. wskazać podstawę ich wykrycia,
    4. określić obszar systemu,
    5. wskazać braki wiedzy,
    6. porównać problem z rozwiązaną historią,
    7. zaproponować następny krok bez powtarzania
       rozwiązania, które zostało już wdrożone.
    """

    def __init__(
        self,
        persistent_memory: PersistentMemory,
    ):
        self.persistent_memory = persistent_memory

        self.reports: List[
            SelfAnalysisReport
        ] = []

    # =====================================================
    # GŁÓWNA SAMOANALIZA
    # =====================================================

    def analyze_development_history(
        self,
    ) -> SelfAnalysisReport:
        """
        Analizuje nierozwiązane wpisy
        trwałej historii rozwoju.
        """

        unresolved_entries = (
            self.persistent_memory
            .unresolved_development()
        )

        resolved_entries = (
            self.persistent_memory
            .resolved_development()
        )

        findings: List[
            SelfAnalysisFinding
        ] = []

        for entry in unresolved_entries:

            finding = self._analyze_development_entry(
                entry=entry,
                resolved_entries=resolved_entries,
            )

            findings.append(
                finding
            )

        report = SelfAnalysisReport(
            findings=findings
        )

        self.reports.append(
            report
        )

        return report

    # =====================================================
    # ANALIZA POJEDYNCZEGO WPISU
    # =====================================================

    def _analyze_development_entry(
        self,
        entry: Dict[str, Any],
        resolved_entries: List[Dict[str, Any]],
    ) -> SelfAnalysisFinding:
        """
        Zamienia nierozwiązany wpis historii
        rozwoju na ustalenie samoanalizy.
        """

        unresolved = entry.get(
            "nierozwiazane",
            [],
        )

        evidence = entry.get(
            "dowody",
            [],
        )

        changes = entry.get(
            "zmiany",
            [],
        )

        test_results = entry.get(
            "wyniki_testow",
            [],
        )

        category = entry.get(
            "kategoria",
            "NIEZNANY OBSZAR",
        )

        problem = self._build_problem_description(
            unresolved
        )

        analysis_evidence = (
            self._build_analysis_evidence(
                evidence=evidence,
                changes=changes,
                test_results=test_results,
            )
        )

        related_history = (
            self._find_related_resolved_history(
                entry=entry,
                resolved_entries=resolved_entries,
            )
        )

        if related_history:
            analysis_evidence.extend(
                self._build_history_evidence(
                    related_history
                )
            )

        unknowns = self._identify_unknowns(
            entry=entry,
            related_history=related_history,
        )

        priority = self._estimate_priority(
            entry=entry
        )

        proposed_next_step = (
            self._propose_next_step(
                entry=entry,
                related_history=related_history,
            )
        )

        return SelfAnalysisFinding(
            title=entry.get(
                "tytul",
                "Nienazwany problem",
            ),
            module=category,
            problem=problem,
            priority=priority,
            status=AnalysisStatus.REQUIRES_ANALYSIS,
            evidence=analysis_evidence,
            unknowns=unknowns,
            proposed_next_step=proposed_next_step,
            source_entry_id=entry.get("id"),
        )

    # =====================================================
    # OPIS PROBLEMU
    # =====================================================

    def _build_problem_description(
        self,
        unresolved: List[str],
    ) -> str:
        """
        Buduje opis problemu z zapisanych
        nierozwiązanych kwestii.
        """

        if not unresolved:
            return (
                "Nie znaleziono jednoznacznie "
                "opisanego nierozwiązanego problemu."
            )

        return " ".join(
            unresolved
        )

    # =====================================================
    # DOWODY
    # =====================================================

    def _build_analysis_evidence(
        self,
        evidence: List[str],
        changes: List[str],
        test_results: List[str],
    ) -> List[str]:
        """
        Buduje zestaw podstaw samoanalizy.
        """

        result: List[str] = []

        for item in evidence:
            result.append(
                f"Dowód historyczny: {item}"
            )

        for item in changes:
            result.append(
                f"Wcześniejsza zmiana: {item}"
            )

        for item in test_results:
            result.append(
                f"Wynik wcześniejszego testu: {item}"
            )

        if not result:
            result.append(
                "Brak wystarczających danych "
                "historycznych do pełnej oceny."
            )

        return result

    def _build_history_evidence(
        self,
        related_history: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Dodaje informacje o powiązanych,
        wcześniej rozwiązanych doświadczeniach.
        """

        result: List[str] = []

        for entry in related_history:

            result.append(
                "Powiązane rozwiązane doświadczenie "
                f"nr {entry['id']}: "
                f"{entry['tytul']}."
            )

            for change in entry.get(
                "zmiany",
                [],
            ):
                result.append(
                    "W rozwiązanym doświadczeniu "
                    f"wdrożono: {change}"
                )

            for test in entry.get(
                "wyniki_testow",
                [],
            ):
                result.append(
                    "W rozwiązanym doświadczeniu "
                    f"uzyskano wynik testu: {test}"
                )

        return result

    # =====================================================
    # PORÓWNANIE Z HISTORIĄ
    # =====================================================

    def _find_related_resolved_history(
        self,
        entry: Dict[str, Any],
        resolved_entries: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Szuka rozwiązanych doświadczeń należących
        do tego samego obszaru systemu.

        To pierwszy etap mechanizmu kontekstowego.

        Sam fakt zgodności kategorii nie oznacza,
        że stare rozwiązanie pasuje do nowego problemu.
        Historia ma służyć jako kontekst i zabezpieczenie
        przed bezmyślnym powtarzaniem wcześniejszych zmian.
        """

        current_category = str(
            entry.get(
                "kategoria",
                ""
            )
        ).casefold()

        related: List[
            Dict[str, Any]
        ] = []

        for resolved in resolved_entries:

            resolved_category = str(
                resolved.get(
                    "kategoria",
                    ""
                )
            ).casefold()

            if (
                current_category
                and current_category
                == resolved_category
            ):
                related.append(
                    resolved
                )

        return related

    # =====================================================
    # BRAKI WIEDZY
    # =====================================================

    def _identify_unknowns(
        self,
        entry: Dict[str, Any],
        related_history: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Wskazuje informacje, których obecna
        historia nie pozwala jeszcze ustalić.
        """

        unknowns: List[str] = []

        if entry.get(
            "nierozwiazane"
        ):
            unknowns.append(
                "Nie wiadomo jeszcze, jakie rozwiązanie "
                "najlepiej usunie zapisany problem."
            )

        if not entry.get(
            "wyniki_testow"
        ):
            unknowns.append(
                "Brakuje wyników testów pozwalających "
                "ocenić zachowanie systemu."
            )

        if not entry.get(
            "dowody"
        ):
            unknowns.append(
                "Brakuje zapisanych dowodów "
                "uzasadniających problem."
            )

        if related_history:
            unknowns.append(
                "Istnieją wcześniejsze rozwiązane "
                "doświadczenia z tego samego obszaru. "
                "Należy ustalić, które ich elementy są "
                "przydatne, a których nie wolno "
                "bezpośrednio powtarzać."
            )

        return unknowns

    # =====================================================
    # PRIORYTET
    # =====================================================

    def _estimate_priority(
        self,
        entry: Dict[str, Any],
    ) -> AnalysisPriority:
        """
        Ustala priorytet problemu według jawnych reguł.
        """

        category = str(
            entry.get(
                "kategoria",
                ""
            )
        ).casefold()

        if "prawdy" in category:
            return AnalysisPriority.HIGH

        if entry.get(
            "nierozwiazane"
        ):
            return AnalysisPriority.MEDIUM

        return AnalysisPriority.LOW

    # =====================================================
    # ANALIZA TREŚCI PROBLEMU
    # =====================================================

    def _problem_text(
        self,
        entry: Dict[str, Any],
    ) -> str:
        """
        Łączy najważniejsze informacje o problemie
        w jeden tekst roboczy.
        """

        parts: List[str] = []

        parts.append(
            str(
                entry.get(
                    "tytul",
                    ""
                )
            )
        )

        parts.append(
            str(
                entry.get(
                    "opis",
                    ""
                )
            )
        )

        parts.extend(
            entry.get(
                "nierozwiazane",
                [],
            )
        )

        parts.extend(
            entry.get(
                "dowody",
                [],
            )
        )

        return " ".join(
            parts
        ).casefold()

    # =====================================================
    # NASTĘPNY KROK
    # =====================================================

    def _propose_next_step(
        self,
        entry: Dict[str, Any],
        related_history: List[Dict[str, Any]],
    ) -> str:
        """
        Przygotowuje następny krok na podstawie
        konkretnego problemu i historii.

        Nie zakłada, że wszystkie problemy należące
        do jednej kategorii wymagają tego samego
        rozwiązania.
        """

        problem_text = self._problem_text(
            entry
        )

        # -------------------------------------------------
        # Problem dotyczący jakości lub siły dowodów.
        # -------------------------------------------------

        evidence_terms = (
            "słaby dowód",
            "bardzo słaby",
            "wiarygodność",
            "minimalną istotność",
            "relację sił",
            "dowód przeciwny",
        )

        if any(
            term in problem_text
            for term in evidence_terms
        ):
            return (
                "Zaprojektować serię kontrolowanych "
                "testów z dowodami o różnych poziomach "
                "wiarygodności po obu stronach twierdzenia. "
                "Porównać siłę poparcia, siłę sprzeciwu "
                "oraz wynik klasyfikacji. Na podstawie "
                "wyników ustalić, czy sama obecność "
                "dowodu przeciwnego powinna wystarczać "
                "do stwierdzenia SPRZECZNOŚCI, czy potrzebne "
                "jest dodatkowe kryterium istotności."
            )

        # -------------------------------------------------
        # Problem dotyczący samej Samoanalizy.
        # -------------------------------------------------

        self_analysis_terms = (
            "samoanaliz",
            "następnego kroku",
            "proponowania",
            "konkretną treść problemu",
        )

        if any(
            term in problem_text
            for term in self_analysis_terms
        ):
            return (
                "Przetestować mechanizm Samoanalizy na "
                "kilku różnych nierozwiązanych problemach "
                "należących do tej samej kategorii. "
                "Sprawdzić, czy dla każdego problemu "
                "powstaje inny następny krok wynikający "
                "z jego treści, dowodów i historii, "
                "zamiast jednej odpowiedzi przypisanej "
                "do całej kategorii."
            )

        # -------------------------------------------------
        # Jeśli istnieje powiązana rozwiązana historia,
        # nie powtarzamy automatycznie starego rozwiązania.
        # -------------------------------------------------

        if related_history:
            return (
                "Porównać bieżący problem z wcześniejszymi "
                "rozwiązanymi doświadczeniami z tego samego "
                "obszaru. Oddzielić elementy już wdrożone "
                "od nowych niewiadomych, następnie "
                "zaprojektować test dotyczący wyłącznie "
                "nierozwiązanej części obecnego problemu."
            )

        # -------------------------------------------------
        # Bezpieczna reguła ogólna.
        # -------------------------------------------------

        return (
            "Przeanalizować konkretną treść problemu "
            "i dostępne dowody, określić możliwe "
            "konkurencyjne wyjaśnienia lub rozwiązania, "
            "a następnie zaprojektować test pozwalający "
            "je porównać przed wprowadzeniem zmiany."
        )

    # =====================================================
    # OSTATNI RAPORT
    # =====================================================

    def last_report(
        self,
    ) -> Optional[SelfAnalysisReport]:
        """
        Zwraca ostatni raport samoanalizy.
        """

        if not self.reports:
            return None

        return self.reports[-1]

    # =====================================================
    # STATYSTYKI
    # =====================================================

    def stats(
        self,
    ) -> Dict[str, Any]:
        """
        Podstawowy stan modułu samoanalizy.
        """

        findings = sum(
            report.number_of_findings
            for report in self.reports
        )

        return {
            "liczba_raportow": len(
                self.reports
            ),
            "liczba_ustalen": findings,
            "modul_gotowy": True,
        }