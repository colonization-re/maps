#!/bin/sh
# Update each catalog entry's playable map dimensions from the map file on disk.
#
#   tools/update_maps_metada.sh [--only ID] [--check]
#
# The tool crawls `maps/**/*.mp` and `maps/**/*.zip`. For ZIP files it uses the
# same playable-member rule as the archive validator and preview renderer: ignore
# directories, `__MACOSX`, and `._` resource forks, then require exactly one
# `.mp`. The `.MP` header stores the full 58x72 grid, including the outer edge
# used by the game; catalog metadata records the playable interior, so this
# writes `(header_width - 2) x (header_height - 2)`. The full file length is
# still checked with the format arithmetic used by win-tools:
#
#   6 + 3 * width * height == file size
#
#   --only ID   just that map
#   --check     compare against maps.json and exit 1 if any size differs
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ONLY=
CHECK=0

die() { echo "update_maps_metada: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
    case $1 in
        --only) [ $# -ge 2 ] || die "--only needs a map id"; ONLY=$2; shift 2 ;;
        --check) CHECK=1; shift ;;
        -h|--help) sed -n '2,22p' "$0" | cut -c3-; exit 0 ;;
        *) die "unknown option: $1" ;;
    esac
done

python3 - "$ROOT" "$ONLY" "$CHECK" <<'PY'
import json
import struct
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

root = Path(sys.argv[1])
only = sys.argv[2]
check = sys.argv[3] == "1"
catalog_path = root / "maps.json"
maps_dir = root / "maps"

MP_HEADER = 6
MP_PLANES = 3


class MetadataError(Exception):
    pass


@dataclass(frozen=True)
class MapSource:
    map_id: str
    relative: str
    raw_width: int
    raw_height: int
    note: str = ""


def playable_zip_members(archive):
    members = []
    for member in archive.infolist():
        name = PurePosixPath(member.filename.replace("\\", "/"))
        if member.is_dir() or name.suffix.casefold() != ".mp":
            continue
        if "__MACOSX" in name.parts or name.name.startswith("._"):
            continue
        members.append(member)
    return members


def decode_mp(data, location):
    if len(data) < MP_HEADER:
        raise MetadataError(f"{location}: too short for a .MP header")
    width, height, _ = struct.unpack_from("<HHH", data, 0)
    if width == 0 or height == 0:
        raise MetadataError(f"{location}: MP dimensions must be non-zero")
    expected = MP_HEADER + MP_PLANES * width * height
    if expected != len(data):
        raise MetadataError(
            f"{location}: not a .MP: 6 + 3*{width}*{height} = "
            f"{expected} but the file is {len(data)} bytes"
        )
    if width <= 2 or height <= 2:
        raise MetadataError(f"{location}: MP grid is too small to have a playable interior")
    return width, height


def source_id(path):
    try:
        relative = path.relative_to(maps_dir)
    except ValueError:
        raise MetadataError(f"{path}: not under {maps_dir}") from None
    if len(relative.parts) < 2:
        raise MetadataError(f"{path}: expected maps/<id>/<file>")
    return relative.parts[0]


def rel(path):
    return path.relative_to(root).as_posix()


def read_mp(path):
    width, height = decode_mp(path.read_bytes(), rel(path))
    return MapSource(source_id(path), rel(path), width, height)


def read_zip(path):
    location = rel(path)
    if not zipfile.is_zipfile(path):
        raise MetadataError(f"{location}: is not a valid ZIP file")
    with zipfile.ZipFile(path) as archive:
        members = playable_zip_members(archive)
        if len(members) != 1:
            raise MetadataError(
                f"{location}: expected exactly one playable .mp member, "
                f"found {len(members)}"
            )
        data = archive.read(members[0])
    width, height = decode_mp(data, f"{location} member {members[0].filename!r}")
    return MapSource(
        source_id(path),
        location,
        width,
        height,
        f" (from {Path(location).name}: {members[0].filename})",
    )


def discover_sources():
    by_id = {}
    errors = []
    for path in sorted(maps_dir.rglob("*")):
        suffix = path.suffix.casefold()
        if suffix not in {".mp", ".zip"}:
            continue
        try:
            source = read_zip(path) if suffix == ".zip" else read_mp(path)
        except (OSError, zipfile.BadZipFile, RuntimeError, MetadataError) as exc:
            errors.append(str(exc))
            continue
        if only and source.map_id != only:
            continue
        by_id.setdefault(source.map_id, []).append(source)
    return by_id, errors


with catalog_path.open(encoding="utf-8") as catalog_file:
    catalog = json.load(catalog_file)

sources_by_id, errors = discover_sources()
for error in errors:
    print(f"  error: {error}", file=sys.stderr)

changed = 0
checked = 0
missing = 0
ambiguous = 0
catalog_ids = set()

for entry in catalog["maps"]:
    map_id = entry.get("id")
    if not isinstance(map_id, str):
        continue
    catalog_ids.add(map_id)
    if only and map_id != only:
        continue

    sources = sources_by_id.get(map_id, [])
    if not sources:
        print(f"  {map_id}: no .mp or .zip source found", file=sys.stderr)
        missing += 1
        continue
    if len(sources) != 1:
        names = ", ".join(source.relative for source in sources)
        print(f"  {map_id}: expected one source, found {names}", file=sys.stderr)
        ambiguous += 1
        continue

    source = sources[0]
    old_size = entry.get("size")
    playable_width = source.raw_width - 2
    playable_height = source.raw_height - 2
    new_size = {"width": playable_width, "height": playable_height}
    checked += 1
    if old_size == new_size:
        print(
            f"  {map_id}: {playable_width}x{playable_height} unchanged"
            f" (raw {source.raw_width}x{source.raw_height}){source.note}"
        )
        continue

    print(
        f"  {map_id}: "
        f"{old_size.get('width') if isinstance(old_size, dict) else '?'}x"
        f"{old_size.get('height') if isinstance(old_size, dict) else '?'} -> "
        f"{playable_width}x{playable_height} "
        f"(raw {source.raw_width}x{source.raw_height}){source.note}"
    )
    entry["size"] = new_size
    changed += 1

for map_id in sorted(set(sources_by_id) - catalog_ids):
    print(f"  {map_id}: source exists but has no catalog entry", file=sys.stderr)

if only and checked == 0 and missing == 0 and ambiguous == 0:
    raise SystemExit(f"update_maps_metada: no map called {only}")

if errors or missing or ambiguous:
    raise SystemExit(1)

if check:
    print(f"checked {checked} map(s), {changed} size(s) differ")
    raise SystemExit(1 if changed else 0)

if changed:
    with catalog_path.open("w", encoding="utf-8") as catalog_file:
        json.dump(catalog, catalog_file, indent=2)
        catalog_file.write("\n")
print(f"updated {changed} of {checked} map(s)")
PY
