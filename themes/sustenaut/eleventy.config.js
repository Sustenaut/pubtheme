// The sustenaut theme: an Eleventy project whose pages read publet reading
// bundles (global data `pub`) and the host's settings (`site`).

import path from "node:path";

import { filters } from "./filters.js";

export default function (eleventyConfig, { require }) {
  for (const [pkg, file] of [
    ["@fontsource-variable/nunito", "nunito-latin-wght-normal.woff2"],
    ["@fontsource-variable/nunito-sans", "nunito-sans-latin-wght-normal.woff2"],
  ]) {
    const dir = path.dirname(require.resolve(`${pkg}/package.json`));
    eleventyConfig.addPassthroughCopy({ [path.join(dir, "files", file)]: `fonts/${file}` });
  }

  for (const [name, filter] of Object.entries(filters)) eleventyConfig.addFilter(name, filter);

  return {
    dir: { includes: "_includes", data: "_data" },
    templateFormats: ["njk"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
  };
}
