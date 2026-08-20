"""Unit tests for scripts/wiki-eval.py PURE metric + parse functions. No qmd index, no
embedding model, no wiki required -- runs everywhere (CI-safe). The subprocess-backed
run_query / live eval are exercised only by the local-only gate (tests/test_wiki_eval.py)."""
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "wiki-eval.py")
spec = importlib.util.spec_from_file_location("wiki_eval", SCRIPT)
we = importlib.util.module_from_spec(spec)
spec.loader.exec_module(we)

# `qmd ... --format json` shape: a list of hits, each carrying a "file" field of
# "qmd://<collection>/<relpath>" plus score/title/snippet fields parse_results ignores.
SEMANTIC = json.dumps([
    {"file": "qmd://wiki/techniques/web/ssrf.md", "score": 0.842},
    {"file": "qmd://wiki/payloads/ssrf.md", "score": 0.7},
    {"file": "qmd://wiki/techniques/web/xxe.md", "score": 0.51},
])
KEYWORD = json.dumps([
    {"file": "qmd://wiki/tools/netexec.md"},
    {"file": "qmd://wiki/tools/nmap.md"},
])


def test_parse_semantic_strips_score_and_keeps_paths():
    assert we.parse_results(SEMANTIC) == ["techniques/web/ssrf.md", "payloads/ssrf.md", "techniques/web/xxe.md"]


def test_parse_keyword_bare_paths():
    assert we.parse_results(KEYWORD) == ["tools/netexec.md", "tools/nmap.md"]


def test_parse_ignores_prose_blocks():
    # a hit from another collection (no "qmd://wiki/" prefix) must not be counted as a result
    other_collection = json.dumps([
        {"file": "qmd://wiki/techniques/web/xss.md"},
        {"file": "qmd://notes/some-file.md"},
    ])
    assert we.parse_results(other_collection) == ["techniques/web/xss.md"]


def test_hit_at_topk():
    ranked = ["a.md", "b.md", "c.md", "d.md"]
    assert we.hit_at(ranked, ["c.md"], 3) is True
    assert we.hit_at(ranked, ["d.md"], 3) is False
    assert we.hit_at(ranked, ["d.md"], 5) is True
    assert we.hit_at(ranked, ["x.md", "b.md"], 3) is True   # any expected counts (twins)


def test_reciprocal_rank():
    ranked = ["a.md", "b.md", "c.md"]
    assert we.reciprocal_rank(ranked, ["b.md"]) == 0.5
    assert we.reciprocal_rank(ranked, ["a.md"]) == 1.0
    assert we.reciprocal_rank(ranked, ["z.md"]) == 0.0
