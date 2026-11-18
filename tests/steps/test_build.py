"""Steps for building a site from reading bundles.

pubtest's steps copy the bundles into the scenario's scratch directory and
run `pubtheme` there as a host would; these set up the bundles' own changes
and read the pages it writes.
"""

from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then

scenarios("../features/build.feature", "../features/concepts.feature", "../features/external.feature")

TRAY_ENERGY = "pub:sha2-256:byz5xtavm3aqnn2kqgv5skwbvmhdpdefkb7jumscxlhfpubtiyla"
TRAY = "pub:sha2-256:cce4jzdasl2f3bbp4pwdpetu5l3naxt55xovsrs2cqx5tab6tfpa"
CLIMATE_HOME = "pub:sha2-256:qbogwvodjpvfifeh65x6est6w4b5buesgvg2ytb3zzcdqifncteq"
THREE_POINT = "pub:sha2-256:i7vdofelpheguwjkovn4kckk4rye3jpsn7h4hptfsztbm7x6zw2a"


def _bundles(root: Path) -> Path:
    return root / "bundles"


def _site(root: Path) -> Path:
    return root / "site"


def _object_bundle(root: Path, cid: str) -> Path:
    return _bundles(root) / "o" / f"{cid}.json"


def _edit(path: Path, change) -> None:
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def _page(root: Path, *parts: str) -> str:
    path = _site(root).joinpath(*parts, "index.html")
    assert path.is_file(), f"no page at {path}"
    return path.read_text()


# --- givens ------------------------------------------------------------------


@given("the tray energy claim holds an estimate with high, likely and low")
def estimate(pubtest_ctx):
    def change(b):
        b["object"]["body"]["data"]["rows"][0][1] = {"high": "1.4", "likely": "1.1", "low": "0.8"}
    _edit(_object_bundle(pubtest_ctx.directory, TRAY_ENERGY), change)


@given("the tray energy claim's content holds markup")
def markup(pubtest_ctx):
    def change(b):
        b["object"]["body"]["content"] = "Trays <script>alert(1)</script> & lids."
    _edit(_object_bundle(pubtest_ctx.directory, TRAY_ENERGY), change)


@given(parsers.parse("the bundles say they are version {version:d}"))
def version(pubtest_ctx, version: int):
    _edit(_bundles(pubtest_ctx.directory) / "index.json", lambda d: d.update(bundle=version))


# --- thens -------------------------------------------------------------------


@then("every object in the bundles has a page")
def every_object(pubtest_ctx):
    index = json.loads((_bundles(pubtest_ctx.directory) / "index.json").read_text())
    for o in index["objects"]:
        _page(pubtest_ctx.directory, "o", o["cid"])


@then(parsers.parse('the name "{name}" has a page'))
def name_page(pubtest_ctx, name: str):
    page = _page(pubtest_ctx.directory, "def", name)
    assert f"/o/{TRAY}/" in page, page


@then("the index links every claim's page")
def index_links(pubtest_ctx):
    index = json.loads((_bundles(pubtest_ctx.directory) / "index.json").read_text())
    page = (_site(pubtest_ctx.directory) / "index.html").read_text()
    for o in index["objects"]:
        if o.get("class") and not o.get("sort"):
            assert f'href="/o/{o["cid"]}/"' in page, o["label"]


@then("every object's canonical bytes are copied unchanged")
def bytes_copied(pubtest_ctx):
    for source in (_bundles(pubtest_ctx.directory) / "pub" / "v1" / "object").iterdir():
        copied = _site(pubtest_ctx.directory) / "pub" / "v1" / "object" / source.name
        assert copied.read_bytes() == source.read_bytes(), source.name


@then("every object's reading bundle is copied beside its page")
def bundles_copied(pubtest_ctx):
    for source in (_bundles(pubtest_ctx.directory) / "o").iterdir():
        assert (_site(pubtest_ctx.directory) / "o" / source.name).read_text() == source.read_text()


@then("the tray energy claim's page links the tray dimension as its unit")
def links_unit(pubtest_ctx):
    page = _page(pubtest_ctx.directory, "o", TRAY_ENERGY)
    unit = page.index(f'href="/o/{TRAY}/"')
    assert ">unit<" in page[unit:unit + 400], page[unit:unit + 400]


@then("the tray energy claim's page links the claim computed from it")
def links_user(pubtest_ctx):
    page = _page(pubtest_ctx.directory, "o", TRAY_ENERGY)
    assert f'href="/o/{CLIMATE_HOME}/"' in page, page


@then(parsers.parse('the tray energy claim\'s page says "{fragment}"'))
def page_says(pubtest_ctx, fragment: str):
    assert fragment in _page(pubtest_ctx.directory, "o", TRAY_ENERGY)


