"""Steps for building a site from reading bundles.

They drive `pubtheme` as a host would, on a copy of publication 0's
bundles in the scenario's scratch directory, and read the pages it writes.
"""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/build.feature", "../features/concepts.feature")

TESTDATA = Path(__file__).resolve().parent.parent / "testdata" / "publication-0"
CONCEPTS = Path(__file__).resolve().parent.parent / "testdata" / "concepts"
TRAY_ENERGY = "pub:sha2-256:byz5xtavm3aqnn2kqgv5skwbvmhdpdefkb7jumscxlhfpubtiyla"
TRAY = "pub:sha2-256:cce4jzdasl2f3bbp4pwdpetu5l3naxt55xovsrs2cqx5tab6tfpa"
CLIMATE_HOME = "pub:sha2-256:qbogwvodjpvfifeh65x6est6w4b5buesgvg2ytb3zzcdqifncteq"
THREE_POINT = "pub:sha2-256:i7vdofelpheguwjkovn4kckk4rye3jpsn7h4hptfsztbm7x6zw2a"


def _bundles(tmp_path: Path) -> Path:
    return tmp_path / "bundles"


def _site(tmp_path: Path) -> Path:
    return tmp_path / "site"


def _object_bundle(tmp_path: Path, cid: str) -> Path:
    return _bundles(tmp_path) / "o" / f"{cid}.json"


def _edit(path: Path, change) -> None:
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def _page(tmp_path: Path, *parts: str) -> str:
    path = _site(tmp_path).joinpath(*parts, "index.html")
    assert path.is_file(), f"no page at {path}"
    return path.read_text()


# --- givens ------------------------------------------------------------------


@given("the reading bundles of publication 0")
def bundles(tmp_path):
    shutil.copytree(TESTDATA, _bundles(tmp_path))


@given("the tray energy claim holds an estimate with high, likely and low")
def estimate(tmp_path):
    def change(b):
        b["object"]["body"]["data"]["rows"][0][1] = {"high": "1.4", "likely": "1.1", "low": "0.8"}
    _edit(_object_bundle(tmp_path, TRAY_ENERGY), change)


@given("the tray energy claim's content holds markup")
def markup(tmp_path):
    def change(b):
        b["object"]["body"]["content"] = "Trays <script>alert(1)</script> & lids."
    _edit(_object_bundle(tmp_path, TRAY_ENERGY), change)


@given(parsers.parse('a site settings file titling the site "{title}"'))
def settings(tmp_path, title: str):
    (tmp_path / "site.json").write_text(json.dumps({"title": title}))


@given(parsers.parse("the bundles say they are version {version:d}"))
def version(tmp_path, version: int):
    _edit(_bundles(tmp_path) / "index.json", lambda d: d.update(bundle=version))


@given("the site directory already holds a file")
def site_not_empty(tmp_path):
    _site(tmp_path).mkdir()
    (_site(tmp_path) / "old.html").write_text("an earlier page")


# --- whens -------------------------------------------------------------------


@when("I build the site with the sustenaut theme", target_fixture="result")
def build(run, binary):
    return run(binary("pubtheme"), "build", "--bundles=bundles", "--out=site", "--theme=sustenaut")


@when("I build the site with those settings", target_fixture="result")
def build_with_settings(run, binary):
    return run(binary("pubtheme"), "build", "--bundles=bundles", "--out=site", "--site=site.json")


@when(parsers.parse('I build the site with a theme named "{theme}"'), target_fixture="result")
def build_unknown(run, binary, theme: str):
    return run(binary("pubtheme"), "build", "--bundles=bundles", "--out=site", f"--theme={theme}")


@when("I list the themes", target_fixture="result")
def list_themes(run, binary):
    return run(binary("pubtheme"), "themes")


# --- thens -------------------------------------------------------------------


@then("every object in the bundles has a page")
def every_object(tmp_path):
    index = json.loads((_bundles(tmp_path) / "index.json").read_text())
    for o in index["objects"]:
        _page(tmp_path, "o", o["cid"])


@then(parsers.parse('the name "{name}" has a page'))
def name_page(tmp_path, name: str):
    page = _page(tmp_path, "def", name)
    assert f"/o/{TRAY}/" in page, page


@then("the index links every claim's page")
def index_links(tmp_path):
    index = json.loads((_bundles(tmp_path) / "index.json").read_text())
    page = (_site(tmp_path) / "index.html").read_text()
    for o in index["objects"]:
        if o.get("class") and not o.get("sort"):
            assert f'href="/o/{o["cid"]}/"' in page, o["label"]


