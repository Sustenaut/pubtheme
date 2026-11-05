// The sustenaut theme's filters, for the static build (eleventy.config.js) and for pages rendered on
// request (lib/external.js), so a page reads the same either way. No imports: this runs in a Worker too.

/** Every byte outside RFC 3986's unreserved characters percent-encoded,
 *  as `pub bundle` encodes a name in its address. */
function encodeName(name) {
  return Array.from(new TextEncoder().encode(String(name)))
    .map((b) =>
      /[A-Za-z0-9\-._~]/.test(String.fromCharCode(b)) ? String.fromCharCode(b) : `%${b.toString(16).toUpperCase().padStart(2, "0")}`,
    )
    .join("");
}

// A name's page is at its path segment: the name with each "/" as "_", as `pub bundle` writes it.
export const segment = (name) => String(name).replaceAll("/", "_");

export const filters = {
  // The first characters of an identifier's hash: enough to tell objects
  // apart by eye; the full identifier is on the object's page.
  short: (cid) => String(cid).split(":").pop().slice(0, 10),
  encname: encodeName,
  isnull: (v) => v === null || v === undefined,
  isobject: (v) => v !== null && typeof v === "object" && !Array.isArray(v),
  hasnull: (rows) => (rows || []).some((r) => r.some((c) => c === null)),
  isurl: (v) => /^https?:\/\//.test(String(v)),
  byhow: (edges, how) => (edges || []).filter((e) => e.how === how),
  nothow: (edges, how) => (edges || []).filter((e) => e.how !== how),
  bykey: (list, key, value) => (list || []).filter((x) => x[key] === value),
  keys: (o) => Object.keys(o || {}),

  // Concepts (publet spec Section 5.9.1).
  defhref: (name) => `/def/${encodeName(segment(name))}/`,
  // The definitions going by one name, grouped by lineage: one entry per
  // lineage, its head and its versions. More than one lineage at a PDC code
  // is a contested code.
  lineages: (cids, byCid) => {
    const groups = new Map();
    for (const cid of cids || []) {
      const b = byCid[cid];
      if (!b || !b.concept) continue;
      const genesis = b.lineage.genesis;
      if (!groups.has(genesis)) {
        const heads = b.lineage.heads.filter((h) => byCid[h]);
        groups.set(genesis, { genesis, head: heads[heads.length - 1] || cid, versions: b.lineage.members });
      }
    }
    return [...groups.values()];
  },
  // The concepts at the top of the classification: subject concepts placed
  // under nothing, each the head of its lineage, in code order.
  pdcroots: (objects) =>
    (objects || [])
      .filter((b) => b.concept && b.concept.form === "subject" && !b.concept.broader.length)
      .filter((b) => !(b.classified_under || []).some((u) => u.code))
      .filter((b) => b.lineage.heads.includes(b.cid))
      .sort((x, y) => x.concept.pdc.localeCompare(y.concept.pdc, "en", { numeric: true })),
  // Narrower concepts by code, each the head of its lineage.
  narrower: (b, byCid) =>
    ((b && b.concept && b.concept.narrower) || [])
      .map((n) => byCid[n.cid])
      .filter((n) => n && n.lineage.heads.includes(n.cid))
      .sort((x, y) => x.concept.pdc.localeCompare(y.concept.pdc, "en", { numeric: true })),
  // Families (publet spec Section 5.9.1): the classes directly under one class, defined together.
  // The head of each lineage among `cids`, in the order given.
  heads: (cids, byCid) => (cids || []).map((c) => byCid[c]).filter((b) => b && b.lineage.heads.includes(b.cid)),
  // The families at the top of the classification: those with no parent, each the head of its lineage.
  familyroots: (objects) => (objects || []).filter((b) => b.family && !b.family.parent && b.lineage.heads.includes(b.cid)),
  // The classes above a family, from the top down, found by walking parent codes: each {code, name, family}.
  // It stops where this site holds no family defining the next code up.
  crumbs: (b, byCid) => {
    const out = [];
    const seen = new Set();
    let at = b;
    while (at && at.family && at.family.parent && !seen.has(at.cid)) {
      seen.add(at.cid);
      const code = at.family.parent;
      const above = at.family.broader.map((c) => byCid[c]).find((x) => x && x.family);
      const cls = above && above.family.classes.find((c) => c.pdc === code);
      out.unshift({ code, name: cls ? cls.name : "", family: above ? above.cid : "" });
      at = above;
    }
    return out;
  },
  // Where a code's class is on its family's page.
  classhref: (code, family) => `/o/${family}/#${encodeName(code)}`,
  // Where a name's page lands: the class in its family, when one family alone defines it.
  landing: (n) => (n && n.classes && n.classes.length === 1 && n.definitions.length === 1
    ? `/o/${n.classes[0].family}/#${encodeName(n.classes[0].code)}` : ""),
  // The families a concept is placed under, by the class each names: {code, family}.
  placed: (b) => ((b && b.classified_under) || []).filter((u) => u.code).map((u) => ({ code: u.code, family: u.concept })),
  // The expert groups covering a concept: its own, and those of the families it is placed under.
  anchorsof: (b, byCid) => {
    const out = [...((b.concept && b.concept.anchors) || [])];
    for (const u of (b.classified_under || []).filter((x) => x.code)) {
      const f = byCid[u.concept];
      for (const a of (f && f.family && f.family.anchors) || []) if (!out.some((x) => x.cid === a.cid)) out.push(a);
    }
    return out;
  },

  // A quantity cell's keys in its measure's order.
  ordered: (cell, order) => {
    const keys = (order || []).filter((k) => k in cell);
    return keys.concat(Object.keys(cell).filter((k) => !keys.includes(k))).map((k) => [k, cell[k]]);
  },
};
