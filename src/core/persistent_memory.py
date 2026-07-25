import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class PersistentMemory:
    """
    Trwała pamięć FENIKS OS.

    Dane są przechowywane w lokalnej bazie SQLite
    i pozostają dostępne po zamknięciu programu.

    Ta warstwa nie zastępuje pamięci roboczej.
    Jej zadaniem jest trwałe przechowywanie informacji,
    które mają przetrwać kolejne uruchomienia FENIKSA.
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
            self.database_path = Path(database_path)

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
        Tworzy podstawową strukturę bazy,
        jeżeli jeszcze nie istnieje.
        """

        with self._connect() as connection:
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

            connection.commit()

    def save(
        self,
        category: str,
        title: str,
        content: str,
        source: str = "FENIKS",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Trwale zapisuje informację.

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
        Odczytuje pojedynczy wpis po jego numerze.
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

        return self._row_to_dict(row)

    def recent(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Zwraca ostatnie zapisane informacje.
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
            self._row_to_dict(row)
            for row in rows
        ]

    def find_by_category(
        self,
        category: str,
    ) -> List[Dict[str, Any]]:
        """
        Odczytuje wpisy należące do wskazanej kategorii.
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
            self._row_to_dict(row)
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
            self._row_to_dict(row)
            for row in rows
        ]

    def count(self) -> int:
        """
        Zwraca liczbę trwałych wpisów.
        """

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM memories
                """
            ).fetchone()

        return int(row["total"])

    def _row_to_dict(
        self,
        row: sqlite3.Row,
    ) -> Dict[str, Any]:
        """
        Zamienia rekord SQLite na zwykły słownik.
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

    def status(self) -> Dict[str, Any]:
        """
        Podaje podstawowy stan trwałej pamięci.
        """

        return {
            "baza_danych": str(
                self.database_path
            ),
            "liczba_wpisow": self.count(),
            "gotowa": True,
        }