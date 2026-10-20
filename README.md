# pubtheme

Themes that turn publet reading bundles into static websites, built with
[Eleventy](https://www.11ty.dev/).

A host shows publets through a theme of its choosing. `pub bundle` (from
[publet](https://github.com/schryer/publet)) writes the reading data: one
JSON bundle per object and per name a definition goes by, each holding
everything its page shows. A theme decides only how that looks, so swapping
themes changes the look of a site and nothing about what it says.

```sh
pub bundle --dir=objects --out=bundles --base=https://pub.example.org
pubtheme build --bundles=bundles --out=site --theme=sustenaut --site=site.json
```

`site.json` holds the host's settings: `title`, `description`, `logo` (a
path to an SVG, relative to the file), `footer` and `review` (the review
service concepts and suggestions link to; the sustenaut theme defaults to
`https://review.sustenaut.eu`). Each is optional.

## The themes

| Theme | What it is |
|---|---|
| `sustenaut` | Sustenaut's look: soil and seedling colours, Nunito, and the components of Sustenaut's planning app ported from its React library. The default, and what sustenaut.eu uses. |

`pubtheme themes` lists them. A theme is an Eleventy project in
`themes/<name>/`: `theme.json`, `eleventy.config.js`, a Tailwind
`theme.css` and its templates in `src/`. Its templates get two global
data objects: `pub` (`index`, `objects`, `byCid`, `names`, as the bundles
hold them) and `site` (the host's settings). Other themes can be added here,
or built in a package of their own against the same bundles.

## What every page carries

- **A page per object** at `/o/<CID>/`: what it says, the scope it was
  asserted under, its values (a null cell reads "not yet known"), what it
  defines or computes, how it is known, what it rests on, what uses it, its
  critiques and versions.
- **A page per name** at `/def/<name>/`, the address spec Section 5.9.1
  describes; a name two definitions share lists both. A `/` in a name is
  `_` in its address (`/def/631_635/`), as `pub bundle` writes it.
- **A concept's page** at its PDC code, `/def/<code>/`. It shows:
  - its form (subject, quantity or relation) and its boundary;
  - its broader and narrower classes, and the claims classified under it;
  - for a relation, its slots and the calculations that solve it (its
    interface);
  - its versions, the expert group (an anchor) covering it, and a link to
    review it.

  A code that more than one concept lineage claims is shown as contested,
  with every concept that claims it.
- **The classification** at `/pdc/`: every subject concept from the top
  tables down.
- **Concepts on every page**: an object's page names the concepts it is
  classified under and links each machine suggestion naming it to the
  review service.
- **Its object's bytes** at `/pub/v1/object/<CID>` and its bundle at
  `/o/<CID>.json`, so a reader can check the page against what it shows.

Pages need no script to read.

## Testing

```sh
make venv node     # the hash-locked test requirements; the pinned npm packages
make functional    # the Gherkin suite, driving bin/pubtheme
make example       # build the sustenaut theme from the test bundles into _site/
```

The test bundles in `tests/testdata/publication-0` are `pub bundle`'s output
for publication 0 (schryer/business-plan). Those in `tests/testdata/concepts`
are fake test data, made by `tools/concept-testdata.py --pub=PATH` with a pub
that bundles concepts (schryer/publet#49). They hold:
- 20 classes of the UDC Summary, from schryer/publet-decimal-classification;
- a quantity concept with two members and two versions, and a competing
  concept at the same code;
- a relation concept and a calculation that solves it;
- an expert group (an anchor), and a machine suggestion. The functional suite follows
[pubkit](https://github.com/schryer/pubkit)'s setup: Gherkin features run
by pytest-bdd, driving the program as a host would.

## Releasing

Releases are made with [pubrel](https://github.com/schryer/pubrel). A pull
request that changes `bin/`, `lib/`, `themes/` or the npm manifests records
what it changes, and CI's `pubrel check` fails one that does not:

```sh
pubrel add added "a new page"     # or changed, removed, fixed, security, internal
```

The rows wait in `corpus/publets/pkg.pubtheme/unreleased.json`. A release is
cut on a clean main with `pubrel prepare`, which sets the version in
`package.json`, publishes the signed package publet, regenerates
`CHANGELOG.md` and opens the release pull request; merging it makes CI tag
it.

## Licence

Apache-2.0.
