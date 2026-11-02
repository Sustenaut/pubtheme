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
      if (!b) continue;
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
      .filter((b) => b.lineage.heads.includes(b.cid))
      .sort((x, y) => x.concept.pdc.localeCompare(y.concept.pdc, "en", { numeric: true })),
  // Narrower concepts by code, each the head of its lineage.
  narrower: (b, byCid) =>
    ((b && b.concept && b.concept.narrower) || [])
      .map((n) => byCid[n.cid])
      .filter((n) => n && n.lineage.heads.includes(n.cid))
      .sort((x, y) => x.concept.pdc.localeCompare(y.concept.pdc, "en", { numeric: true })),
  // A quantity cell's keys in its measure's order.
  ordered: (cell, order) => {
    const keys = (order || []).filter((k) => k in cell);
    return keys.concat(Object.keys(cell).filter((k) => !keys.includes(k))).map((k) => [k, cell[k]]);
  },
};
