[View the deployed map archive](https://colonization-re.github.io/maps/)

# Sid Meier's Colonization Map Archive

A community-maintained archive of custom maps for the original **Sid Meier's
Colonization**. The project is intended to preserve maps from websites that
have disappeared and to accept community contributions through pull requests.

See [CONTRIBUTING.md](CONTRIBUTING.md) to add another map.

## Archive layout

Each map has a stable, lowercase ID and exactly three files:

```text
maps/
└── new-world/
    ├── new-world.mp
    ├── new-world_preview.png
    └── new-world_full.png
```

- `*.mp` is the playable Colonization map, extracted from its original download
  without modifying the map data.
- `*_preview.png` is a smaller image suitable for indexes and galleries.
- `*_full.png` is the full-size map image.
- [`maps.json`](maps.json) is the machine-readable catalog.
- [`maps.schema.json`](maps.schema.json) documents the catalog format.

Links in the catalog are repository-relative, so they work in local clones and
can be converted to raw GitHub URLs by consumers.

## Catalog format

```json
{
  "catalog_version": 2,
  "maps": [
    {
      "id": "new-world",
      "name": "New World",
      "author": "Jane Doe",
      "release_date": "1996-08-14",
      "size": {
        "width": 58,
        "height": 72
      },
      "tags": ["historical", "large"],
      "source_link": "https://web.archive.org/web/20010101000000/https://example.com/new-world",
      "file_link": "maps/new-world/new-world.mp",
      "preview_link": "maps/new-world/new-world_preview.png",
      "full_preview_link": "maps/new-world/new-world_full.png"
    }
  ]
}
```

`size` is the playable map size in tiles, not the MP file size. For preserved
maps whose exact date is unavailable, `release_date` may be a year (`"1996"`)
or a year and month (`"1996-08"`). Use `null` only when no reliable date can be
found. `source_link` is optional, but strongly encouraged for archived maps.

## Validate the archive

Python 3.9 or newer is the only requirement:

```sh
python3 tools/validate_archive.py
```

The same validation runs automatically on pushes and pull requests. It checks
catalog structure, naming, broken links, MP headers and dimensions, PNG
signatures, duplicate IDs, and unlisted map folders.

## Website

GitHub Pages is rebuilt from `maps.json` on every push to `main`. Build it
locally with:

```sh
python3 tools/build_site.py
python3 -m http.server --directory _site 8000
```

The generated site is written to `_site/` and is not committed. It contains
the catalog, map downloads, previews, and a searchable static index. The build
downloads `col.min.css` and its checksum manifest from the pinned web-ui
release, verifies the stylesheet, and includes it in the Pages artifact so it
is served with the correct CSS media type. For an offline build, pass an
existing release asset with `--web-ui-css path/to/col.min.css`.

The site uses the pinned `@colonization-re/web-ui` release named in
[`site/WEB_UI_VERSION`](site/WEB_UI_VERSION). To upgrade the design system,
change that one line and rebuild. Archive-specific CSS lives in
[`site/assets/site.css`](site/assets/site.css). Reusable components that are
still missing from the shared design system are described in
[`site/WEB_UI_GAPS.md`](site/WEB_UI_GAPS.md).

Before the first deployment, make sure the repository's **Settings → Pages →
Build and deployment → Source** is set to **GitHub Actions**.

## Preservation and rights

Please preserve provenance: link to the original page or a Wayback Machine
snapshot, and do not modify the extracted map data. Contributors must only
submit files they are permitted to redistribute. Copyright remains with each
map's creator; inclusion in this archive does not place a map in the public
domain or apply a repository-wide license to it.
