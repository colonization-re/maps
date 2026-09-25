# Suggested web-ui additions

The archive uses `@colonization-re/web-ui` v1.1.0 directly. Most of the page is
composed from existing classes. The following archive-specific rules look
general enough to move into a future web-ui release.

## Media card

A card variant for a preview image above structured content:

```html
<article class="col-card col-media-card">
  <a class="col-media-card-media"><img class="col-art" ...></a>
  <div class="col-media-card-body">...</div>
  <div class="col-media-card-actions">...</div>
</article>
```

Desired behavior:

- remove the outer card padding and clip content to the card radius;
- provide a configurable media aspect ratio with a sensible default;
- center an image with `object-fit: contain` on `--surface-2`;
- separate media and body with the standard border;
- let the body grow so action rows align at the bottom across a grid;
- retain compatibility with `.col-card--hover` and `.col-art`.

This would replace `.archive-map-card`, `.archive-map-preview`,
`.archive-map-body`, and `.archive-map-actions`.

## Skip link

A `.col-skip-link` accessibility utility that is positioned outside the
viewport until focused, then appears above `.col-bar` using the design-system
colors, radius, and z-index. This would replace `.archive-skip-link` and be
useful on every page with persistent navigation.

## Toolbar

A `.col-toolbar` composition for filters and compact actions:

- flex, wrap, and vertically align its children;
- allow one field to grow while actions retain their intrinsic width;
- remove the normal bottom margin from direct `.col-field` children;
- provide a clean single-column layout at narrow widths.

This would replace the small `.archive-filter-*` layout rules and generalize
the existing margin normalization that `.col-row` already provides.

## Release asset delivery

This is not a component gap, but it affects browser consumers. GitHub currently
serves the `col.min.css` release asset as `application/octet-stream` with
`X-Content-Type-Options: nosniff`. A direct `<link rel="stylesheet">` can
therefore be rejected by browsers even though the README recommends it.

The map archive works around this by downloading and checksum-verifying the
pinned asset at build time, then serving it from GitHub Pages as a `.css` file.
A future web-ui release process could publish the stylesheet through a static
host or package CDN that returns `text/css`, and document that URL for direct
browser use.

## Link button hover color

`a:hover { color: var(--brand-hover) }` (specificity 0,1,1) beats `.col-btn`
(0,1,0), and the default `.col-btn:hover` only changes background and border.
So an `<a class="col-btn">` on hover shows `--brand-hover` text on a
`--brand-hover` background, making the label invisible. Variants that set their
own hover color are unaffected. The archive works around it with
`a.col-btn:where(:hover){color:var(--_fg)}`; a future web-ui release could set
`color: var(--_fg)` in `.col-btn:hover`.