@then("the tray energy claim's page shows low, likely and high in that order")
def quantity_order(pubtest_ctx):
    page = _page(pubtest_ctx.directory, "o", TRAY_ENERGY)
    cells = page.split("<tbody>", 1)[1]
    positions = [cells.find(f">{k}<") for k in ("low", "likely", "high")]
    assert -1 not in positions and positions == sorted(positions), cells[:800]


@then("the tray energy claim's page shows the markup escaped")
def escaped(pubtest_ctx):
    page = _page(pubtest_ctx.directory, "o", TRAY_ENERGY)
    assert "<script>" not in page, page
    assert html.escape("Trays <script>alert(1)</script> & lids.", quote=False) in page, page


# --- concepts (publet spec Section 5.9.1) --------------------------------------


def _concept_page(root: Path, code: str) -> str:
    return _page(root, "def", code.replace("/", "_"))


@then(parsers.parse('the page for "{code}" says "{text}"'))
def concept_says(pubtest_ctx, code: str, text: str):
    page = _concept_page(pubtest_ctx.directory, code)
    assert text in page or html.escape(text, quote=False) in page, page[:2000]


def _extracts(root: Path) -> dict[str, str]:
    index = json.loads((_bundles(root) / "index.json").read_text())
    return {o["label"].split(" ")[0]: o["cid"] for o in index["objects"]
            if o.get("class") == "empirical"}


@then(parsers.parse('the page for "{code}" lists both extracts as members'))
def concept_members(pubtest_ctx, code: str):
    page = _concept_page(pubtest_ctx.directory, code)
    for cid in _extracts(pubtest_ctx.directory).values():
        assert f"/o/{cid}/" in page, cid


@then(parsers.parse('the classification page lists "{child}" under "{parent}" under "{top}"'))
def classification(pubtest_ctx, child: str, parent: str, top: str):
    page = _page(pubtest_ctx.directory, "pdc")
    at = [page.index(f"<code>{code}</code>") for code in (top, parent, child)]
    assert at == sorted(at), at


@then(parsers.parse('the Gargaro extract\'s page names the concept "{code}"'))
def extract_concept(pubtest_ctx, code: str):
    page = _page(pubtest_ctx.directory, "o", _extracts(pubtest_ctx.directory)["Gargaro"])
    assert f'href="/def/{code}/"' in page and "Member of" in page, page[:3000]


@then(parsers.parse('the Gargaro extract\'s page links its suggestion at "{prefix}"'))
def extract_suggestion(pubtest_ctx, prefix: str):
    page = _page(pubtest_ctx.directory, "o", _extracts(pubtest_ctx.directory)["Gargaro"])
    assert f'href="{prefix}pub%3Asha2-256%3A' in page, page[:3000]


def _families(root: Path) -> dict[str, str]:
    """Each family by its parent code."""
    index = json.loads((_bundles(root) / "index.json").read_text())
    return {o["label"]: o["cid"] for o in index["objects"] if o.get("sort") == "family"}


def _family_page(root: Path, parent: str) -> str:
    return _page(root, "o", _families(root)[parent])


def _encoded(code: str) -> str:
    return "".join(c if c.isalnum() or c in "-._~" else f"%{ord(c):02X}" for c in code)


@given(parsers.parse('the family under "{parent}" has the signature status "{status}"'))
def family_signature(pubtest_ctx, parent: str, status: str):
    cid = _families(pubtest_ctx.directory)[parent]
    _edit(_object_bundle(pubtest_ctx.directory, cid), lambda b: b["summary"].update(signature=status))
    for name in (_bundles(pubtest_ctx.directory) / "def").glob("*.json"):
        def change(n):
            if cid in n["related"]:
                n["related"][cid]["signature"] = status
        _edit(name, change)


@then(parsers.parse('the page for "{code}" lands on "{at}" in the family under "{parent}"'))
def lands(pubtest_ctx, code: str, at: str, parent: str):
    page = _concept_page(pubtest_ctx.directory, code)
    href = f"/o/{_families(pubtest_ctx.directory)[parent]}/#{_encoded(at)}"
    assert f'<meta http-equiv="refresh" content="0; url={href}">' in page, page[:800]
    assert f'href="{href}"' in page, page


@then(parsers.parse('the family under "{parent}" has a place for "{code}"'))
def family_place(pubtest_ctx, parent: str, code: str):
    assert f'id="{html.escape(code)}"' in _family_page(pubtest_ctx.directory, parent)


@then(parsers.parse('the family under "{parent}" names {codes} above it in that order'))
def family_crumbs(pubtest_ctx, parent: str, codes: str):
    page = _family_page(pubtest_ctx.directory, parent)
    nav = page[page.index('aria-label="Broader classes"'):]
    nav = nav[:nav.index("</nav>")]
    wanted = [c.strip().strip('"') for c in codes.replace(" and ", ", ").split(",")]
    at = [nav.index(f"<code>{c}</code>") for c in wanted]
    assert at == sorted(at), (wanted, nav)


