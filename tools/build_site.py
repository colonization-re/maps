#!/usr/bin/env python3
"""Build the static GitHub Pages catalog from maps.json."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from validate_archive import Validator


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
TEMPLATE_PATH = SITE_DIR / "index.template.html"
WEB_UI_VERSION_PATH = SITE_DIR / "WEB_UI_VERSION"
CATALOG_PATH = ROOT / "maps.json"
DEFAULT_OUTPUT = ROOT / "_site"
VERSION_PATTERN = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
RELEASE_URL = "https://github.com/colonization-re/web-ui/releases/download/{version}/{asset}"
USER_AGENT = "colonization-map-archive-site-builder/1"
MAX_CSS_BYTES = 2 * 1024 * 1024
MAX_CHECKSUM_BYTES = 64 * 1024


def escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


EXTERNAL_ICON = (
    '<svg class="archive-action-icon" aria-hidden="true" viewBox="0 0 24 24" '
    'width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M15 3h6v6"></path><path d="M10 14 21 3"></path>'
    '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>'
    '</svg>'
)

DOWNLOAD_ICON = (
    '<svg class="archive-action-icon" aria-hidden="true" viewBox="0 0 24 24" '
    'width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>'
    '<path d="M7 10l5 5 5-5"></path><path d="M12 15V3"></path>'
    '</svg>'
)

DETAILS_ICON = (
    '<svg class="archive-action-icon" aria-hidden="true" viewBox="0 0 24 24" '
    'width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="10"></circle>'
    '<path d="M12 16v-4"></path><path d="M12 8h.01"></path>'
    '</svg>'
)


def external_label(label: str) -> str:
    return f"{label}{EXTERNAL_ICON}"


def icon_label(icon: str, label: str) -> str:
    return f"{icon}{label}"


def map_card(entry: dict[str, Any]) -> str:
    map_id = escaped(entry["id"])
    modal_id = escaped(f"details-{entry['id']}")
    name = escaped(entry["name"])
    author = escaped(entry["author"])
    release_date = entry["release_date"]
    date_label = escaped(release_date) if release_date else "Unknown"
    date_markup = (
        f'<time datetime="{date_label}">{date_label}</time>'
        if release_date
        else '<span class="col-faint">Unknown</span>'
    )
    width = entry["size"]["width"]
    height = entry["size"]["height"]
    area = width * height
    tags = "".join(
        f'<span class="col-badge col-badge--brand archive-tag">{escaped(tag)}</span>'
        for tag in entry["tags"]
    )
    if not tags:
        tags = '<span class="col-meta">No tags</span>'

    source_link = entry.get("source_link")
    source_row = ""
    source_action = ""
    if source_link:
        source_row = (
            '<dt>Original source</dt>'
            f'<dd><a href="{escaped(source_link)}" target="_blank" '
            f'rel="noopener noreferrer">{external_label("View source")}</a></dd>'
        )
        source_action = (
            f'<a class="col-btn col-btn--quiet col-btn--sm" href="{escaped(source_link)}" '
            f'target="_blank" rel="noopener noreferrer">{external_label("Source")}</a>'
        )

    tag_list = " ".join(entry["tags"])
    search_text = " ".join(
        [entry["id"], entry["name"], entry["author"], *entry["tags"]]
    )
    file_link = escaped(entry["file_link"])
    preview_link = escaped(entry["preview_link"])
    full_preview_link = escaped(entry["full_preview_link"])

    return f"""      <article class="col-card col-card--hover archive-map-card" data-map-card data-search="{escaped(search_text)}" data-tags="{escaped(tag_list)}" data-sort-name="{name}" data-sort-date="{escaped(release_date or "")}" data-sort-size="{area}">
        <a class="archive-map-preview" href="{full_preview_link}" aria-label="View full-size map image for {name}" target="_blank" rel="noopener noreferrer">
          <img class="col-art" src="{preview_link}" alt="Preview of {name}" loading="lazy" decoding="async">
          <span class="archive-map-size col-mono col-tnum" aria-hidden="true">{width} × {height}</span>
        </a>
        <div class="archive-map-body">
          <h2>{name}</h2>
          <p class="archive-map-author">{author}</p>
          <div class="col-row archive-tags" aria-label="Map tags">{tags}</div>
          <div class="archive-map-footer">
            <div class="col-btnrow archive-map-actions">
              <a class="col-btn col-btn--sm" href="{file_link}" download>{icon_label(DOWNLOAD_ICON, "Download")}</a>
              <button class="col-btn col-btn--outline col-btn--sm" type="button" data-map-details-target="{modal_id}">{icon_label(DETAILS_ICON, "Details")}</button>
            </div>
          </div>
        </div>
        <dialog class="col-dialog archive-map-dialog" id="{modal_id}" data-map-details-dialog aria-labelledby="{modal_id}-title">
          <div class="col-dialog-head">
            <p class="col-eyebrow">{map_id}</p>
            <h3 id="{modal_id}-title">{name}</h3>
          </div>
          <div class="col-dialog-body">
            <img class="col-art archive-dialog-preview" src="{preview_link}" alt="Preview of {name}" loading="lazy" decoding="async">
            <dl class="col-dl archive-dialog-details">
              <dt>Author</dt><dd>{author}</dd>
              <dt>Released</dt><dd>{date_markup}</dd>
              <dt>Map size</dt><dd class="col-mono col-tnum">{width} × {height} tiles</dd>
              <dt>Tags</dt><dd><div class="col-row archive-tags">{tags}</div></dd>
              {source_row}
            </dl>
          </div>
          <div class="col-dialog-foot">
            {source_action}
            <a class="col-btn col-btn--outline col-btn--sm" href="{full_preview_link}" target="_blank" rel="noopener noreferrer">{external_label("Full image")}</a>
            <a class="col-btn col-btn--sm" href="{file_link}" download>{icon_label(DOWNLOAD_ICON, "Download")}</a>
            <button class="col-btn col-btn--ghost col-btn--sm" type="button" data-map-details-close>Close</button>
          </div>
        </dialog>
      </article>"""


def tag_filter_controls(entries: list[dict[str, Any]]) -> str:
    tags = sorted({tag for entry in entries for tag in entry["tags"]})
    return "\n".join(
        f"""                <label class="archive-tag-option">
                  <input type="checkbox" value="{escaped(tag)}" data-map-tag-option>
                  <span>{escaped(tag)}</span>
                </label>"""
        for tag in tags
    )


def catalog_content(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return """<section class="col-card col-card--ticks archive-empty" aria-labelledby="empty-title">
      <p class="col-eyebrow">Awaiting the first chart</p>
      <h2 id="empty-title">No maps have been archived yet</h2>
      <p class="col-dim">Have a custom map or a recovered download? Help start the collection.</p>
      <div class="col-btnrow">
        <a class="col-btn" href="https://github.com/colonization-re/maps/issues/new?template=map_submission.yml">Submit a map</a>
        <a class="col-btn col-btn--outline" href="https://github.com/colonization-re/maps/blob/main/CONTRIBUTING.md">Read the guide</a>
      </div>
    </section>"""

    cards = "\n".join(map_card(entry) for entry in entries)
    filters = tag_filter_controls(entries)
    map_word = "map" if len(entries) == 1 else "maps"
    return f"""<section aria-labelledby="maps-title">
      <div class="col-sectionhead"><h2 id="maps-title">Map catalog</h2></div>
      <div class="col-card archive-filter-panel">
        <div class="col-spread">
          <label class="col-field archive-search-field">
            <span class="col-label">Search maps</span>
            <input class="col-input" type="search" placeholder="Name, author, or tag" autocomplete="off" data-map-search>
          </label>
          <div class="col-field archive-tag-filter-field">
            <span class="col-label">Filter by tag</span>
            <div class="archive-tag-picker" data-map-tag-picker>
              <button class="col-input archive-tag-input" type="button" data-map-tag-toggle aria-expanded="false">
                <span class="archive-tag-value" data-map-tag-value>Any tag</span>
              </button>
              <div class="archive-tag-menu" data-map-tag-menu hidden>
{filters}
              </div>
            </div>
          </div>
          <label class="col-field archive-sort-field">
            <span class="col-label">Sort maps</span>
            <select class="col-input" data-map-sort>
              <option value="name-asc">A-Z</option>
              <option value="name-desc">Z-A</option>
              <option value="date-desc">Release date</option>
              <option value="size-desc">Map size</option>
            </select>
          </label>
          <div class="col-field archive-view-field">
            <span class="col-label">View</span>
            <div class="col-segmented archive-view-toggle" role="group" aria-label="Catalog view">
              <button type="button" data-map-view="gallery" aria-pressed="true">Gallery</button>
              <button type="button" data-map-view="list" aria-pressed="false">List</button>
            </div>
          </div>
          <div class="col-row">
            <p class="col-meta archive-filter-status" data-filter-status aria-live="polite">{len(entries)} of {len(entries)} {map_word} shown</p>
            <button class="col-btn col-btn--ghost col-btn--sm" type="button" data-clear-filters disabled>Clear</button>
          </div>
        </div>
      </div>
      <p class="col-note col-note--warn" data-no-results hidden>No maps match the current filters.</p>
      <div class="col-grid archive-map-grid" data-map-grid>
{cards}
      </div>
    </section>"""


def clean_output(output: Path) -> None:
    resolved = output.resolve()
    if resolved == ROOT or ROOT not in resolved.parents:
        raise ValueError("output directory must be inside the repository")
    if output.is_symlink():
        raise ValueError("output directory must not be a symbolic link")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)


def download(url: str, limit: int) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        content = response.read(limit + 1)
    if len(content) > limit:
        raise ValueError(f"release asset exceeds the {limit}-byte safety limit")
    return content


def web_ui_css(version: str, local_css: Path | None) -> bytes:
    if local_css is not None:
        content = local_css.read_bytes()
        if len(content) > MAX_CSS_BYTES:
            raise ValueError("local web-ui stylesheet exceeds the safety limit")
        return content

    css = download(RELEASE_URL.format(version=version, asset="col.min.css"), MAX_CSS_BYTES)
    manifest_bytes = download(
        RELEASE_URL.format(version=version, asset="SHA256SUMS.txt"),
        MAX_CHECKSUM_BYTES,
    )
    manifest = manifest_bytes.decode("ascii")
    expected = None
    for line in manifest.splitlines():
        checksum, separator, filename = line.partition("  ")
        if separator and filename == "col.min.css":
            expected = checksum
            break
    if expected is None or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("release checksum manifest has no valid col.min.css entry")
    actual = hashlib.sha256(css).hexdigest()
    if actual != expected:
        raise ValueError(f"web-ui stylesheet checksum mismatch: expected {expected}, got {actual}")
    return css


def copy_archive(entries: list[dict[str, Any]], output: Path) -> None:
    shutil.copy2(CATALOG_PATH, output / "maps.json")
    shutil.copy2(ROOT / "maps.schema.json", output / "maps.schema.json")
    for entry in entries:
        for field in ("file_link", "preview_link", "full_preview_link"):
            relative = Path(entry[field])
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)


def build(output: Path, local_css: Path | None = None) -> None:
    validator = Validator()
    validator.validate()
    if validator.errors:
        details = "\n".join(f"- {error}" for error in validator.errors)
        raise ValueError(f"archive validation failed:\n{details}")

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    entries = catalog["maps"]
    web_ui_version = WEB_UI_VERSION_PATH.read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(web_ui_version):
        raise ValueError("site/WEB_UI_VERSION must contain a tag such as v1.1.0")
    stylesheet = web_ui_css(web_ui_version, local_css)

    replacements = {
        "{{WEB_UI_VERSION}}": escaped(web_ui_version),
        "{{CATALOG_VERSION}}": escaped(catalog["catalog_version"]),
        "{{CATALOG_CONTENT}}": catalog_content(entries),
    }
    page = TEMPLATE_PATH.read_text(encoding="utf-8")
    for marker, value in replacements.items():
        page = page.replace(marker, value)
    unresolved = re.findall(r"{{[A-Z_]+}}", page)
    if unresolved:
        raise ValueError(f"unresolved template markers: {', '.join(unresolved)}")

    clean_output(output)
    (output / "assets").mkdir()
    shutil.copy2(SITE_DIR / "assets" / "site.css", output / "assets" / "site.css")
    shutil.copy2(SITE_DIR / "assets" / "site.js", output / "assets" / "site.js")
    shutil.copy2(
        SITE_DIR / "assets" / "ship-leaving-europe.png",
        output / "assets" / "ship-leaving-europe.png",
    )
    (output / "assets" / "col.min.css").write_bytes(stylesheet)
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / ".nojekyll").touch()
    copy_archive(entries, output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="output directory inside the repository (default: _site)",
    )
    parser.add_argument(
        "--web-ui-css",
        type=Path,
        help="use a local col.min.css instead of downloading the pinned release",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    try:
        build(output, args.web_ui_css)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Site build failed: {exc}", file=sys.stderr)
        return 1
    print(f"Static catalog built at {output.resolve().relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
