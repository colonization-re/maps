# Contributing a map

Thank you for helping preserve the Colonization mapping community's work.

## Add a map

1. Fork this repository and create a branch.
2. Choose a stable map ID made from lowercase letters, numbers, and hyphens.
   For example, use `new-world` for a map displayed as “New World”.
3. Create `maps/<id>/` and add exactly these files:

   ```text
   maps/<id>/<id>.zip
   maps/<id>/<id>_preview.png
   maps/<id>/<id>_full.png
   ```

4. Add one entry to `maps.json`. Keep entries sorted by `id`. All catalog links
   must be relative paths matching the names above.
5. Run `python3 tools/validate_archive.py` from the repository root.
6. Open a pull request and complete the checklist in the template.

## File guidelines

- Preserve the original ZIP downloaded from its source. Do not repackage it
  merely to rename files inside the archive.
- Make sure the ZIP opens successfully and contains the map data.
- Use PNG for both images. The preview should be a reasonably small version for
  gallery use; the full image should retain the best available resolution.
- Do not add passwords, executables, unrelated files, or archives containing
  absolute paths, `..` path traversal, or symbolic links.
- GitHub rejects individual files larger than 100 MiB. If an artifact is that
  large, discuss it in an issue before submitting it.

## Metadata guidelines

- `id`: stable filesystem-safe identifier; it must match the directory name.
- `name`: original human-readable title, preserving spelling where known.
- `author`: original creator's name or `"Unknown"` when it cannot be found.
- `release_date`: `YYYY-MM-DD`, `YYYY-MM`, or `YYYY`; use `null` if unknown.
- `size`: playable width and height in tiles, both positive integers.
- `tags`: unique, lowercase labels using letters, numbers, and hyphens.
- `source_link`: original source or Wayback Machine URL. Omit it only if none is
  known.
- `file_link`, `preview_link`, and `full_preview_link`: repository-relative
  paths generated from the ID.

When recovering a map through the Wayback Machine, prefer a snapshot close to
the original publication date. Put any useful context about uncertain authors,
dates, or provenance in the pull-request description.

## Updating an existing entry

Avoid replacing an original ZIP with a repackaged copy. If correcting metadata
or supplying a better image, explain the evidence and origin in the pull
request. Renaming an ID changes every public asset path and should be reserved
for genuine mistakes.
