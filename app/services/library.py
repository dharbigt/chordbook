# SPDX-License-Identifier: GPL-3.0-or-later

import html
import json
import os
import random
import base64
import tempfile
from datetime import date
from pathlib import Path
from typing import Any


TEXT_FIELDS = [
    "contributor",
    "author",
    "songwriter",
    "artist",
    "composer",
    "lyricist",
    "production",
    "album",
    "year",
    "date",
    "comment",
]

EXTRA_FIELDS = ["genre", "instrument", "tempo"]

GENRE_OPTIONS = [
    "Blues",
    "Country/Bluegrass",
    "Dance/Electronica",
    "Formal/Classical",
    "Industrial/Post-Rock",
    "Jazz",
    "Musical/Soundtrack",
    "Pop/Rock",
    "Reggae/Soca/Calypso",
    "Soul/R&B",
    "Traditional/Folk/Roots",
]

TEMPO_OPTIONS = [
    "Larghissimo (24 BPM and under)",
    "Grave (25-45 BPM)",
    "Lento (45-50 BPM)",
    "Largo (50-55 BPM)",
    "Larghetto (55-60 BPM)",
    "Adagio (60-72 BPM)",
    "Adagretto (72-80 BPM)",
    "Andantino (80-84 BPM)",
    "Andante (84-90 BPM)",
    "Andante moderato (90-96 BPM)",
    "Marcia moderato (83-85 BPM)",
    "Moderato (96-108 BPM)",
    "Allegro moderato (108-112 BPM)",
    "Allegretto (112-120 BPM)",
    "Allegro (120-128 BPM)",
    "Vivace (132-144 BPM)",
    "Vivacissimo (144-160 BPM)",
    "Allegrissimo (145-167 BPM)",
    "Presto (168-200 BPM)",
    "Prestissimo (200 BPM and over)",
]

EDITABLE_FIELDS = set(TEXT_FIELDS + EXTRA_FIELDS + ["title", "rating"])