@then(parsers.parse('the family under "{parent}" links the family under "{code}"'))
def family_links(pubtest_ctx, parent: str, code: str):
    page = _family_page(pubtest_ctx.directory, parent)
    assert f'href="/o/{_families(pubtest_ctx.directory)[code]}/"' in page and f"Classes under {code}" in page, page


@then(parsers.parse('the page for "{code}" links "{at}" in the family under "{parent}"'))
def concept_broader(pubtest_ctx, code: str, at: str, parent: str):
    page = _concept_page(pubtest_ctx.directory, code)
    assert f'href="/o/{_families(pubtest_ctx.directory)[parent]}/#{_encoded(at)}"' in page, page


@then(parsers.parse('the family under "{parent}" says "{text}"'))
def family_says(pubtest_ctx, parent: str, text: str):
    page = _family_page(pubtest_ctx.directory, parent)
    assert text in page or html.escape(text, quote=False) in page, page


@then("no page for a concept holds a script")
def no_script(pubtest_ctx):
    for page in (_site(pubtest_ctx.directory) / "def").rglob("index.html"):
        assert "<script" not in page.read_text().lower(), page


# --- objects kept elsewhere --------------------------------------------------


def _rendered(root: Path, *ask: str) -> dict:
    helper = Path(__file__).resolve().parent / "rendered.mjs"
    out = subprocess.run(["node", str(helper), "elsewhere", "worker", "kept", *ask], cwd=root, check=True,
                         capture_output=True, text=True).stdout
    return json.loads(out)


def _kept_objects(root: Path) -> list[str]:
    index = json.loads((root / "kept" / "index.json").read_text())
    return [o["cid"] for o in index["objects"] if o["held"]]


@then("that site has no page, bundle or bytes for those objects")
def no_object_files(pubtest_ctx):
    site = pubtest_ctx.directory / "elsewhere"
    for cid in _kept_objects(pubtest_ctx.directory):
        assert not (site / "o" / cid).exists(), cid
        assert not (site / "o" / f"{cid}.json").exists(), cid
        assert not (site / "pub" / "v1" / "object" / cid).exists(), cid


@then("that site has no page for the names only they define")
def no_name_files(pubtest_ctx):
    manifest = json.loads((pubtest_ctx.directory / "elsewhere" / "_external" / "manifest.json").read_text())
    assert manifest["segments"]
    for segment in manifest["segments"]:
        assert not (pubtest_ctx.directory / "elsewhere" / "def" / segment / "index.html").exists(), segment


@then("every name's rendered page is the page the whole site has")
def names_same(pubtest_ctx):
    rendered = _rendered(pubtest_ctx.directory)["names"]
    assert rendered
    for segment, page in rendered.items():
        assert page == (_site(pubtest_ctx.directory) / "def" / segment / "index.html").read_text(), segment


@then("every object's rendered page is the page the whole site has")
def objects_same(pubtest_ctx):
    rendered = _rendered(pubtest_ctx.directory)["objects"]
    assert set(rendered) == set(_kept_objects(pubtest_ctx.directory))
    for cid, page in rendered.items():
        assert page == (_site(pubtest_ctx.directory) / "o" / cid / "index.html").read_text(), cid


@then(parsers.parse('the index entry for "{code}" names the family under "{parent}"'))
def index_family(pubtest_ctx, code: str, parent: str):
    manifest = json.loads((pubtest_ctx.directory / "elsewhere" / "_external" / "manifest.json").read_text())
    segment = code.replace("/", "_")
    shard = json.loads((pubtest_ctx.directory / "elsewhere" / "_external" / "index" / f"{manifest['segments'][segment]}.json").read_text())
    assert shard["names"][segment]["classes"] == [{"code": code, "family": _families(pubtest_ctx.directory)[parent]}]


@then(parsers.parse('a search for "{query}" finds "{code}" first'))
def search_first(pubtest_ctx, query: str, code: str):
    assert _rendered(pubtest_ctx.directory, f"--search={query}")["found"][0]["code"] == code


@then(parsers.parse('a search for "{query}" finds nothing that lacks those words'))
def search_words(pubtest_ctx, query: str):
    found = _rendered(pubtest_ctx.directory, f"--search={query}")["found"]
    assert found
    for entry in found:
        text = f"{entry['code']} {entry['label']}".lower()
        assert all(word in text for word in query.split()), entry


@then(parsers.parse('a search page for "{query}" shows it escaped'))
def search_escaped(pubtest_ctx, query: str):
    page = _rendered(pubtest_ctx.directory, f"--search={query}")["page"]
    assert "<script>" not in page and html.escape(query, quote=False) in page
