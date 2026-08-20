#!/usr/bin/env python3
"""wiki-eval.py - retrieval quality harness for the qmd-indexed wiki.

Reads a tracked gold set (scripts/wiki-eval-gold.json) of representative pentest queries,
each mapped to the canonical wiki page(s) that MUST rank. For each query it runs the qmd
CLI (hybrid `qmd query --no-rerank`, or keyword `qmd search` when mode="keyword") against
the `wiki` collection and computes hit@3, hit@5, and MRR, per-query and aggregate. Result
paths are wiki-relative (e.g. techniques/web/ssrf.md); a query hits if ANY of its expected
paths is in the top-k (either counts).

Read-only against the live index. Shells out to `qmd ... --format json` per query (the qmd
CLI is a standalone binary, not a Python-importable module) and parses each hit's "file"
field. QMD_VAULT is set automatically. Exit 0 for reports; exit 1 for the gate modes
(--verify-gold with a missing page, --check with a regression).

  python3 scripts/wiki-eval.py                 # human report (per-query + aggregate)
  python3 scripts/wiki-eval.py --json          # metrics as JSON (subagent/CI consumption)
  python3 scripts/wiki-eval.py --verify-gold   # assert every expected page exists on disk (exit 1 if not)
  python3 scripts/wiki-eval.py --baseline      # write scripts/wiki-eval-baseline.json from the current index
  python3 scripts/wiki-eval.py --check         # compare live eval to the baseline; exit 1 on regression
"""
import datetime
import json
import os
import shutil
import subprocess
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
WIKI = os.path.join(VAULT, "wiki")
GOLD = os.path.join(VAULT, "scripts", "wiki-eval-gold.json")
BASELINE = os.path.join(VAULT, "scripts", "wiki-eval-baseline.json")
TOPN = 5
# `qmd query`'s hybrid mode samples lex/vec/hyde query-expansion through a small LLM, so hit@3
# can flip a query or two between identical runs with no real regression (observed: 0-2 of 51
# gold queries flip run-to-run). Tolerate up to this many per-query flips before failing; the
# aggregate check is derived from this same budget so the two never disagree.
MAX_QUERY_FLIPS = 2

_WIKI_PREFIX = "qmd://wiki/"


def parse_results(stdout):
    """Ranked wiki-relative paths from `qmd ... --format json` stdout: each hit's "file" field
    is "qmd://wiki/<relpath>"; strip the collection prefix so results line up with the gold
    set's wiki-relative expected paths (e.g. techniques/web/ssrf.md)."""
    try:
        items = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return []
    out = []
    for it in items:
        f = it.get("file", "")
        if f.startswith(_WIKI_PREFIX):
            out.append(f[len(_WIKI_PREFIX):])
    return out


def _dedupe(paths):
    """Order-preserving dedupe so hit@k is page-level (semantic results repeat a file across
    chunks)."""
    seen, out = set(), []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _run_subprocess(query, mode, window):
    cmd = ["qmd", "search" if mode == "keyword" else "query", query,
           "-c", "wiki", "-n", str(window), "--format", "json"]
    if mode != "keyword":
        cmd.append("--no-rerank")  # hybrid RRF only; the LLM rerank pass is too slow for a 50-query gate
    env = dict(os.environ, QMD_VAULT=VAULT, HF_HUB_DISABLE_PROGRESS_BARS="1")
    try:
        out = subprocess.check_output(cmd, text=True, env=env,
                                      stderr=subprocess.DEVNULL, timeout=180)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return []
    return parse_results(out)


def run_query(query, mode, n=TOPN):
    """Ranked, page-level (deduped) wiki-relative paths for one query. Fetches a wider window
    than n so dedupe still yields n distinct pages."""
    window = max(n * 3, 12)
    return _dedupe(_run_subprocess(query, mode, window))


def hit_at(ranked, expected, k):
    return any(e in ranked[:k] for e in expected)


def reciprocal_rank(ranked, expected):
    for i, r in enumerate(ranked, 1):
        if r in expected:
            return 1.0 / i
    return 0.0


def load_gold():
    with open(GOLD, encoding="utf-8") as fh:
        return json.load(fh)["queries"]


def verify_gold(gold):
    """Return the list of expected paths that do not exist on disk."""
    missing = []
    for row in gold:
        for p in row["expected"]:
            if not os.path.isfile(os.path.join(WIKI, p)):
                missing.append(f'{p}  (query: "{row["query"]}")')
    return missing


