import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class PersistentMemory:
    """
    Trwała pamięć FENIKS OS.

    Pamięć wykorzystuje lokalną bazę SQLite.

    Przechowuje obecnie dwa główne rodzaje danych:

    1. Zwykłe trwałe wspomnienia.
    2. Historię rozwoju FENIKSA.

    Dane pozostają dostępne po zamknięciu
    i ponownym uruchomieniu programu.
    """

    def __init__(
        self,
        database_path: Optional[str] = None,
    ):
        if database_path is None:
            project_root = (
                Path(__file__).resolve().parents[2]
            )

            data_directory = project_root / "data"

            data_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.database_path = (
                data_directory / "feniks.db"
            )

        else:
            self.database_path = Path(
                database_path
            )

            self.database_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        """
        Tworzy połączenie z bazą danych.
        """

        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _initialize_database(self) -> None:
        """
        Tworzy wymagane tabele, jeżeli jeszcze
        nie istnieją.

        CREATE TABLE IF NOT EXISTS pozwala bezpiecznie
        rozszerzać istniejącą bazę FENIKSA.
        """

        with self._connect() as connection:

            # -------------------------------------------------
            # ZWYKŁA PAMIĘĆ TRWAŁA
            # -------------------------------------------------

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            # -------------------------------------------------
            # HISTORIA ROZWOJU FENIKSA
            # -------------------------------------------------

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS development_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    discovered_by TEXT NOT NULL,

                    evidence TEXT NOT NULL,
                    changes TEXT NOT NULL,
                    test_results TEXT NOT NULL,
                    unresolved TEXT NOT NULL,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            connection.commit()

    # =========================================================
    # ZWYKŁA PAMIĘĆ TRWAŁA
    # =========================================================

    def save(
        self,
        category: str,
        title: str,
        content: str,
        source: str = "FENIKS",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Trwale zapisuje zwykłe wspomnienie.

        Zwraca numer identyfikacyjny wpisu.
        """

        if not category.strip():
            raise ValueError(
                "Kategoria nie może być pusta."
            )

        if not title.strip():
            raise ValueError(
                "Tytuł nie może być pusty."
            )

        if not content.strip():
            raise ValueError(
                "Treść nie może być pusta."
            )

        if metadata is None:
            metadata = {}

        created_at = datetime.now().isoformat(
            timespec="seconds"
        )

        metadata_json = json.dumps(
            metadata,
            ensure_ascii=False,
        )

        with self._connect() as connection:

            cursor = connection.execute(
                """
                INSERT INTO memories (
                    category,
                    title,
                    content,
                    source,
                    metadata,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    category,
                    title,
                    content,
                    source,
                    metadata_json,
                    created_at,
                ),
            )

            connection.commit()

            return int(cursor.lastrowid)

    def get(
        self,
        memory_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Odczytuje pojedyncze wspomnienie po numerze.
        """

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT *
                FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()

        if row is None:
            return None

        return self._memory_row_to_dict(row)

    def recent(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Zwraca ostatnie trwałe wspomnienia.
        """

        if limit <= 0:
            return []

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            self._memory_row_to_dict(row)
            for row in rows
        ]

    def find_by_category(
        self,
        category: str,
    ) -> List[Dict[str, Any]]:
        """
        Odczytuje wspomnienia należące
        do wskazanej kategorii.
        """

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM memories
                WHERE category = ?
                ORDER BY id DESC
                """,
                (category,),
            ).fetchall()

        return [
            self._memory_row_to_dict(row)
            for row in rows
        ]

    def search(
        self,
        phrase: str,
    ) -> List[Dict[str, Any]]:
        """
        Wyszukuje frazę w tytule i treści pamięci.
        """

        phrase = phrase.strip()

        if not phrase:
            return []

        pattern = f"%{phrase}%"

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM memories
                WHERE title LIKE ?
                   OR content LIKE ?
                ORDER BY id DESC
                """,
                (
                    pattern,
                    pattern,
                ),
            ).fetchall()

        return [
            self._memory_row_to_dict(row)
            for row in rows
        ]

    def count(self) -> int:
        """
        Zwraca liczbę zwykłych trwałych wspomnień.
        """

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM memories
                """
            ).fetchone()

        return int(row["total"])

    def _memory_row_to_dict(
        self,
        row: sqlite3.Row,
    ) -> Dict[str, Any]:
        """
        Zamienia rekord pamięci SQLite
        na zwykły słownik.
        """

        return {
            "id": row["id"],
            "kategoria": row["category"],
            "tytul": row["title"],
            "tresc": row["content"],
            "zrodlo": row["source"],
            "metadane": json.loads(
                row["metadata"]
            ),
            "utworzono": row["created_at"],
        }

    # =========================================================
    # TRWAŁA HISTORIA ROZWOJU
    # =========================================================

    def save_development_entry(
        self,
        title: str,
        description: str,
        category: str,
        status: str,
        discovered_by: str,
        evidence: Optional[List[str]] = None,
        changes: Optional[List[str]] = None,
        test_results: Optional[List[str]] = None,
        unresolved: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> int:
        """
        Zapisuje doświadczenie rozwojowe FENIKSA
        w trwałej historii rozwoju.
        """

        if not title.strip():
            raise ValueError(
                "Tytuł doświadczenia rozwojowego "
                "nie może być pusty."
            )

        if not description.strip():
            raise ValueError(
                "Opis doświadczenia rozwojowego "
                "nie może być pusty."
            )

        if evidence is None:
            evidence = []

        if changes is None:
            changes = []

        if test_results is None:
            test_results = []

        if unresolved is None:
            unresolved = []

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        if created_at is None:
            created_at = now

        if updated_at is None:
            updated_at = now

        with self._connect() as connection:

            cursor = connection.execute(
                """
                INSERT INTO development_history (
                    title,
                    description,
                    category,
                    status,
                    discovered_by,
                    evidence,
                    changes,
                    test_results,
                    unresolved,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    description,
                    category,
                    status,
                    discovered_by,
                    json.dumps(
                        evidence,
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        changes,
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        test_results,
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        unresolved,
                        ensure_ascii=False,
                    ),
                    created_at,
                    updated_at,
                ),
            )

            connection.commit()

            return int(cursor.lastrowid)

    def development_history(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Odczytuje trwałą historię rozwoju FENIKSA.
        """

        with self._connect() as connection:

            if limit is None:

                rows = connection.execute(
                    """
                    SELECT *
                    FROM development_history
                    ORDER BY id DESC
                    """
                ).fetchall()

            else:

                if limit <= 0:
                    return []

                rows = connection.execute(
                    """
                    SELECT *
                    FROM development_history
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [
            self._development_row_to_dict(row)
            for row in rows
        ]

    def get_development_entry(
        self,
        entry_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Odczytuje pojedynczy wpis historii rozwoju.
        """

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT *
                FROM development_history
                WHERE id = ?
                """,
                (entry_id,),
            ).fetchone()

        if row is None:
            return None

        return self._development_row_to_dict(row)

    def find_development_by_category(
        self,
        category: str,
    ) -> List[Dict[str, Any]]:
        """
        Wyszukuje doświadczenia rozwojowe
        należące do określonej kategorii.
        """

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM development_history
                WHERE category = ?
                ORDER BY id DESC
                """,
                (category,),
            ).fetchall()

        return [
            self._development_row_to_dict(row)
            for row in rows
        ]

    def unresolved_development(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Zwraca wpisy posiadające nierozwiązane kwestie.
        """

        entries = self.development_history()

        return [
            entry
            for entry in entries
            if entry["nierozwiazane"]
        ]

    def development_count(self) -> int:
        """
        Zwraca liczbę trwałych wpisów rozwojowych.
        """

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM development_history
                """
            ).fetchone()

        return int(row["total"])

    def _development_row_to_dict(
        self,
        row: sqlite3.Row,
    ) -> Dict[str, Any]:
        """
        Zamienia rekord historii rozwoju
        na polski słownik danych.
        """

        return {
            "id": row["id"],
            "tytul": row["title"],
            "opis": row["description"],
            "kategoria": row["category"],
            "status": row["status"],
            "wykryto_przez": row["discovered_by"],
            "dowody": json.loads(
                row["evidence"]
            ),
            "zmiany": json.loads(
                row["changes"]
            ),
            "wyniki_testow": json.loads(
                row["test_results"]
            ),
            "nierozwiazane": json.loads(
                row["unresolved"]
            ),
            "utworzono": row["created_at"],
            "zaktualizowano": row["updated_at"],
        }

    # =========================================================
    # STAN PAMIĘCI
    # =========================================================

    def status(self) -> Dict[str, Any]:
        """
        Podaje podstawowy stan trwałej pamięci FENIKSA.
        """

        return {
            "baza_danych": str(
                self.database_path
            ),
            "liczba_wspomnien": self.count(),
            "liczba_wpisow_rozwoju":
                self.development_count(),
            "nierozwiazane_wpisy_rozwoju": len(
                self.unresolved_development()
            ),
            "gotowa": True,
        }