@then("the site has a stylesheet carrying the theme's colours")
def stylesheet(tmp_path):
    css = (_site(tmp_path) / "style.css").read_text()
    assert "--color-ground" in css and "#f3efe2" in css.lower(), css[:400]


@then("every object's canonical bytes are copied unchanged")
def bytes_copied(tmp_path):
    for source in (_bundles(tmp_path) / "pub" / "v1" / "object").iterdir():
        copied = _site(tmp_path) / "pub" / "v1" / "object" / source.name
        assert copied.read_bytes() == source.read_bytes(), source.name


@then("every object's reading bundle is copied beside its page")
def bundles_copied(tmp_path):
    for source in (_bundles(tmp_path) / "o").iterdir():
        assert (_site(tmp_path) / "o" / source.name).read_text() == source.read_text()


@then("the tray energy claim's page links the tray dimension as its unit")
def links_unit(tmp_path):
    page = _page(tmp_path, "o", TRAY_ENERGY)
    unit = page.index(f'href="/o/{TRAY}/"')
    assert ">unit<" in page[unit:unit + 400], page[unit:unit + 400]


@then("the tray energy claim's page links the claim computed from it")
def links_user(tmp_path):
    page = _page(tmp_path, "o", TRAY_ENERGY)
    assert f'href="/o/{CLIMATE_HOME}/"' in page, page


@then(parsers.parse('the tray energy claim\'s page says "{fragment}"'))
def page_says(tmp_path, fragment: str):
    assert fragment in _page(tmp_path, "o", TRAY_ENERGY)


@then("the tray energy claim's page shows low, likely and high in that order")
def quantity_order(tmp_path):
    page = _page(tmp_path, "o", TRAY_ENERGY)
    cells = page.split("<tbody>", 1)[1]
    positions = [cells.find(f">{k}<") for k in ("low", "likely", "high")]
    assert -1 not in positions and positions == sorted(positions), cells[:800]


@then("the tray energy claim's page shows the markup escaped")
def escaped(tmp_path):
    page = _page(tmp_path, "o", TRAY_ENERGY)
    assert "<script>" not in page, page
    assert html.escape("Trays <script>alert(1)</script> & lids.", quote=False) in page, page


@then(parsers.parse('the index is titled "{title}"'))
def titled(tmp_path, title: str):
    page = (_site(tmp_path) / "index.html").read_text()
    assert f"<title>{title}</title>" in page, page[:600]


# --- concepts (publet spec Section 5.9.1) --------------------------------------


@given("the reading bundles of the PDC sample")
def concept_bundles(tmp_path):
    shutil.copytree(CONCEPTS, _bundles(tmp_path))


def _concept_page(tmp_path: Path, code: str) -> str:
    return _page(tmp_path, "def", code.replace("/", "_"))


@then(parsers.parse('the page for "{code}" says "{text}"'))
def concept_says(tmp_path, code: str, text: str):
    page = _concept_page(tmp_path, code)
    assert text in page or html.escape(text, quote=False) in page, page[:2000]


def _extracts(tmp_path: Path) -> dict[str, str]:
    index = json.loads((_bundles(tmp_path) / "index.json").read_text())
    return {o["label"].split(" ")[0]: o["cid"] for o in index["objects"]
            if o.get("class") == "empirical"}


@then(parsers.parse('the page for "{code}" lists both extracts as members'))
def concept_members(tmp_path, code: str):
    page = _concept_page(tmp_path, code)
    for cid in _extracts(tmp_path).values():
        assert f"/o/{cid}/" in page, cid


@then(parsers.parse('the classification page lists "{child}" under "{parent}" under "{top}"'))
def classification(tmp_path, child: str, parent: str, top: str):
    page = _page(tmp_path, "pdc")
    at = [page.index(f"<code>{code}</code>") for code in (top, parent, child)]
    assert at == sorted(at), at


@then(parsers.parse('the Gargaro extract\'s page names the concept "{code}"'))
def extract_concept(tmp_path, code: str):
    page = _page(tmp_path, "o", _extracts(tmp_path)["Gargaro"])
    assert f'href="/def/{code}/"' in page and "Member of" in page, page[:3000]


@then(parsers.parse('the Gargaro extract\'s page links its suggestion at "{prefix}"'))
def extract_suggestion(tmp_path, prefix: str):
    page = _page(tmp_path, "o", _extracts(tmp_path)["Gargaro"])
    assert f'href="{prefix}pub%3Asha2-256%3A' in page, page[:3000]


@then("no page for a concept holds a script")
def no_script(tmp_path):
    for page in (_site(tmp_path) / "def").rglob("index.html"):
        assert "<script" not in page.read_text().lower(), page
