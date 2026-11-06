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
`https://review.sustenaut.eu`) and `search` (true: a search form on every page, for a site that answers
`/search` itself, below). Each is optional.

## Objects kept elsewhere

A host limits how many files a site can have, and a classification is thousands of objects. `--external` leaves the
objects of another bundle, and the names only they define, out of the site:

```sh
pub bundle --dir=all-objects --out=bundles --base=https://pub.example.org
pub bundle --dir=classification-objects --out=kept --base=https://pub.example.org
pubtheme build --bundles=bundles --out=site --site=site.json --external=kept --worker-out=worker
```

Bundle `kept` from those objects alone: it is what you can publish, while `bundles` knows what the rest of the site
says about them. Your site's server, a Cloudflare Worker say, then renders their pages on request, reading the
same as the static ones, with what the build wrote:

| Where | What |
|---|---|
| `worker/render.js` | `renderer(site)` with `.name(entry, byCid)`, `.object(bundle, byCid)` and `.search(query, entries)`, each giving a page's HTML; `part(code)`; `objectPart(bundle)`; `objectNeeds(bundle)`; `search(entries, query)`. The theme's templates, compiled so nothing is evaluated at run time. |
| `site/_external/manifest.json` | `{site, segments}`: the settings, and which part of the index each name's path segment is in. |
| `site/_external/index/<part>.json` | `{names, byCid}`: the names of that part, and everything their pages show, including what the rest of the site says about them. A name a family defines has `classes: [{code, family}]`, the family's CID for its code. A concept's `annotations` are the CIDs of what classifies it. Small enough to parse on a request. |
| `site/_external/search.json` | Every name and object, `{code, label, href}`. |
| `site/_external/bundles/<letter>.json` | Each kept object's bundle's SHA-256, by CID, in parts by the CID hash's first letter. |

An object's page takes its bundle from `kept`, wherever you keep it, a `byCid` holding the `byCid` of
`objectPart(bundle)` for a concept or a family (null for anything else), and the bundles of the objects `objectNeeds`
names.
An object's bytes are those you already hold: a CID's hash is their SHA-256.

## The themes

| Theme | What it is |
|---|---|
| `sustenaut` | Sustenaut's look: soil and seedling colours, Nunito, and the components of Sustenaut's planning app ported from its React library. Its tokens and fonts are [`@sustenaut/theme`](https://github.com/Sustenaut/theme)'s, shared with every Sustenaut site. The default, and what sustenaut.eu uses. |

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
- **A family's page** at `/o/<CID>/`: the classes directly under one class,
  defined and signed together (publet spec Section 5.9.1). It names the
  classes above it, from the top down by their `parent` codes, and has a
  place for each class at its code (`/o/<CID>/#<code>`), with its boundary,
  what is placed under it, what else claims its code, and a link to the
  family under it.
- **A class's code**, `/def/<code>/`, lands on its place in its family's
  page; a code more than one definition claims shows each of them.
- **A concept's page** at its PDC code, `/def/<code>/`. It shows:
  - its form (subject, quantity or relation) and its boundary;
  - its broader and narrower classes, and the claims classified under it;
  - for a relation, its slots and the calculations that solve it (its
    interface);
  - its versions, the expert group (an anchor) covering it, and a link to
    review it.

  A code that more than one concept lineage claims is shown as contested,
  with every concept that claims it.
- **The classification** at `/pdc/`: every class from the top tables down,
  family by family, with the concepts placed under each.
- **Whether its author signed it**, on every object's page and each class:
  `pub bundle` gives each object's signature status, and only what its
  author signed counts.
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
are fake test data, made by `tools/concept-testdata.py --pub=PATH` with pub
from publet's v0.4.0 release (the tool names the release it needs). They hold:
- 20 classes of the UDC Summary, from schryer/publet-decimal-classification,
  in 11 families;
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
