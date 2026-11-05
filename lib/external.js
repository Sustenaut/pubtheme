// Objects kept elsewhere: a site can leave most of its objects out of its files, because a host
// limits how many it can have, and render them on request.
//
// What stays, in `_external/`: `index/<key>.json`, the classes, with everything a concept's page shows and what
// links to it, in parts so a request parses only one; `manifest.json`, which part each name is in; `search.json`,
// what can be searched for; and `bundles/<letter>.json`, the hash of each object's bundle, which is its address
// wherever it is kept. And worker-out/render.js: the theme's templates compiled to work in a Worker, where nothing
// may be evaluated at run time.
//
// `external` is a `pub bundle` of those objects alone, not of the whole site: it is what a host may publish.
// The full bundles know what else cites a class, so that goes in the index and nowhere public.

import crypto from "node:crypto";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";

import { build as esbuild } from "esbuild";

import { part } from "./render.js";

const require = createRequire(import.meta.url);

// The templates a request can reach. Pages (front matter) lose it; includes have their short names.
const TEMPLATES = ["src/_includes/base.njk", "src/_includes/components.njk", "src/_includes/concept.njk",
  "src/_includes/family.njk", "src/_includes/search.njk", "src/name.njk", "src/object.njk"];

export function readExternal(dir) {
  const index = JSON.parse(fs.readFileSync(path.join(dir, "index.json"), "utf8"));
  const held = index.objects.filter((o) => o.held);
  return { dir, held, cids: new Set(held.map((o) => o.cid)) };
}

/** The names only external objects define, as long as they are concepts or families: their pages are rendered on
 *  request. */
export function externalNames(pub, cids) {
  const out = new Set();
  const classifying = (c) => pub.byCid[c] && (pub.byCid[c].concept || pub.byCid[c].family);
  for (const n of pub.names) {
    if (n.definitions.length && n.definitions.every((c) => cids.has(c) && classifying(c))) {
      out.add(n.name);
    }
  }
  return out;
}

export function removeExternalFiles(pub, cids, out) {
  const names = externalNames(pub, cids);
  const gone = (file) => fs.rmSync(path.join(out, file), { force: true });
  for (const b of pub.objects) {
    if (cids.has(b.cid)) {
      gone(path.join("o", `${b.cid}.json`));
      gone(b.bytes.path);
    }
  }
  for (const n of pub.names) {
    if (names.has(n.name)) gone(pub.index.name_paths?.[n.name] || path.join("def", `${n.name}.json`));
  }
}

/** A concept's or family's bundle, cut to what its page shows: the rest is in its own bundle. */
function project(b) {
  const { content, defines, computes } = b.object.body;
  const body = { content, defines, ...(computes ? { computes } : {}) };
  const said = JSON.stringify([b.concept, b.family, b.classified_under, body]);
  const related = Object.fromEntries(Object.entries(b.related).filter(([cid]) => said.includes(cid))
    .map(([cid, r]) => [cid, { label: r.label, name: r.name, path: r.path, held: r.held }]));
  return {
    cid: b.cid,
    summary: { signature: b.summary.signature },
    concept: b.concept,
    family: b.family,
    classified_under: (b.classified_under || []).filter((u) => u.code),
    lineage: b.lineage,
    object: { created: b.object.created, body },
    related,
    annotations: (b.used_by || []).filter((e) => e.how === "classifies annotation").map((e) => e.cid),
  };
}

function settingsForRequests(settings) {
  const out = { ...settings };
  if (out.logo) out.logo = "/logo.svg"; // a path on the build machine: pages only ask whether there is one
  return out;
}