def evaluate(gold, n=TOPN):
    per = []
    for row in gold:
        ranked = run_query(row["query"], row.get("mode", "semantic"), n)
        per.append({
            "query": row["query"],
            "expected": row["expected"],
            "hit@3": hit_at(ranked, row["expected"], 3),
            "hit@5": hit_at(ranked, row["expected"], 5),
            "rr": reciprocal_rank(ranked, row["expected"]),
            "top": ranked[:n],
        })
    q = len(per) or 1
    agg = {
        "hit@3": round(sum(p["hit@3"] for p in per) / q, 4),
        "hit@5": round(sum(p["hit@5"] for p in per) / q, 4),
        "mrr": round(sum(p["rr"] for p in per) / q, 4),
        "n_queries": len(per),
    }
    return {"aggregate": agg, "per_query": per}


def main():
    args = sys.argv[1:]

    gold = load_gold()

    if "--verify-gold" in args:
        missing = verify_gold(gold)
        if missing:
            print(f"wiki-eval: {len(missing)} gold expected-path(s) missing on disk:")
            for m in missing:
                print(f"  {m}")
            return 1
        print(f"wiki-eval: gold set OK ({len(gold)} queries, all expected pages exist).")
        return 0

    if not shutil.which("qmd"):
        print("wiki-eval: `qmd` not on PATH; cannot run retrieval eval. "
              "(--verify-gold works without qmd.)", file=sys.stderr)
        return 1

    res = evaluate(gold)

    if "--baseline" in args:
        base = {
            "_comment": "Baseline metrics for scripts/wiki-eval.py --check, captured from the "
                        "clean index. Regenerate with: python3 scripts/wiki-eval.py --baseline. "
                        "The pytest gate fails if a live eval drops aggregate hit@3 below "
                        "baseline (minus epsilon) or flips a per-query hit@3 from true to false.",
            "captured": datetime.date.today().isoformat(),
            "aggregate": res["aggregate"],
            "per_query_hit3": {p["query"]: p["hit@3"] for p in res["per_query"]},
        }
        with open(BASELINE, "w", encoding="utf-8") as fh:
            json.dump(base, fh, indent=2)
            fh.write("\n")
        print(f"wiki-eval: wrote {os.path.relpath(BASELINE, VAULT)} "
              f"(hit@3={res['aggregate']['hit@3']}, mrr={res['aggregate']['mrr']}, "
              f"n={res['aggregate']['n_queries']}).")
        return 0

    if "--check" in args:
        if not os.path.isfile(BASELINE):
            print("wiki-eval: no baseline; run `python3 scripts/wiki-eval.py --baseline` first.",
                  file=sys.stderr)
            return 1
        with open(BASELINE, encoding="utf-8") as fh:
            base = json.load(fh)
        n_q = base["aggregate"].get("n_queries") or len(base.get("per_query_hit3", {})) or 1
        epsilon = (MAX_QUERY_FLIPS + 0.5) / n_q  # matches the per-query flip budget below
        regressions = []
        if res["aggregate"]["hit@3"] < base["aggregate"]["hit@3"] - epsilon:
            regressions.append(f'aggregate hit@3 {res["aggregate"]["hit@3"]} < baseline '
                               f'{base["aggregate"]["hit@3"]} (beyond the {MAX_QUERY_FLIPS}-flip budget)')
        live = {p["query"]: p["hit@3"] for p in res["per_query"]}
        flips = [query for query, was in base.get("per_query_hit3", {}).items()
                 if was and not live.get(query, False)]
        if len(flips) > MAX_QUERY_FLIPS:
            regressions.append(f'{len(flips)} per-query flips to miss exceeds the '
                               f'{MAX_QUERY_FLIPS}-flip noise budget: ' +
                               ", ".join(f'"{q}"' for q in flips))
        if regressions:
            print(f"wiki-eval CHECK FAIL: {len(regressions)} regression(s):")
            for r in regressions:
                print(f"  {r}")
            return 1
        note = f" ({len(flips)} flip(s) within the {MAX_QUERY_FLIPS}-query noise budget)" if flips else ""
        print(f"wiki-eval CHECK OK: hit@3={res['aggregate']['hit@3']} "
              f">= baseline {base['aggregate']['hit@3']}{note}.")
        return 0

    if "--json" in args:
        print(json.dumps(res, indent=2))
        return 0

    agg = res["aggregate"]
    print(f"Wiki retrieval eval  ({agg['n_queries']} queries)")
    print(f"  hit@3 = {agg['hit@3']}   hit@5 = {agg['hit@5']}   MRR = {agg['mrr']}")
    print("-" * 70)
    for p in res["per_query"]:
        mark = "ok " if p["hit@3"] else "MISS"
        print(f"  [{mark}] rr={p['rr']:.2f}  {p['query']}")
        if not p["hit@3"]:
            print(f"         expected {p['expected']}")
            print(f"         got      {p['top']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
