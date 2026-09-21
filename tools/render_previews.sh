#!/bin/sh
# Re-render every map's two preview images from the map file the catalog names.
#
#   tools/render_previews.sh [--only ID] [--check] [--game DIR] [--colwin PATH]
#
# For each entry in maps.json it takes `file_link` -- either `<id>.mp` or a
# `<id>.zip` holding exactly one playable `.mp`, which is what the validator
# allows -- and writes
#
#   maps/<id>/<id>_full.png       1856 x 2304 for a 58 x 72 map, 32 px a square
#   maps/<id>/<id>_preview.png    464 x 576,   8 px a square
#
# The drawing is done by `colwin map-preview` from the sibling win-tools
# repository, which needs an installed copy of the game to take the artwork
# from. Neither this repository nor that one contains the game.
#
#   --only ID     just that map
#   --check       render to a temporary directory and compare, changing nothing;
#                 exits 1 if any committed image differs. Useful after changing
#                 the renderer, but note it compares BYTES: a different zlib --
#                 another Python, another platform -- can re-encode the same
#                 picture differently and report a difference that is not one.
#   --game DIR    the installed game; default $COLWIN_GAME
#   --colwin PATH colwin.py; default $COLWIN, else ../win-tools/colwin.py
#
# Requires Python 3.9+ and nothing else, like the rest of this repository.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ONLY=
CHECK=0
GAME=${COLWIN_GAME:-}
COLWIN=${COLWIN:-"$ROOT/../win-tools/colwin.py"}
FULL_TILE=32
PREVIEW_TILE=8

die() { echo "render_previews: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
    case $1 in
        --only) [ $# -ge 2 ] || die "--only needs a map id"; ONLY=$2; shift 2 ;;
        --check) CHECK=1; shift ;;
        --game) [ $# -ge 2 ] || die "--game needs a directory"; GAME=$2; shift 2 ;;
        --colwin) [ $# -ge 2 ] || die "--colwin needs a path"; COLWIN=$2; shift 2 ;;
        -h|--help) sed -n '2,27p' "$0" | cut -c3-; exit 0 ;;
        *) die "unknown option: $1" ;;
    esac
done

[ -n "$GAME" ] || die "no game directory: pass --game DIR or set COLWIN_GAME.
The map art is read out of the install's COLDATA1.DLL; this repository does not
contain the game."
[ -d "$GAME" ] || die "--game $GAME is not a directory"
[ -f "$COLWIN" ] || die "no colwin.py at $COLWIN.
Clone https://github.com/colonization-re/win-tools beside this repository, or
pass --colwin PATH."

WORK=$(mktemp -d) || die "cannot make a temporary directory"
trap 'rm -rf "$WORK"' EXIT INT TERM

# id and source file of every catalogued map, one per line.
catalog() {
    python3 - "$ROOT/maps.json" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    for entry in json.load(f)["maps"]:
        print("%s\t%s" % (entry["id"], entry["file_link"]))
PY
}

# The one playable .mp inside a zip, by the rule the validator uses: not a
# directory, not __MACOSX or a ._ resource fork, and exactly one of them.
extract_mp() {
    python3 - "$1" "$2" <<'PY'
import pathlib, sys, zipfile
src, dest = sys.argv[1], pathlib.Path(sys.argv[2])
with zipfile.ZipFile(src) as archive:
    members = []
    for member in archive.infolist():
        name = pathlib.PurePosixPath(member.filename)
        if member.is_dir() or name.suffix.casefold() != ".mp":
            continue
        if "__MACOSX" in name.parts or name.name.startswith("._"):
            continue
        members.append(member)
    if len(members) != 1:
        sys.exit("%s: expected exactly one playable .mp member, found %d"
                 % (src, len(members)))
    dest.write_bytes(archive.read(members[0]))
    print(members[0].filename)
PY
}

render() {      # render SOURCE.mp OUT.png TILE
    python3 "$COLWIN" map-preview "$1" "$GAME" --out="$2" --tile="$3" >/dev/null
}

drawn=0
missing=0
differs=0

# `while read` from a file rather than from a pipeline: a pipeline would run the
# loop in a subshell and the counts would not survive it.
catalog >"$WORK/catalog"
while IFS='	' read -r id link; do
    [ -n "$ONLY" ] && [ "$ONLY" != "$id" ] && continue
    src=$ROOT/$link
    if [ ! -f "$src" ]; then
        echo "  $id: $link is missing" >&2
        missing=$((missing + 1))
        continue
    fi
    case $link in
        *.zip)
            mp=$WORK/$id.mp
            inside=$(extract_mp "$src" "$mp") || exit 1
            note=" (from $(basename "$link"): $inside)"
            ;;
        *)
            mp=$src
            note=
            ;;
    esac

    full=$ROOT/maps/$id/${id}_full.png
    preview=$ROOT/maps/$id/${id}_preview.png
    if [ "$CHECK" -eq 1 ]; then
        render "$mp" "$WORK/$id-full.png" "$FULL_TILE"
        render "$mp" "$WORK/$id-preview.png" "$PREVIEW_TILE"
        for pair in "$full:$WORK/$id-full.png" "$preview:$WORK/$id-preview.png"; do
            have=${pair%%:*}
            want=${pair#*:}
            if [ ! -f "$have" ]; then
                echo "  $id: $(basename "$have") is missing"
                differs=$((differs + 1))
            elif ! cmp -s "$have" "$want"; then
                echo "  $id: $(basename "$have") differs from a fresh render"
                differs=$((differs + 1))
            fi
        done
        echo "  $id: checked$note"
    else
        render "$mp" "$full" "$FULL_TILE"
        render "$mp" "$preview" "$PREVIEW_TILE"
        echo "  $id: ${id}_full.png and ${id}_preview.png$note"
    fi
    drawn=$((drawn + 1))
done <"$WORK/catalog"

if [ -n "$ONLY" ] && [ "$drawn" -eq 0 ] && [ "$missing" -eq 0 ]; then
    die "no map called $ONLY in maps.json"
fi

if [ "$CHECK" -eq 1 ]; then
    echo "checked $drawn map(s), $differs image(s) differ, $missing source(s) missing"
else
    echo "rendered $drawn map(s), $missing source(s) missing"
fi
[ "$differs" -eq 0 ] && [ "$missing" -eq 0 ]