export async function writeExternal({ pub, elsewhere, settings, themeDir, out, workerOut }) {
  const names = externalNames(pub, elsewhere.cids);
  const parts = {};
  const segments = {};
  const search = [];
  for (const n of pub.names) {
    const head = pub.byCid[n.definitions[0]];
    const seg = n.segment || String(n.name).replaceAll("/", "_");
    const cls = head?.family?.classes.find((c) => c.pdc === n.name);
    search.push(head?.concept ? { code: n.name, label: head.object.body.defines.name, href: `/def/${encodeURIComponent(seg)}/` }
      : cls ? { code: n.name, label: cls.name, href: `/def/${encodeURIComponent(seg)}/` }
        : { code: "", label: n.name, href: `/def/${encodeURIComponent(seg)}/` });
    if (!names.has(n.name)) continue;
    const key = part(n.name);
    const shard = (parts[key] ??= { names: {}, byCid: {} });
    segments[seg] = key;
    shard.names[seg] = { name: n.name, segment: n.segment, address: n.address, definitions: n.definitions,
      classes: n.classes || [] };
    // What this name's page reads: its definitions, their versions, narrower concepts and calculations, the
    // families they are placed under; for a family, what its own page reads too, as that page uses this part.
    for (const cid of n.definitions) {
      const b = pub.byCid[cid];
      const wanted = b.family ? familyNeeds(b, pub.byCid) : [cid, ...b.lineage.members, ...b.lineage.heads,
        ...b.concept.broader, ...b.concept.narrower.map((x) => x.cid), ...b.concept.solved_by,
        ...(b.classified_under || []).filter((u) => u.code).flatMap((u) => pub.byCid[u.concept] ? familyNeeds(pub.byCid[u.concept], pub.byCid) : [])];
      for (const w of wanted) if (pub.byCid[w] && !shard.byCid[w]) shard.byCid[w] = project(pub.byCid[w]);
    }
  }
  for (const b of pub.objects) {
    if (!elsewhere.cids.has(b.cid) && b.summary.label) search.push({ code: "", label: b.summary.label, href: `/o/${b.cid}/` });
  }

  const dir = path.join(out, "_external");
  fs.mkdirSync(path.join(dir, "index"), { recursive: true });
  fs.writeFileSync(path.join(dir, "manifest.json"), JSON.stringify({ site: settingsForRequests(settings), segments }));
  for (const [key, shard] of Object.entries(parts)) fs.writeFileSync(path.join(dir, "index", `${key}.json`), JSON.stringify(shard));
  fs.writeFileSync(path.join(dir, "search.json"), JSON.stringify(search));
  const hashes = {};
  for (const o of elsewhere.held) {
    (hashes[bundlePart(o.cid)] ??= {})[o.cid] = crypto.createHash("sha256").update(fs.readFileSync(path.join(elsewhere.dir, o.path))).digest("hex");
  }
  fs.mkdirSync(path.join(dir, "bundles"), { recursive: true });
  for (const [key, hashed] of Object.entries(hashes)) fs.writeFileSync(path.join(dir, "bundles", `${key}.json`), JSON.stringify(hashed));
  await writeRenderer(themeDir, workerOut);
}

/** What a family's page reads: the family, its versions, the families above it to the top, those under each of its
 *  classes, and those its expert groups are over. */
function familyNeeds(b, byCid) {
  const out = [b.cid, ...b.lineage.members, ...b.lineage.heads, ...b.family.classes.flatMap((c) => c.narrower),
    ...b.family.anchors.map((a) => a.over)];
  const seen = new Set();
  for (let at = b; at && at.family && !seen.has(at.cid); at = at.family.broader.map((c) => byCid[c]).find((x) => x && x.family)) {
    seen.add(at.cid);
    out.push(...at.family.broader);
  }
  return out;
}

/** Which part of `bundles/` an object's hash is in: the start of its CID's hash. */
function bundlePart(cid) {
  return cid.split(":").pop().slice(0, 1);
}

async function writeRenderer(themeDir, workerOut) {
  const nunjucks = require("nunjucks");
  fs.mkdirSync(workerOut, { recursive: true });
  const compiled = TEMPLATES.map((file) => {
    const source = fs.readFileSync(path.join(themeDir, file), "utf8").replace(/^---\n[\s\S]*?\n---\n?/, "");
    const name = path.basename(file);
    return `${JSON.stringify(name)}: ${nunjucks.precompileString(source, { name, wrapper: (t) => `(function() {\n${t[0].template}\n})()`, env: new nunjucks.Environment() })}`;
  });
  const work = fs.mkdtempSync(path.join(os.tmpdir(), "pubtheme-renderer-"));
  const entry = path.join(work, "entry.js");
  fs.writeFileSync(entry, `
import slim from ${JSON.stringify(require.resolve("nunjucks/browser/nunjucks-slim.js"))};
import { filters } from ${JSON.stringify(path.join(themeDir, "filters.js"))};
import { renderer as make } from ${JSON.stringify(new URL("./render.js", import.meta.url).pathname)};
const templates = {${compiled.join(",\n")}};
export const renderer = (site) => make(slim, templates, filters, site);
export { objectNeeds, objectPart, part, search } from ${JSON.stringify(new URL("./render.js", import.meta.url).pathname)};
`);
  await esbuild({ entryPoints: [entry], bundle: true, format: "esm", platform: "browser", legalComments: "none",
    outfile: path.join(workerOut, "render.js"), logLevel: "silent" });
  fs.rmSync(work, { recursive: true, force: true });
}
