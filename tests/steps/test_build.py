"""Steps for building a site from reading bundles.

They drive `pubtheme` as a host would, on a copy of publication 0's
bundles in the scenario's scratch directory, and read the pages it writes.
"""

from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/build.feature", "../features/concepts.feature", "../features/external.feature")

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


def _families(tmp_path: Path) -> dict[str, str]:
    """Each family by its parent code."""
    index = json.loads((_bundles(tmp_path) / "index.json").read_text())
    return {o["label"]: o["cid"] for o in index["objects"] if o.get("sort") == "family"}


def _family_page(tmp_path: Path, parent: str) -> str:
    return _page(tmp_path, "o", _families(tmp_path)[parent])


def _encoded(code: str) -> str:
    return "".join(c if c.isalnum() or c in "-._~" else f"%{ord(c):02X}" for c in code)


@given(parsers.parse('the family under "{parent}" has the signature status "{status}"'))
def family_signature(tmp_path, parent: str, status: str):
    cid = _families(tmp_path)[parent]
    _edit(_object_bundle(tmp_path, cid), lambda b: b["summary"].update(signature=status))
    for name in (_bundles(tmp_path) / "def").glob("*.json"):
        def change(n):
            if cid in n["related"]:
                n["related"][cid]["signature"] = status
        _edit(name, change)


@then(parsers.parse('the page for "{code}" lands on "{at}" in the family under "{parent}"'))
def lands(tmp_path, code: str, at: str, parent: str):
    page = _concept_page(tmp_path, code)
    href = f"/o/{_families(tmp_path)[parent]}/#{_encoded(at)}"
    assert f'<meta http-equiv="refresh" content="0; url={href}">' in page, page[:800]
    assert f'href="{href}"' in page, page


@then(parsers.parse('the family under "{parent}" has a place for "{code}"'))
def family_place(tmp_path, parent: str, code: str):
    assert f'id="{html.escape(code)}"' in _family_page(tmp_path, parent)


@then(parsers.parse('the family under "{parent}" names {codes} above it in that order'))
def family_crumbs(tmp_path, parent: str, codes: str):
    page = _family_page(tmp_path, parent)
    nav = page[page.index('aria-label="Broader classes"'):]
    nav = nav[:nav.index("</nav>")]
    wanted = [c.strip().strip('"') for c in codes.replace(" and ", ", ").split(",")]
    at = [nav.index(f"<code>{c}</code>") for c in wanted]
    assert at == sorted(at), (wanted, nav)


@then(parsers.parse('the family under "{parent}" links the family under "{code}"'))
def family_links(tmp_path, parent: str, code: str):
    page = _family_page(tmp_path, parent)
    assert f'href="/o/{_families(tmp_path)[code]}/"' in page and f"Classes under {code}" in page, page


@then(parsers.parse('the page for "{code}" links "{at}" in the family under "{parent}"'))
def concept_broader(tmp_path, code: str, at: str, parent: str):
    page = _concept_page(tmp_path, code)
    assert f'href="/o/{_families(tmp_path)[parent]}/#{_encoded(at)}"' in page, page


@then(parsers.parse('the family under "{parent}" says "{text}"'))
def family_says(tmp_path, parent: str, text: str):
    page = _family_page(tmp_path, parent)
    assert text in page or html.escape(text, quote=False) in page, page


@then("no page for a concept holds a script")
def no_script(tmp_path):
    for page in (_site(tmp_path) / "def").rglob("index.html"):
        assert "<script" not in page.read_text().lower(), page


# --- objects kept elsewhere --------------------------------------------------


def _rendered(tmp_path: Path, *ask: str) -> dict:
    helper = Path(__file__).resolve().parent / "rendered.mjs"
    out = subprocess.run(["node", str(helper), "elsewhere", "worker", "kept", *ask], cwd=tmp_path, check=True,
                         capture_output=True, text=True).stdout
    return json.loads(out)


def _kept_objects(tmp_path: Path) -> list[str]:
    index = json.loads((tmp_path / "kept" / "index.json").read_text())
    return [o["cid"] for o in index["objects"] if o["held"]]


@given("the same objects, bundled to be kept elsewhere")
def kept(tmp_path):
    shutil.copytree(_bundles(tmp_path), tmp_path / "kept")


@when("I build another site with those objects kept elsewhere", target_fixture="result")
def build_elsewhere(run, binary):
    return run(binary("pubtheme"), "build", "--bundles=bundles", "--out=elsewhere", "--external=kept", "--worker-out=worker")


@when("I build another site with --external alone", target_fixture="result")
def build_external_alone(run, binary):
    return run(binary("pubtheme"), "build", "--bundles=bundles", "--out=elsewhere", "--external=kept")


@then("that site has no page, bundle or bytes for those objects")
def no_object_files(tmp_path):
    site = tmp_path / "elsewhere"
    for cid in _kept_objects(tmp_path):
        assert not (site / "o" / cid).exists(), cid
        assert not (site / "o" / f"{cid}.json").exists(), cid
        assert not (site / "pub" / "v1" / "object" / cid).exists(), cid


@then("that site has no page for the names only they define")
def no_name_files(tmp_path):
    manifest = json.loads((tmp_path / "elsewhere" / "_external" / "manifest.json").read_text())
    assert manifest["segments"]
    for segment in manifest["segments"]:
        assert not (tmp_path / "elsewhere" / "def" / segment / "index.html").exists(), segment


@then("every name's rendered page is the page the whole site has")
def names_same(tmp_path):
    rendered = _rendered(tmp_path)["names"]
    assert rendered
    for segment, page in rendered.items():
        assert page == (_site(tmp_path) / "def" / segment / "index.html").read_text(), segment


@then("every object's rendered page is the page the whole site has")
def objects_same(tmp_path):
    rendered = _rendered(tmp_path)["objects"]
    assert set(rendered) == set(_kept_objects(tmp_path))
    for cid, page in rendered.items():
        assert page == (_site(tmp_path) / "o" / cid / "index.html").read_text(), cid


@then(parsers.parse('the index entry for "{code}" names the family under "{parent}"'))
def index_family(tmp_path, code: str, parent: str):
    manifest = json.loads((tmp_path / "elsewhere" / "_external" / "manifest.json").read_text())
    segment = code.replace("/", "_")
    shard = json.loads((tmp_path / "elsewhere" / "_external" / "index" / f"{manifest['segments'][segment]}.json").read_text())
    assert shard["names"][segment]["classes"] == [{"code": code, "family": _families(tmp_path)[parent]}]


@then(parsers.parse('a search for "{query}" finds "{code}" first'))
def search_first(tmp_path, query: str, code: str):
    assert _rendered(tmp_path, f"--search={query}")["found"][0]["code"] == code


@then(parsers.parse('a search for "{query}" finds nothing that lacks those words'))
def search_words(tmp_path, query: str):
    found = _rendered(tmp_path, f"--search={query}")["found"]
    assert found
    for entry in found:
        text = f"{entry['code']} {entry['label']}".lower()
        assert all(word in text for word in query.split()), entry


@then(parsers.parse('a search page for "{query}" shows it escaped'))
def search_escaped(tmp_path, query: str):
    page = _rendered(tmp_path, f"--search={query}")["page"]
    assert "<script>" not in page and html.escape(query, quote=False) in page
