#!/usr/bin/env python3
"""Make tests/testdata/concepts: reading bundles for the concept pages.

    tools/concept-testdata.py --pub=PATH/TO/pub

Needs a pub that knows the concept sort and bundles concepts (publet spec
Section 5.9.1; schryer/publet#49). Composes in a throwaway workspace:

- 20 classes of the UDC Summary (tests/testdata/concepts-src/pdc-sample.json)
  as subject concepts, each placed under its broader classes;
- a quantity concept, LED shelf electricity per growing area and day, at
  628.9~1, with two extracts classified under it, then revised once;
- a competing concept at the same code, so the code is contested;
- a relation concept at 628.9~2 and a calculation that solves it;
- an anchor (an expert group) over 628.9, and a triage suggestion.

`pub` has no command for anchors or triage, so those two are built here as
canonical CBOR, unsigned like the rest. Everything is fake test data.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tests" / "testdata" / "concepts-src" / "pdc-sample.json"
OUT = ROOT / "tests" / "testdata" / "concepts"
AT = "2026-10-14T12:00:00Z"


# --- canonical CBOR, for the two objects pub has no command for -------------

def head(major: int, arg: int) -> bytes:
    m = major << 5
    if arg <= 23:
        return bytes([m | arg])
    if arg <= 0xFF:
        return bytes([m | 24, arg])
    if arg <= 0xFFFF:
        return bytes([m | 25]) + arg.to_bytes(2, "big")
    return bytes([m | 26]) + arg.to_bytes(4, "big")


def cbor(v) -> bytes:
    if isinstance(v, str):
        raw = unicodedata.normalize("NFC", v).encode()
        return head(3, len(raw)) + raw
    if isinstance(v, bool):
        return bytes([0xF5 if v else 0xF4])
    if isinstance(v, int):
        return head(0, v)
    if isinstance(v, list):
        return head(4, len(v)) + b"".join(cbor(x) for x in v)
    items = sorted(v.items(), key=lambda kv: kv[0].encode())
    return head(5, len(items)) + b"".join(cbor(k) + cbor(x) for k, x in items)


def cid_of(data: bytes) -> str:
    return "pub:sha2-256:" + base64.b32encode(hashlib.sha256(data).digest()).decode().lower().rstrip("=")


def obj(kind: str, author: str, body: dict) -> bytes:
    return cbor({"pub": "1", "type": kind, "created": AT, "author": author, "body": body})


# --- pub ---------------------------------------------------------------------

class Pub:
    def __init__(self, pub: str, workspace: Path):
        self.pub, self.ws = pub, workspace

    def __call__(self, *args: str) -> str:
        out = subprocess.run([self.pub, *args], cwd=self.ws, capture_output=True, text=True)
        if out.returncode != 0:
            raise SystemExit(f"pub {' '.join(args[:2])}: {out.stderr.strip()}")
        return out.stdout.split()[0] if out.stdout.split() else ""

    def define(self, content: str, defines: dict, *depends: str, cls: str = "definitional") -> str:
        path = self.ws / "defines.json"
        path.write_text(json.dumps(defines))
        return self("compose", f"--created={AT}", f"--class={cls}", f"--content={content}",
                    "--scope=unconditional", f"--defines={path}", *[f"--depends={d}" for d in depends])

    def classify(self, member: str, subject: str) -> str:
        return self("annotate", f"--created={AT}", "--kind=classifies", f"--target={member}",
                    f"--subject={subject}", "--scope=unconditional")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pub", required=True)
    args = parser.parse_args()
    ws = Path(tempfile.mkdtemp(prefix="pubtheme-concepts-"))
    pub = Pub(args.pub, ws)
    pub("init")

    # The PDC sample: subject concepts, placed under their broader classes.
    sample = json.loads(SRC.read_text())
    code = {}
    for c in sample["classes"]:
        code[c["pdc"]] = pub.define(c["claim"]["content"], c["claim"]["defines"])
    for c in sample["classes"]:
        for parent in c["broader"]:
            if parent in code:
                pub.classify(code[c["pdc"]], code[parent])

    # Units and kinds.
    ucum = pub.define("UCUM: the Unified Code for Units of Measure, version 2.2.",
                      {"sort": "system", "name": "UCUM", "version": "2.2"})
    energy = pub.define("energy per area and time: energy used per growing area per day.",
                        {"sort": "kind", "name": "energy per area and time", "dimension": {"g": 1, "s": -3}}, ucum)
    power = pub.define("power per area: lamp power per growing area.",
                       {"sort": "kind", "name": "power per area", "dimension": {"g": 1, "s": -3}}, ucum)
    share = pub.define("share of the day: the fraction of a day the lights are on.",
                       {"sort": "kind", "name": "share of the day", "dimension": {}}, ucum)

    # A quantity concept under 628.9, its members, a revision, and a competitor.
    led = {"sort": "concept", "pdc": "628.9~1", "name": "LED shelf electricity per growing area and day",
           "kind": energy, "boundary": {"includes": ["Indoor shelves or racks lit only by LEDs"],
                                        "excludes": ["Daylight greenhouses"]}}
    first = pub.define("LED shelf electricity per growing area and day: what LED shelves use.", led)
    led["boundary"]["includes"].append("Electricity for lights, fans and pumps")
    defines2 = ws / "defines2.json"
    defines2.write_text(json.dumps(led))
    revised = pub("revise", first, f"--created=2026-10-14T13:00:00Z",
                  "--content=LED shelf electricity per growing area and day: what LED shelves use, with fans and pumps.",
                  f"--defines={defines2}")
    pub.classify(revised, code["628.9"])
    competitor = pub.define("Indoor lighting electricity: any electric light for plants indoors.",
                            {"sort": "concept", "pdc": "628.9~1", "name": "Indoor plant lighting electricity",
                             "kind": energy, "boundary": {"includes": ["Any electric light for plants indoors"],
                                                          "excludes": []}})
    method = pub("compose", f"--created={AT}", "--class=procedural", "--scope=unconditional",
                 "--content=Read the electricity figure from the paper's table (fake).")
    extracts = []
    for content in ["Gargaro et al. 2025 (fake): a vertical farm's LED shelves used 1.1 kWh per m2 per day.",
                    "Piovano et al. 2026 (fake): LED shelves used 0.9 to 1.3 kWh per m2 per day."]:
        e = pub("compose", f"--created={AT}", "--class=empirical", "--scope=unconditional",
                f"--content={content}", f"--method={method}")
        extracts.append(e)
        pub.classify(e, revised)

    # A relation concept and a calculation solving it.
    relation = pub.define(
        "LED shelf electricity from lamp power: energy is lamp power times the share of the day lit.",
        {"sort": "concept", "pdc": "628.9~2", "name": "LED shelf electricity from lamp power",
         "relation": {"statement": "energy per area and day = lamp power per area x share of the day lit",
                      "slots": [{"role": "energy", "concept": "628.9~1"}, {"role": "power", "kind": power},
                                {"role": "lit", "kind": share}],
                      "form": {"product": {"coefficient": "1",
                                           "exponents": {"energy": 1, "power": -1, "lit": -1}}}}},
        revised)
    pub.classify(relation, code["628.9"])
    default = pub("compose", f"--created={AT}", "--class=normative", "--scope=unconditional",
                  "--content=Without a stated photoperiod, assume 16 hours of light a day (fake).")
    computes = ws / "computes.json"
    computes.write_text(json.dumps({"solves": {"concept": "628.9~2", "target": "energy", "requires": ["power"],
                                               "optional": [{"role": "lit", "default": default}]}}))
    pub("compose", f"--created={AT}", "--class=procedural", "--scope=unconditional",
        "--content=Multiply lamp power per area by the share of the day lit (fake).",
        f"--computes={computes}", f"--depends={relation}", f"--depends={default}")

    # Bundle the workspace, then add the anchor and the triage suggestion.
    staging = ws / "staging"
    pub("bundle", f"--out={staging}")
    objects = ws / "objects"
    objects.mkdir()
    for f in (staging / "pub" / "v1" / "object").iterdir():
        (objects / (f.name.replace(":", "_") + ".cbor")).write_bytes(f.read_bytes())
    steward = cid_of(b"a steward key (fake)")
    anchor = obj("anchor", steward, {
        "lineage": code["628.9"], "current": code["628.9"], "rationale": method,
        "stewards": [steward, cid_of(b"a second steward key (fake)")], "threshold": 1})
    suggester = cid_of(b"a suggester key (fake)")
    triage = obj("claim.annotation", suggester, {
        "kind": "triage", "target": extracts[0],
        "value": {"finding": "groups-under", "refs": [revised, *extracts],
                  "engine": {"model": "a model (fake)", "version": "2026-10",
                             "prompt": cid_of(b"prompt"), "inputs": cid_of(b"inputs")},
                  "candidate": cid_of(b"candidate drafts")}})
    for data in (anchor, triage):
        (objects / (cid_of(data).replace(":", "_") + ".cbor")).write_bytes(data)
    if OUT.exists():
        shutil.rmtree(OUT)
    subprocess.run([args.pub, "bundle", f"--dir={objects}", f"--out={OUT}", "--base=https://pub.example.org",
                    "--title=Concept pages (test data)"], check=True)
    shutil.rmtree(ws)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
