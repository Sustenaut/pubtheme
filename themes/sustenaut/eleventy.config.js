// The sustenaut theme: an Eleventy project whose pages read publet reading
// bundles (global data `pub`) and the host's settings (`site`).

import path from "node:path";

/** Every byte outside RFC 3986's unreserved characters percent-encoded,
 *  as `pub bundle` encodes a name in its address. */
function encodeName(name) {
  return Array.from(new TextEncoder().encode(String(name)))
    .map((b) =>
      /[A-Za-z0-9\-._~]/.test(String.fromCharCode(b)) ? String.fromCharCode(b) : `%${b.toString(16).toUpperCase().padStart(2, "0")}`,
    )
    .join("");
}

export default function (eleventyConfig, { require }) {
  for (const [pkg, file] of [
    ["@fontsource-variable/nunito", "nunito-latin-wght-normal.woff2"],
    ["@fontsource-variable/nunito-sans", "nunito-sans-latin-wght-normal.woff2"],
  ]) {
    const dir = path.dirname(require.resolve(`${pkg}/package.json`));
    eleventyConfig.addPassthroughCopy({ [path.join(dir, "files", file)]: `fonts/${file}` });
  }

  // The first characters of an identifier's hash: enough to tell objects
  // apart by eye; the full identifier is on the object's page.
  eleventyConfig.addFilter("short", (cid) => String(cid).split(":").pop().slice(0, 10));
  eleventyConfig.addFilter("encname", encodeName);
  eleventyConfig.addFilter("isnull", (v) => v === null || v === undefined);
  eleventyConfig.addFilter("isobject", (v) => v !== null && typeof v === "object" && !Array.isArray(v));
  eleventyConfig.addFilter("hasnull", (rows) => (rows || []).some((r) => r.some((c) => c === null)));
  eleventyConfig.addFilter("isurl", (v) => /^https?:\/\//.test(String(v)));
  eleventyConfig.addFilter("byhow", (edges, how) => (edges || []).filter((e) => e.how === how));
  eleventyConfig.addFilter("nothow", (edges, how) => (edges || []).filter((e) => e.how !== how));
  eleventyConfig.addFilter("bykey", (list, key, value) => (list || []).filter((x) => x[key] === value));
  eleventyConfig.addFilter("keys", (o) => Object.keys(o || {}));
  // A quantity cell's keys in its measure's order.
  eleventyConfig.addFilter("ordered", (cell, order) => {
    const keys = (order || []).filter((k) => k in cell);
    return keys.concat(Object.keys(cell).filter((k) => !keys.includes(k))).map((k) => [k, cell[k]]);
  });

  return {
    dir: { includes: "_includes", data: "_data" },
    templateFormats: ["njk"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
  };
}
