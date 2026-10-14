# Changelog

## Unreleased

### Added
- Concept pages (publet spec Section 5.9.1) at `/def/<PDC code>/`. Each shows the concept's form, boundary, broader and narrower classes, members, the calculations that solve it, its versions, the expert group covering it, and a link to review it. A code claimed by more than one concept lineage is shown as contested.
- `/pdc/`, the classification from the top tables down.
- Object pages name the concepts the object is classified under, and link each suggestion naming it to the review service (`site.review`, by default https://review.sustenaut.eu).
- A name's bundle is read from the index's `name_paths`, so a name with a slash (the PDC code 631/635) is served at `/def/631_635/`.
- `pubtheme build` turns publet reading bundles (bundle version 1, from `pub bundle`) into a static website with a theme; `pubtheme themes` lists the themes.
- The `sustenaut` theme: a page per object and per name, each with what it rests on and what uses it, values with null shown as "not yet known", the object's bytes and bundle beside it; Sustenaut's tokens and components ported from its React library.
