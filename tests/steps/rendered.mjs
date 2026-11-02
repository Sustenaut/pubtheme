// Renders pages from what `--external --worker-out` wrote, as a site's Worker would, and prints them as JSON.
//   node rendered.mjs SITE WORKER_OUT EXTERNAL_BUNDLES [--search=QUERY]
import fs from "node:fs";
import path from "node:path";

const [site, workerOut, external, ask] = process.argv.slice(2);
const { objectNeeds, renderer, part, search } = await import(path.resolve(workerOut, "render.js"));
const read = (...p) => JSON.parse(fs.readFileSync(path.join(...p), "utf8"));
const manifest = read(site, "_external", "manifest.json");
const render = renderer(manifest.site);
const parts = {};
const shard = (key) => (parts[key] ??= fs.existsSync(path.join(site, "_external", "index", `${key}.json`))
  ? read(site, "_external", "index", `${key}.json`) : { byCid: {}, names: {} });
if (ask?.startsWith("--search=")) {
  const q = ask.slice("--search=".length);
  const entries = read(site, "_external", "search.json");
  console.log(JSON.stringify({ found: search(entries, q), page: render.search(q, entries) }));
} else {
  const names = Object.fromEntries(Object.entries(manifest.segments).map(([seg, key]) => [seg, render.name(shard(key).names[seg], shard(key).byCid)]));
  const objects = {};
  for (const o of read(external, "index.json").objects.filter((x) => x.held)) {
    const b = read(external, o.path);
    const byCid = { ...(b.concept ? shard(part(b.concept.pdc)).byCid : {}) };
    for (const cid of objectNeeds(b)) {
      if (fs.existsSync(path.join(external, "o", `${cid}.json`))) byCid[cid] = read(external, "o", `${cid}.json`);
    }
    objects[o.cid] = render.object(b, byCid);
  }
  console.log(JSON.stringify({ names, objects }));
}
