// Build a site from publet reading bundles with one of the themes.
//
// A theme is an Eleventy project in themes/<name>/: its templates read the
// bundles `pub bundle` wrote, which hold everything a page shows, so a
// theme decides how things look and nothing about what they are.

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

import Eleventy from "@11ty/eleventy";

const require = createRequire(import.meta.url);
const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

/** The bundle shapes this release of pubtheme reads. */
export const BUNDLE_VERSIONS = [1];

/** The themes this package holds, by name. */
export function themes() {
  const dir = path.join(ROOT, "themes");
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((e) => e.isDirectory() && fs.existsSync(path.join(dir, e.name, "theme.json")))
    .map((e) => ({ name: e.name, ...readJson(path.join(dir, e.name, "theme.json")) }));
}

/** Read the bundles in `dir` into the data every theme gets as `pub`. */
export function loadBundles(dir) {
  const index = readJson(path.join(dir, "index.json"));
  if (!BUNDLE_VERSIONS.includes(index.bundle)) {
    throw new Error(
      `${dir}: bundle version ${index.bundle} is not one this pubtheme reads (${BUNDLE_VERSIONS.join(", ")}); ` +
        "use a pubtheme release made for it",
    );
  }
  const objects = index.objects
    .filter((s) => s.held)
    .map((s) => readJson(path.join(dir, s.path)));
  const byCid = Object.fromEntries(objects.map((b) => [b.cid, b]));
  const names = Object.keys(index.names)
    .sort()
    .map((name) => readJson(path.join(dir, "def", `${name}.json`)));
  return { index, objects, byCid, names };
}

/**
 * Write the site for `bundles` with theme `theme` into `out`, which must be
 * empty or absent so nothing from an earlier build survives into this one.
 * `site` is the host's settings: title, description, logo, footer.
 */
export async function build({ theme, bundles, out, site = {}, pathPrefix = "/" }) {
  const themeDir = path.join(ROOT, "themes", theme);
  if (!fs.existsSync(path.join(themeDir, "theme.json"))) {
    const known = themes().map((t) => t.name).join(", ");
    throw new Error(`no theme named ${theme}; this pubtheme has: ${known}`);
  }
  prepare(out);
  const pub = loadBundles(bundles);
  const settings = {
    title: pub.index.title,
    base: pub.index.base,
    ...site,
  };

  const { default: configure } = await import(path.join(themeDir, "eleventy.config.js"));
  const eleventy = new Eleventy(path.join(themeDir, "src"), out, {
    quietMode: true,
    pathPrefix,
    configPath: false,
    config(eleventyConfig) {
      eleventyConfig.addGlobalData("pub", pub);
      eleventyConfig.addGlobalData("site", settings);
      // The objects' bytes and each bundle beside the page made from it,
      // so a reader can check a page against what it shows.
      eleventyConfig.addPassthroughCopy({ [path.join(bundles, "pub")]: "pub" });
      eleventyConfig.addPassthroughCopy({ [path.join(bundles, "o")]: "o" });
      eleventyConfig.addPassthroughCopy({ [path.join(bundles, "def")]: "def" });
      eleventyConfig.addPassthroughCopy({ [path.join(bundles, "index.json")]: "index.json" });
      if (settings.logo) {
        eleventyConfig.addPassthroughCopy({ [path.resolve(settings.logo)]: "logo.svg" });
      }
      return configure(eleventyConfig, { require });
    },
  });
  await eleventy.write();
  styles(themeDir, out);
  return { objects: pub.objects.length, names: pub.names.length };
}

/** Compile the theme's Tailwind stylesheet against the pages just written. */
function styles(themeDir, out) {
  const input = path.join(out, ".pubtheme-input.css");
  const tailwind = path.dirname(require.resolve("tailwindcss/package.json"));
  fs.writeFileSync(
    input,
    `@import "${path.join(tailwind, "index.css")}";\n` +
      `@import "${path.join(themeDir, "theme.css")}";\n` +
      `@source "${out}";\n`,
  );
  const cli = path.join(path.dirname(require.resolve("@tailwindcss/cli/package.json")), "dist", "index.mjs");
  const run = spawnSync(process.execPath, [cli, "-i", input, "-o", path.join(out, "style.css"), "--minify"], {
    encoding: "utf8",
  });
  fs.rmSync(input);
  if (run.status !== 0) {
    throw new Error(`tailwind failed:\n${run.stderr}`);
  }
}

function prepare(out) {
  if (fs.existsSync(out) && fs.readdirSync(out).length > 0) {
    throw new Error(`${out} is not empty; the site is written to an empty or new directory`);
  }
  fs.mkdirSync(out, { recursive: true });
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}
