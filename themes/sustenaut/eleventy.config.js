// The sustenaut theme: an Eleventy project whose pages read publet reading
// bundles (global data `pub`) and the host's settings (`site`).

import fs from "node:fs";
import path from "node:path";

import { filters } from "./filters.js";

export default function (eleventyConfig, { require }) {
  // The theme package's fonts, at the fonts/ path its fonts.css names.
  const fonts = path.join(path.dirname(require.resolve("@sustenaut/theme/fonts.css")), "fonts");
  for (const file of fs.readdirSync(fonts).filter((f) => f.endsWith(".woff2"))) {
    eleventyConfig.addPassthroughCopy({ [path.join(fonts, file)]: `fonts/${file}` });
  }

  for (const [name, filter] of Object.entries(filters)) eleventyConfig.addFilter(name, filter);

  return {
    dir: { includes: "_includes", data: "_data" },
    templateFormats: ["njk"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
  };
}
