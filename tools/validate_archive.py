#!/usr/bin/env python3
"""Validate the map catalog and all locally referenced assets."""

from __future__ import annotations

import json
import re
import stat
import struct
import sys
import zipfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "maps.json"
MAPS_DIR = ROOT / "maps"
MAX_FILE_SIZE = 100 * 1024 * 1024
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_PATTERN = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[a-zA-Z]:[/\\]")
EXECUTABLE_SUFFIXES = {".bat", ".cmd", ".com", ".dll", ".exe", ".msi", ".scr"}
ALLOWED_FIELDS = {
    "id",
    "name",
    "author",
    "release_date",
    "size",
    "tags",
    "source_link",
    "file_link",
    "preview_link",
    "full_preview_link",
}
REQUIRED_FIELDS = ALLOWED_FIELDS - {"source_link"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class Validator:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, location: str, message: str) -> None:
        self.errors.append(f"{location}: {message}")

    def load_catalog(self) -> dict[str, Any] | None:
        try:
            with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
                data = json.load(catalog_file)
        except (OSError, json.JSONDecodeError) as exc:
            self.error("maps.json", str(exc))
            return None

        if not isinstance(data, dict):
            self.error("maps.json", "top-level value must be an object")
            return None

        allowed = {"$schema", "catalog_version", "maps"}
        unknown = set(data) - allowed
        if unknown:
            self.error("maps.json", f"unknown fields: {', '.join(sorted(unknown))}")
        if data.get("catalog_version") != 1:
            self.error("maps.json.catalog_version", "must be 1")
        if not isinstance(data.get("maps"), list):
            self.error("maps.json.maps", "must be an array")
            return None
        return data

    def validate(self) -> None:
        catalog = self.load_catalog()
        if catalog is None:
            return

        entries = catalog["maps"]
        ids: set[str] = set()
        listed_ids: set[str] = set()
        previous_id: str | None = None

        for index, entry in enumerate(entries):
            location = f"maps.json.maps[{index}]"
            if not isinstance(entry, dict):
                self.error(location, "must be an object")
                continue
            map_id = entry.get("id")
            if isinstance(map_id, str):
                listed_ids.add(map_id)
            self.validate_entry(entry, location)
            if not isinstance(map_id, str):
                continue
            if map_id in ids:
                self.error(f"{location}.id", f"duplicate ID {map_id!r}")
            ids.add(map_id)
            if previous_id is not None and map_id < previous_id:
                self.error(location, "entries must be sorted by ID")
            previous_id = map_id

        if not MAPS_DIR.is_dir():
            self.error("maps", "directory does not exist")
            return
        actual_ids = {path.name for path in MAPS_DIR.iterdir() if path.is_dir()}
        for unlisted in sorted(actual_ids - listed_ids):
            self.error(f"maps/{unlisted}", "directory has no catalog entry")
        for missing in sorted(listed_ids - actual_ids):
            self.error(f"maps/{missing}", "catalog entry has no directory")

    def validate_entry(self, entry: dict[str, Any], location: str) -> None:
        unknown = set(entry) - ALLOWED_FIELDS
        missing = REQUIRED_FIELDS - set(entry)
        if unknown:
            self.error(location, f"unknown fields: {', '.join(sorted(unknown))}")
        if missing:
            self.error(location, f"missing fields: {', '.join(sorted(missing))}")

        map_id = entry.get("id")
        if not isinstance(map_id, str) or not ID_PATTERN.fullmatch(map_id):
            self.error(f"{location}.id", "must be a lowercase, hyphen-separated ID")
            return

        for field in ("name", "author"):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                self.error(f"{location}.{field}", "must be a non-empty string")

        self.validate_date(entry.get("release_date"), f"{location}.release_date")
        self.validate_size(entry.get("size"), f"{location}.size")
        self.validate_tags(entry.get("tags"), f"{location}.tags")

        if "source_link" in entry:
            source = entry["source_link"]
            if not isinstance(source, str):
                self.error(f"{location}.source_link", "must be an HTTP(S) URL")
            else:
                parsed = urlparse(source)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    self.error(f"{location}.source_link", "must be an HTTP(S) URL")

        expected_paths = {
            "file_link": f"maps/{map_id}/{map_id}.zip",
            "preview_link": f"maps/{map_id}/{map_id}_preview.png",
            "full_preview_link": f"maps/{map_id}/{map_id}_full.png",
        }
        for field, expected in expected_paths.items():
            value = entry.get(field)
            field_location = f"{location}.{field}"
            if value != expected:
                self.error(field_location, f"must be {expected!r}")
                continue
            self.validate_asset(value, field_location)

        map_dir = MAPS_DIR / map_id
        if map_dir.is_dir():
            expected_names = {PurePosixPath(path).name for path in expected_paths.values()}
            actual_names = {path.name for path in map_dir.iterdir()}
            for extra in sorted(actual_names - expected_names):
                self.error(f"maps/{map_id}/{extra}", "unexpected file or directory")

    def validate_date(self, value: Any, location: str) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            self.error(location, "must be YYYY-MM-DD, YYYY-MM, YYYY, or null")
            return
        match = DATE_PATTERN.fullmatch(value)
        if not match:
            self.error(location, "must be YYYY-MM-DD, YYYY-MM, YYYY, or null")
            return
        year, month, day = match.groups()
        try:
            if int(year) < 1:
                raise ValueError
            if month and day:
                date(int(year), int(month), int(day))
            elif month and not 1 <= int(month) <= 12:
                raise ValueError
        except ValueError:
            self.error(location, "is not a valid calendar date")

    def validate_size(self, value: Any, location: str) -> None:
        if not isinstance(value, dict):
            self.error(location, "must contain integer width and height")
            return
        if set(value) != {"width", "height"}:
            self.error(location, "must contain only width and height")
        for dimension in ("width", "height"):
            number = value.get(dimension)
            if isinstance(number, bool) or not isinstance(number, int) or number < 1:
                self.error(f"{location}.{dimension}", "must be a positive integer")

    def validate_tags(self, value: Any, location: str) -> None:
        if not isinstance(value, list):
            self.error(location, "must be an array")
            return
        seen: set[str] = set()
        for index, tag in enumerate(value):
            tag_location = f"{location}[{index}]"
            if not isinstance(tag, str) or not ID_PATTERN.fullmatch(tag):
                self.error(tag_location, "must be lowercase and hyphen-separated")
            elif tag in seen:
                self.error(tag_location, f"duplicate tag {tag!r}")
            else:
                seen.add(tag)
        all_tags_are_strings = all(isinstance(tag, str) for tag in value)
        if all_tags_are_strings and value != sorted(value):
            self.error(location, "must be sorted alphabetically")

    def validate_asset(self, relative: str, location: str) -> None:
        path = ROOT / relative
        if not path.is_file():
            self.error(location, f"file does not exist: {relative}")
            return
        if path.is_symlink():
            self.error(location, "must not be a symbolic link")
            return
        if path.stat().st_size > MAX_FILE_SIZE:
            self.error(location, "file exceeds GitHub's 100 MiB limit")
        if path.suffix == ".png":
            self.validate_png(path, location)
        elif path.suffix == ".zip":
            self.validate_zip(path, location)

    def validate_png(self, path: Path, location: str) -> None:
        try:
            header = path.read_bytes()[:24]
            if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
                self.error(location, "is not a valid PNG file")
                return
            width, height = struct.unpack(">II", header[16:24])
            if width == 0 or height == 0:
                self.error(location, "PNG dimensions must be non-zero")
        except OSError as exc:
            self.error(location, str(exc))

    def validate_zip(self, path: Path, location: str) -> None:
        if not zipfile.is_zipfile(path):
            self.error(location, "is not a valid ZIP file")
            return
        try:
            with zipfile.ZipFile(path) as archive:
                members = archive.infolist()
                if not members:
                    self.error(location, "ZIP file is empty")
                folded_names: set[str] = set()
                for member in members:
                    normalized_name = member.filename.replace("\\", "/")
                    member_path = PurePosixPath(normalized_name)
                    if (
                        member_path.is_absolute()
                        or WINDOWS_ABSOLUTE_PATTERN.match(member.filename)
                        or ".." in member_path.parts
                    ):
                        self.error(location, f"ZIP has unsafe path: {member.filename!r}")
                    if PurePosixPath(normalized_name).suffix.casefold() in EXECUTABLE_SUFFIXES:
                        self.error(location, f"ZIP contains an executable: {member.filename!r}")
                    folded = member.filename.casefold()
                    if folded in folded_names:
                        self.error(location, f"ZIP has duplicate path: {member.filename!r}")
                    folded_names.add(folded)
                    unix_mode = member.external_attr >> 16
                    if stat.S_ISLNK(unix_mode):
                        self.error(location, f"ZIP contains a symbolic link: {member.filename!r}")
                    if member.flag_bits & 0x1:
                        self.error(location, f"ZIP contains an encrypted file: {member.filename!r}")
                corrupt = archive.testzip()
                if corrupt:
                    self.error(location, f"ZIP member failed CRC check: {corrupt!r}")
        except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
            self.error(location, str(exc))


def main() -> int:
    validator = Validator()
    validator.validate()
    if validator.errors:
        print(f"Archive validation failed with {len(validator.errors)} error(s):", file=sys.stderr)
        for error in validator.errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Archive validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
