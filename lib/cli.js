// pubtheme: build a static site from publet reading bundles with a theme.
//
//   pubtheme build --bundles=DIR --out=DIR [--theme=sustenaut] [--site=FILE] [--path-prefix=/]
//   pubtheme themes
//
// The bundles come from `pub bundle`. --site names a JSON file of the
// host's settings (title, description, logo, footer).

import fs from "node:fs";
import path from "node:path";

import { build, themes } from "./build.js";

const USAGE =
  "usage: pubtheme build --bundles=DIR --out=DIR [--theme=sustenaut] [--site=FILE] [--path-prefix=/]\n" +
  "       pubtheme themes";

async function main(argv) {
  const [command, ...rest] = argv;
  if (command === "themes") {
    for (const t of themes()) console.log(`${t.name}\t${t.description ?? ""}`);
    return 0;
  }
  if (command !== "build") {
    console.error(USAGE);
    return 2;
  }
  const options = { theme: "sustenaut", pathPrefix: "/" };
  for (const arg of rest) {
    const [key, value] = arg.split(/=(.*)/s);
    switch (key) {
      case "--bundles":
        options.bundles = path.resolve(value);
        break;
      case "--out":
        options.out = path.resolve(value);
        break;
      case "--theme":
        options.theme = value;
        break;
      case "--site":
        options.site = JSON.parse(fs.readFileSync(value, "utf8"));
        if (options.site.logo) options.site.logo = path.resolve(path.dirname(value), options.site.logo);
        break;
      case "--path-prefix":
        options.pathPrefix = value;
        break;
      default:
        console.error(`unknown argument: ${arg}\n${USAGE}`);
        return 2;
    }
  }
  if (!options.bundles || !options.out) {
    console.error(`--bundles and --out are required\n${USAGE}`);
    return 2;
  }
  const done = await build(options);
  console.log(`${done.objects} object page(s) and ${done.names} name page(s) in ${options.out}`);
  return 0;
}

main(process.argv.slice(2)).then(
  (code) => process.exit(code),
  (error) => {
    console.error(error.message);
    process.exit(1);
  },
);
