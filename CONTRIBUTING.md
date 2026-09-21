# Contributing a map

Thank you for helping preserve the Colonization mapping community's work.

## Recommended: submit a map with an issue

The easiest way to contribute is to open a
[map submission issue](https://github.com/colonization-re/maps/issues/new?template=map_submission.yml).
You do not need to fork the repository, create a branch, or edit
`maps.json`.

Use the issue form when you have a custom map, a recovered download, or useful
metadata for an existing map. Please include as much as you can:

- The map name and author.
- The original source page or a Wayback Machine snapshot, if known.
- The playable `.mp` file, or a `.zip` if required scenario support files are
  needed.
- Preview images, screenshots, or notes that help identify the map.
- A short note confirming that the files may be redistributed here.

A maintainer will review the issue, ask follow-up questions if needed, and add
accepted maps to the repository.

## Advanced: submit a pull request

Pull requests are welcome if you are comfortable preparing the repository
changes yourself.

1. Fork this repository and create a branch.
2. Choose a stable map ID made from lowercase letters, numbers, and hyphens.
   For example, use `new-world` for a map displayed as “New World”.
3. Create `maps/<id>/` and add exactly these files:

   ```text
   maps/<id>/<id>.mp
   maps/<id>/<id>_preview.png
   maps/<id>/<id>_full.png
   ```

   If the map requires supporting scenario files, `<id>.zip` may replace
   `<id>.mp`.

4. Add one entry to `maps.json`. Keep entries sorted by `id`. All catalog links
   must be relative paths matching the names above.
5. Run `python3 tools/validate_archive.py` from the repository root.
6. Open a pull request and complete the checklist in the template. If there is
   already a submission issue for the map, link it in the pull-request
   description.

## File guidelines

- Extract the playable `.mp` file from the original download and rename it to
  match the map ID. Do not modify the map data itself.
- If a download contains multiple `.mp` files, create a separate map directory
  and catalog entry for each one.
- Use a ZIP only when supporting files are needed for the map to work. Name it
  `<id>.zip`; it must contain exactly one playable `.mp` file and must not be
  encrypted or contain executables, symbolic links, or unsafe paths.
- Use PNG for both images. The preview should be a reasonably small version for
  gallery use; the full image should retain the best available resolution.
  `tools/render_previews.sh` draws both from the map file — see
  [README](README.md#render-the-preview-images) — so a submission does not need
  to include them, and a reviewer can reproduce them.
- Do not add unrelated archives, executables, or files.
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
dates, or provenance in the issue or pull-request description.

## Updating an existing entry

Avoid modifying the original map data. If correcting metadata or supplying a
better image, explain the evidence and origin in an issue or pull request.
Renaming an ID changes every public asset path and should be reserved for
genuine mistakes.
