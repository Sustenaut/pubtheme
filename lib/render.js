// Pages rendered on request, by a site's Worker (external.js writes the Worker's copy, render.js in its
// worker-out): the same templates and filters as the static build, so a page reads the same either way.
// Node's own modules can't be used here.

const MAX_RESULTS = 100;

/** Which part of the index a name or PDC code is in: its first two letters or digits. Parts keep a request's parsing short. */
export function part(name) {
  const key = String(name).toLowerCase().replace(/[^a-z0-9]/g, "").slice(0, 2);
  return key || "_";
}

/** The part of the index an object's page reads, for a concept or a family; null for anything else. */
export function objectPart(b) {
  if (b.concept) return part(b.concept.pdc);
  if (b.family && b.family.classes.length) return part(b.family.classes[0].pdc);
  return null;
}

/** The other objects whose bundles an object's page reads: put them in the byCid given to render it. */
export function objectNeeds(b) {
  const items = (b.object.body.sections || []).flatMap((section) => (section.items || []).map((item) => item.ref));
  return [...(b.suggestions || []), ...items, ...(b.classified_under || []).map((u) => u.concept)];
}

/** The entries matching every word, an exact code first, then codes starting with it, then the rest in order. */
export function search(entries, query) {
  const words = String(query || "").toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  const whole = words.join(" ");
  const rank = (e) => {
    const code = (e.code || "").toLowerCase();
    if (code === whole) return 0;
    return code.startsWith(whole) ? 1 : 2;
  };
  return entries
    .filter((e) => {
      const text = `${e.code || ""} ${e.label || ""}`.toLowerCase();
      return words.every((w) => text.includes(w));
    })
    .map((e, i) => [rank(e), i, e])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
    .map((x) => x[2]);
}

export function renderer(nunjucks, templates, filters, site) {
  const env = new nunjucks.Environment(new nunjucks.PrecompiledLoader(templates));
  for (const [name, filter] of Object.entries(filters)) env.addFilter(name, filter);
  env.addFilter("url", (href) => href); // the Eleventy filter, for a site at the root
  const page = (template, title, context, byCid = {}) => {
    const shared = { site, pub: { byCid }, ...context };
    const content = env.render(template, shared);
    return env.render("base.njk", { ...shared, title, content });
  };
  const escape = (text) => nunjucks.lib.escape(String(text));
  return {
    /** A name's page, from its entry and the objects of its part of the index. */
    name(n, byCid) {
      return page("name.njk", escape(n.name), { n }, byCid);
    },
    /** An object's page, from its bundle, and for a concept the objects of its part of the index. */
    object(b, byCid = {}) {
      return page("object.njk", escape(b.summary.label), { b, checkable: `/${b.bytes.path}` }, byCid);
    },
    search(query, entries) {
      const found = search(entries, query);
      const results = found.slice(0, MAX_RESULTS);
      return page("search.njk", "Search", { query: String(query || ""), results, more: found.length > results.length });
    },
  };
}
