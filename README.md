# Sid Meier's Colonization Map Archive

A community-maintained archive of custom maps for the original **Sid Meier's
Colonization**. The project is intended to preserve maps from websites that
have disappeared and to accept community contributions through pull requests.

The archive does not currently contain any maps. See [CONTRIBUTING.md](CONTRIBUTING.md)
to add the first one.

## Archive layout

Each map has a stable, lowercase ID and exactly three files:

```text
maps/
└── new-world/
    ├── new-world.zip
    ├── new-world_preview.png
    └── new-world_full.png
```

- `*.zip` is the original map download, kept intact whenever possible.
- `*_preview.png` is a smaller image suitable for indexes and galleries.
- `*_full.png` is the full-size map image.
- [`maps.json`](maps.json) is the machine-readable catalog.
- [`maps.schema.json`](maps.schema.json) documents the catalog format.

Links in the catalog are repository-relative, so they work in local clones and
can be converted to raw GitHub URLs by consumers.

## Catalog format

```json
{
  "catalog_version": 1,
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
      "source_link": "https://web.archive.org/web/20010101000000/https://example.com/new-world.zip",
      "file_link": "maps/new-world/new-world.zip",
      "preview_link": "maps/new-world/new-world_preview.png",
      "full_preview_link": "maps/new-world/new-world_full.png"
    }
  ]
}
```

`size` is the playable map size in tiles, not the ZIP file size. For preserved
maps whose exact date is unavailable, `release_date` may be a year (`"1996"`)
or a year and month (`"1996-08"`). Use `null` only when no reliable date can be
found. `source_link` is optional, but strongly encouraged for archived maps.

## Validate the archive

Python 3.9 or newer is the only requirement:

```sh
python3 tools/validate_archive.py
```

The same validation runs automatically on pushes and pull requests. It checks
catalog structure, naming, broken links, PNG and ZIP signatures, unsafe ZIP
paths, duplicate IDs, and unlisted map folders.

## Preservation and rights

Please preserve provenance: link to the original page or a Wayback Machine
snapshot and avoid modifying the original ZIP. Contributors must only submit
files they are permitted to redistribute. Copyright remains with each map's
creator; inclusion in this archive does not place a map in the public domain or
apply a repository-wide license to it.