class LibraryService:
    def __init__(self, text_dir: Path):
        self.text_dir = text_dir

    def get_files(self) -> list[str]:
        if not self.text_dir.exists():
            return []
        files = [
            p.name
            for p in self.text_dir.iterdir()
            if p.is_file() and not p.name.startswith(".")
        ]
        return sorted(files)

    def get_random_file(self) -> str | None:
        files = self.get_files()
        return random.choice(files) if files else None

    def get_random_filtered_file(self, query: str, query_field: str) -> str | None:
        genre_lookup = {option.lower(): option for option in GENRE_OPTIONS}
        matches = []
        for filename in self.get_files():
            header = self.parse_header(filename)
            if query == "_unset" and query_field == "genre":
                genre_value = str(header.get("genre", "")).strip().lower()
                if genre_value in genre_lookup:
                    continue
            elif query_field == "*":
                haystack = " ".join(str(v) for v in header.values())
                if query.lower() not in haystack.lower():
                    continue
            else:
                haystack = str(header.get(query_field, ""))
                if query.lower() not in haystack.lower():
                    continue
            matches.append(filename)
        return random.choice(matches) if matches else self.get_random_file()

    def get_file_contents(self, filename: str) -> str:
        safe_name = self.validate_filename(filename)
        text = (self.text_dir / safe_name).read_text(encoding="utf-8", errors="ignore")
        if text.startswith(chr(1)):
            pivot = text.find(chr(2))
            if pivot != -1:
                return text[pivot + 1 :]
        return text

    def get_file_header(self, filename: str) -> str:
        safe_name = self.validate_filename(filename)
        text = (self.text_dir / safe_name).read_text(encoding="utf-8", errors="ignore")
        if text.startswith(chr(1)):
            pivot = text.find(chr(2))
            if pivot != -1:
                return text[1:pivot]
        return ""

    def file_exists(self, filename: str) -> bool:
        safe_name = self.validate_filename(filename)
        return (self.text_dir / safe_name).exists()

    def create_file(self, filename: str, body: str, header: dict[str, Any] | None = None) -> str:
        safe_name = self.validate_filename(filename, add_txt_extension=True)
        target = self.text_dir / safe_name
        if target.exists():
            raise FileExistsError(f"File already exists: {safe_name}")
        merged_header = header or {}
        if not merged_header.get("date"):
            merged_header = {**merged_header, "date": date.today().isoformat()}
        normalized_header = self._normalize_header(safe_name, merged_header)
        payload = f"{chr(1)}{self._safe_json_dumps(normalized_header)}{chr(2)}{self._sanitize_text(body)}"
        self.text_dir.mkdir(parents=True, exist_ok=True)
        self._write_payload_atomic(target, payload)
        return safe_name

    def save_file_content(self, filename: str, body: str, header_updates: dict[str, Any] | None = None) -> None:
        safe_name = self.validate_filename(filename)
        target = self.text_dir / safe_name
        if not target.exists():
            raise FileNotFoundError(f"File does not exist: {safe_name}")

        current_header = self.parse_header(safe_name)
        if header_updates:
            for key, value in header_updates.items():
                current_header[str(key).lower()] = value

        normalized_header = self._normalize_header(safe_name, current_header)
        payload = f"{chr(1)}{self._safe_json_dumps(normalized_header)}{chr(2)}{self._sanitize_text(body)}"
        self._write_payload_atomic(target, payload)

    def update_file_header(self, filename: str, key: str, value: Any) -> None:
        header = self._safe_json(self.get_file_header(filename))
        body = self.get_file_contents(filename)
        header[key.lower()] = self._sanitize_text(value)
        payload = f"{chr(1)}{self._safe_json_dumps(self._normalize_header(filename, header))}{chr(2)}{self._sanitize_text(body)}"
        self._write_payload_atomic(self.text_dir / self.validate_filename(filename), payload)

    def parse_header(self, filename: str) -> dict[str, Any]:
        header_text = self.get_file_header(filename)
        header = self._safe_json(header_text)

        if not header:
            header = {
                "title": self.get_document_name(filename),
                "artist": self.get_document_author(filename),
                "rating": 1,
                "count": 0,
            }

        if not header.get("title"):
            header["title"] = self.get_document_name(filename)

        if not header.get("artist"):
            header["artist"] = self.get_document_author(filename)

        if not header.get("date"):
            stat = (self.text_dir / self.validate_filename(filename)).stat()
            header["date"] = date.fromtimestamp(stat.st_mtime).isoformat()

        for field in TEXT_FIELDS:
            header.setdefault(field, "")

        for field in EXTRA_FIELDS:
            header.setdefault(field, "")

        header["rating"] = self._coerce_int(header.get("rating", 0), default=0)
        header["count"] = self._coerce_int(header.get("count", 0), default=0)

        # Keep file headers normalized to simplify search/sort and future migrations.
        self._write_header_if_changed(filename, header)
        return header

    def get_document_name(self, filename: str) -> str:
        stem = filename.removesuffix(".txt")
        bits = stem.split("--", 1)
        if len(bits) == 1:
            return stem.replace("_", " ").title()
        return bits[1].replace("_", " ").title()

    def get_document_author(self, filename: str) -> str:
        stem = filename.removesuffix(".txt")
        bits = stem.split("--", 1)
        author = bits[0]

        parties = author.split("_and_", 1)
        if len(parties) > 1:
            left = self._flip_comma_name(parties[0])
            author = f"{left} and {parties[1]}"
        else:
            author = self._flip_comma_name(parties[0])

        return author.replace("_", " ").title()

    def build_index_rows(
        self,
        sort_by: str,
        order: str,
        min_count: int,
        min_rating: int,
        query: str,
        query_field: str,
    ) -> tuple[list[dict[str, Any]], set[str], dict[str, dict[str, int]]]:
        rows: list[dict[str, Any]] = []
        all_fields: set[str] = set(TEXT_FIELDS + EXTRA_FIELDS + ["title", "count", "rating"])
        facets = {
            "genre": {option: 0 for option in GENRE_OPTIONS} | {"_unset": 0},
            "tempo": {option: 0 for option in TEMPO_OPTIONS},
        }
        genre_lookup = {option.lower(): option for option in GENRE_OPTIONS}
        tempo_lookup = {option.lower(): option for option in TEMPO_OPTIONS}

        for filename in self.get_files():
            header = self.parse_header(filename)
            all_fields.update(header.keys())

            if header.get("count", 0) <= min_count:
                continue
            if header.get("rating", 0) <= min_rating:
                continue

            genre_value = str(header.get("genre", "")).strip().lower()
            if genre_value in genre_lookup:
                facets["genre"][genre_lookup[genre_value]] += 1
            else:
                facets["genre"]["_unset"] += 1

            tempo_value = str(header.get("tempo", "")).strip().lower()
            if tempo_value in tempo_lookup:
                facets["tempo"][tempo_lookup[tempo_value]] += 1

            if query:
                if query == "_unset" and query_field == "genre":
                    if genre_value in genre_lookup:
                        continue
                elif query_field == "*":
                    haystack = " ".join(str(v) for v in header.values())
                    if query.lower() not in haystack.lower():
                        continue
                else:
                    haystack = str(header.get(query_field, ""))
                    if query.lower() not in haystack.lower():
                        continue

            rows.append(
                {
                    "filename": filename,
                    "file_token": base64.urlsafe_b64encode(os.fsencode(filename)).decode("ascii"),
                    "name": self.get_document_name(filename),
                    "author": self.get_document_author(filename),
                    "header": header,
                }
            )

        reverse = order.upper() == "DESC"

        def sort_key(item: dict[str, Any]) -> tuple[int, Any]:
            if sort_by == "title":
                return (1, str(item.get("name", "")).lower())
            if sort_by == "artist":
                return (1, str(item["header"].get("artist", "")).lower())

            value = item["header"].get(sort_by, "")
            if sort_by in {"count", "rating", "year"}:
                return (0, self._coerce_int(value, default=0))
            return (1, str(value).lower())

        rows.sort(key=sort_key, reverse=reverse)
        return rows, all_fields, facets

    @staticmethod
    def escape_text(value: str) -> str:
        return html.escape(value)

    @staticmethod
    def _safe_json(payload: str) -> dict[str, Any]:
        if not payload:
            return {}
        try:
            parsed = json.loads(payload)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _write_header_if_changed(self, filename: str, header: dict[str, Any]) -> None:
        existing = self._safe_json(self.get_file_header(filename))
        normalized = self._normalize_header(filename, header)
        if existing == normalized:
            return
        body = self.get_file_contents(filename)
        payload = f"{chr(1)}{self._safe_json_dumps(normalized)}{chr(2)}{self._sanitize_text(body)}"
        self._write_payload_atomic(self.text_dir / self.validate_filename(filename), payload)

    def _safe_json_dumps(self, value: dict[str, Any]) -> str:
        return json.dumps(self._sanitize_text(value), ensure_ascii=False)

    def _normalize_header(self, filename: str, header: dict[str, Any]) -> dict[str, Any]:
        normalized = {str(k).lower(): self._sanitize_text(v) for k, v in header.items()}

        if not normalized.get("title"):
            normalized["title"] = self.get_document_name(filename)
        if not normalized.get("artist"):
            normalized["artist"] = self.get_document_author(filename)

        for field in TEXT_FIELDS:
            normalized.setdefault(field, "")
        for field in EXTRA_FIELDS:
            normalized.setdefault(field, "")

        normalized["rating"] = self._coerce_int(normalized.get("rating", 0), default=0)
        normalized["count"] = self._coerce_int(normalized.get("count", 0), default=0)
        return normalized

    @staticmethod
    def validate_filename(filename: str, add_txt_extension: bool = False) -> str:
        safe_name = os.path.basename(str(filename or "").strip())
        if not safe_name:
            raise ValueError("Filename is required")
        if safe_name.startswith("."):
            raise ValueError("Hidden files are not allowed")
        if "/" in safe_name or "\\" in safe_name:
            raise ValueError("Invalid filename")
        if any(ord(ch) < 32 for ch in safe_name):
            raise ValueError("Invalid filename")
        if add_txt_extension and not safe_name.lower().endswith(".txt"):
            safe_name = f"{safe_name}.txt"
        return safe_name

    @staticmethod
    def _write_payload_atomic(target: Path, payload: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as tmp:
            tmp.write(payload)
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, target)

    @staticmethod
    def _flip_comma_name(value: str) -> str:
        split_name = value.split(",", 1)
        if len(split_name) > 1:
            return f"{split_name[1]} {split_name[0]}".strip()
        return split_name[0]

    @staticmethod
    def _coerce_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _sanitize_text(value: Any) -> Any:
        if isinstance(value, str):
            # Strip malformed surrogate code points from legacy text before UTF-8 writes.
            return value.encode("utf-8", errors="replace").decode("utf-8")
        if isinstance(value, dict):
            return {str(k): LibraryService._sanitize_text(v) for k, v in value.items()}
        if isinstance(value, list):
            return [LibraryService._sanitize_text(v) for v in value]
        return value
