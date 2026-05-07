#!/usr/bin/env python3
"""
PII Benchmark Runner
Usage:
  python3 benchmark/benchmark_runner.py                          # run all tests
  python3 benchmark/benchmark_runner.py --filter user_type=program_director
  python3 benchmark/benchmark_runner.py --filter entry_point=language_quality
  python3 benchmark/benchmark_runner.py --filter id=PD-001,BX-004
  python3 benchmark/benchmark_runner.py --skip-semantic          # structural checks only
  python3 benchmark/benchmark_runner.py --dry-run                # list tests, no requests
  python3 benchmark/benchmark_runner.py --compare results/run_A.json results/run_B.json
  python3 benchmark/benchmark_runner.py --url http://localhost:8001
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
import yaml

# Load .env from project root (same logic as main.py)
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            _key, _val = _k.strip(), _v.strip()
            if _val and not os.environ.get(_key):
                os.environ[_key] = _val

sys.path.insert(0, str(Path(__file__).parent))
from evaluator import evaluate_semantic, evaluate_structural

# ---------------------------------------------------------------------------
BASE_URL = "http://localhost:8000"
BENCHMARKS_FILE = Path(__file__).parent / "benchmarks.yaml"
RESULTS_DIR = Path(__file__).parent / "results"
SUMMARY_FILE = RESULTS_DIR / "summary.json"

PASS_THRESHOLD = 80.0
PARTIAL_THRESHOLD = 50.0

ANSI = {
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}


def c(color: str, text: str) -> str:
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def print_progress(current: int, total: int, label: str) -> None:
    bar_width = 28
    filled = int(bar_width * (current - 1) / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    pct = int(100 * (current - 1) / total)
    print(f"\n[{bar}] {current}/{total} ({pct}%) — {c('cyan', label)}", flush=True)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def check_health(base_url: str) -> bool:
    try:
        r = httpx.get(f"{base_url}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def send_chat(base_url: str, message: str, history: list, programs: list) -> str:
    """POST to /chat and collect the full streamed response."""
    payload = {"message": message, "history": history, "programs": programs}
    chunks = []
    with httpx.stream(
        "POST",
        f"{base_url}/chat",
        json=payload,
        timeout=120,
    ) as r:
        r.raise_for_status()
        for chunk in r.iter_text():
            chunks.append(chunk)
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------

def run_test(test: dict, base_url: str, skip_semantic: bool) -> dict:
    """Execute one test and return a result dict."""
    programs = test.get("programs", [])
    history = [{"role": m["role"], "content": m["content"]} for m in test.get("history", [])]

    if test.get("multi_turn"):
        turns = test["turns"]
        response = ""
        for i, turn_msg in enumerate(turns):
            response = send_chat(base_url, turn_msg, history, programs)
            if i < len(turns) - 1:
                history.append({"role": "user", "content": turn_msg})
                history.append({"role": "assistant", "content": response})
        query_for_eval = turns[-1]
    else:
        query_for_eval = test["message"]
        response = send_chat(base_url, query_for_eval, history, programs)

    criteria_results = []
    total_weight = 0.0
    weighted_score = 0.0

    for criterion in test.get("criteria", []):
        weight = float(criterion.get("weight", 1.0))
        ctype = criterion["type"]
        desc = criterion["description"]

        if ctype == "structural":
            score, reason = evaluate_structural(response, criterion)
        elif ctype == "semantic":
            if skip_semantic:
                criteria_results.append({
                    "type": ctype,
                    "description": desc,
                    "weight": weight,
                    "score": None,
                    "reason": "skipped",
                })
                continue
            score, reason = evaluate_semantic(query_for_eval, response, criterion)
        else:
            score, reason = 0.0, f"Unknown criterion type: {ctype}"

        criteria_results.append({
            "type": ctype,
            "description": desc,
            "weight": weight,
            "score": score,
            "reason": reason,
        })
        weighted_score += score * weight
        total_weight += weight

    if total_weight > 0:
        test_score = (weighted_score / total_weight) * 100
    else:
        test_score = 0.0

    if test_score >= PASS_THRESHOLD:
        status = "pass"
    elif test_score >= PARTIAL_THRESHOLD:
        status = "partial"
    else:
        status = "fail"

    return {
        "id": test["id"],
        "name": test["name"],
        "user_type": test.get("user_type", ""),
        "entry_point": test.get("entry_point", ""),
        "programs": programs,
        "score": round(test_score, 1),
        "status": status,
        "response_preview": response[:400],
        "response_full": response,
        "criteria_results": criteria_results,
    }


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def compute_category_scores(results: list) -> dict:
    by_user = {}
    by_entry = {}
    for r in results:
        ut = r["user_type"]
        ep = r["entry_point"]
        by_user.setdefault(ut, []).append(r["score"])
        by_entry.setdefault(ep, []).append(r["score"])

    return {
        "by_user_type": {k: round(sum(v) / len(v), 1) for k, v in by_user.items()},
        "by_entry_point": {k: round(sum(v) / len(v), 1) for k, v in by_entry.items()},
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_test_result(result: dict, verbose: bool = False) -> None:
    status = result["status"]
    score = result["score"]
    color = "green" if status == "pass" else ("yellow" if status == "partial" else "red")
    icon = "✓" if status == "pass" else ("~" if status == "partial" else "✗")

    print(f"\n[{result['id']}] {result['name']}")
    print(f"  Programs: {', '.join(result['programs']) or '(all)'}")

    for cr in result["criteria_results"]:
        if cr["score"] is None:
            marker = c("cyan", "  –")
        elif cr["score"] >= 1.0:
            marker = c("green", "  ✓")
        elif cr["score"] >= 0.5:
            marker = c("yellow", "  ~")
        else:
            marker = c("red", "  ✗")
        label = cr["type"].upper()
        print(f"{marker} {label}: {cr['description']} ({cr['score']}) — {cr['reason']}")

    print(f"  Score: {c(color, f'{score:.1f}')} {c(color, icon)} {status.upper()}")

    if verbose and status != "pass":
        print(f"\n  Response preview:\n  {result['response_preview'][:300]}\n")


def print_summary(run: dict, previous: dict | None = None) -> None:
    score = run["overall_score"]
    prev_score = previous["overall_score"] if previous else None
    delta = f"  (prev: {prev_score:.1f}, {'+' if score >= prev_score else ''}{score - prev_score:.1f})" if prev_score is not None else ""

    print("\n" + "━" * 55)
    print(f"  RESULTS — {run['run_id']}")
    print("━" * 55)
    score_str = f"{score:.1f}/100"
    print(f"  Overall Score: {c('bold', score_str)}{delta}")
    print(f"  Tests: {run['tests_passed']} pass  {run['tests_partial']} partial  {run['tests_failed']} fail  ({run['tests_run']} total)")

    cats = run["category_scores"]
    print("\n  By User Type:")
    for k, v in sorted(cats["by_user_type"].items()):
        bar = "█" * int(v / 10)
        print(f"    {k:<26} {v:5.1f}  {bar}")

    print("\n  By Entry Point:")
    for k, v in sorted(cats["by_entry_point"].items()):
        bar = "█" * int(v / 10)
        print(f"    {k:<26} {v:5.1f}  {bar}")

    failed = [r for r in run["results"] if r["status"] != "pass"]
    if failed:
        print(f"\n  Non-passing tests ({len(failed)}):")
        for r in failed:
            color = "yellow" if r["status"] == "partial" else "red"
            print(f"    {c(color, r['id'])} ({r['score']:.1f}) — {r['name']}")
            for cr in r["criteria_results"]:
                if cr["score"] is not None and cr["score"] < 1.0:
                    print(f"      ✗ {cr['type']}: {cr['description']} — {cr['reason']}")

    print(f"\n  Saved: {run['result_file']}")
    print("━" * 55)


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------

def save_run(run: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{run['run_id']}.json"
    run["result_file"] = str(path)
    path.write_text(json.dumps(run, indent=2))

    # Update summary index
    summary = []
    if SUMMARY_FILE.exists():
        summary = json.loads(SUMMARY_FILE.read_text())
    summary.append({
        "run_id": run["run_id"],
        "timestamp": run["timestamp"],
        "overall_score": run["overall_score"],
        "tests_run": run["tests_run"],
        "tests_passed": run["tests_passed"],
        "file": str(path),
    })
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2))
    return path


def load_run(path: str) -> dict:
    return json.loads(Path(path).read_text())


def load_latest_run(exclude_id: str | None = None) -> dict | None:
    if not SUMMARY_FILE.exists():
        return None
    summary = json.loads(SUMMARY_FILE.read_text())
    for entry in reversed(summary):
        if entry["run_id"] != exclude_id:
            p = Path(entry["file"])
            if p.exists():
                return json.loads(p.read_text())
    return None


# ---------------------------------------------------------------------------
# Compare command
# ---------------------------------------------------------------------------

def compare_runs(path_a: str, path_b: str) -> None:
    a = load_run(path_a)
    b = load_run(path_b)

    print(f"\nComparing runs:")
    print(f"  A: {a['run_id']}  score={a['overall_score']:.1f}")
    print(f"  B: {b['run_id']}  score={b['overall_score']:.1f}")
    delta = b["overall_score"] - a["overall_score"]
    sign = "+" if delta >= 0 else ""
    print(f"  Delta: {sign}{delta:.1f}\n")

    by_id_a = {r["id"]: r for r in a["results"]}
    by_id_b = {r["id"]: r for r in b["results"]}

    all_ids = sorted(set(by_id_a) | set(by_id_b))
    improved, regressed, unchanged = [], [], []

    for tid in all_ids:
        ra = by_id_a.get(tid)
        rb = by_id_b.get(tid)
        if ra is None or rb is None:
            continue
        d = rb["score"] - ra["score"]
        if d > 1:
            improved.append((tid, ra["score"], rb["score"], d, rb["name"]))
        elif d < -1:
            regressed.append((tid, ra["score"], rb["score"], d, rb["name"]))
        else:
            unchanged.append((tid, ra["score"], rb["score"], rb["name"]))

    if improved:
        print(c("green", f"  Improved ({len(improved)}):"))
        for tid, sa, sb, d, name in improved:
            print(f"    {tid:8s} {sa:5.1f} → {sb:5.1f}  (+{d:.1f})  {name}")

    if regressed:
        print(c("red", f"\n  Regressed ({len(regressed)}):"))
        for tid, sa, sb, d, name in regressed:
            print(f"    {tid:8s} {sa:5.1f} → {sb:5.1f}  ({d:.1f})  {name}")

    if unchanged:
        print(f"\n  Unchanged ({len(unchanged)}): {' '.join(t[0] for t in unchanged)}")


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def apply_filter(tests: list, filter_str: str | None) -> list:
    if not filter_str:
        return tests
    key, _, value = filter_str.partition("=")
    key = key.strip()
    values = {v.strip() for v in value.split(",")}

    if key == "id":
        return [t for t in tests if t["id"] in values]
    elif key == "user_type":
        return [t for t in tests if t.get("user_type") in values]
    elif key == "entry_point":
        return [t for t in tests if t.get("entry_point") in values]
    else:
        print(f"Unknown filter key: {key}. Use id, user_type, or entry_point.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Analysis pass
# ---------------------------------------------------------------------------

ARCHITECTURE_CONTEXT = """
## PII Architecture Summary (for diagnostic use)

### Retrieval layers (build_context in main.py)
- Tier 1 (always): PLOs scoped to active program(s), CLOs for program courses, course title list
- Tier 2 (broad queries, no course mentioned): all item titles + metadata, no body text
- Tier 3 (detail queries): full body text for course-specific; keyword-scored snippets for broad
- Inferential path: fires when INFERENTIAL_QUERY_RE matches ("which assignments would assess",
  "suited to assess", "best assess", etc.) or QUOTED_FRAGMENT_RE + competency language;
  fetches ALL item body text (500-char truncated) for semantic comparison
- Competency path: fires when COMPETENCY_CODE_RE or COMPETENCY_QUERY_RE matches;
  loads competency catalog + assignment links; broad competency queries skip Tier 2/3
  and use fetch_plo_clo_summary() instead of full alignment chain
- PLO alignment chain: fires when PLO numbers mentioned; full PLO→CLO→Item traversal

### Back-reference anchoring
When query contains "this", "that", or "it": scans last 4 assistant messages for bold
markdown item titles, fetches them as "Pinned Items". If no codes in current message,
also scans history for competency codes (cap 10).

### Key behavioral rules in SYSTEM_PROMPT_BASE
1. Exploratory vs definitive framing: PM/LD competencies have formal links → definitive;
   Leadership-HRM SHRM has no item links → always exploratory (pending director decision)
2. Forbidden language: never "weakness/weaknesses/weak" → substitute "area for improvement",
   "limited coverage", or "underdeveloped"; do NOT comment on user's word choice
3. Language analysis preamble: required in italics when user explicitly requests language
   quality or alignment analysis; does NOT fire for factual retrieval questions
4. CLO/PLO quality framing: use "needs" not "lacks"
5. Options format: ANY user-facing choice uses `> **Option N:** [phrase]` blockquote format;
   phrase must read as a natural standalone user message; never bullet points
6. Co-orientation (low confidence): formula is "I can approach this as [X] or as [Y] —
   which is closer to what you need right now?"; prohibited phrases: "your question is
   unclear", "could you be more specific", "that's a broad question"
7. SHRM not a gap: Leadership-HRM SHRM mapping is pending director decision, not missing
   integration; response must use exploratory/pending framing, not "gap"
8. Pages never assessed: Pages may contain assignment descriptions but are not directly
   assessed — always cite the Assignment as the assessable artifact

### Key functions in main.py
- build_context() — orchestrates all retrieval and routing
- COMPETENCY_CODE_RE, COMPETENCY_QUERY_RE — competency detection patterns
- INFERENTIAL_QUERY_RE — semantic matching trigger
- QUOTED_FRAGMENT_RE — quoted text + competency language trigger
- SYSTEM_PROMPT_BASE — all behavioral rules encoded here
- build_program_scope_block() — injects program-specific framing + competency assumption
- fetch_plo_alignment_chain() — full PLO→CLO→Item traversal
- fetch_plo_clo_summary() — compact PLO→CLO bridge for broad competency queries
- fetch_inferential_items() — all items with truncated body for semantic matching
- get_course_role_lookup() — program-aware required/elective labels
"""

ANALYSIS_PROMPT_TEMPLATE = """You are a diagnostic engineer reviewing benchmark test failures for the Program Intelligence Interface (PII), a RAG-based AI system.

{architecture}

## Failed / Partial Tests to Diagnose

{failures}

---

For each test above, produce a structured diagnosis. Use this exact format for each (substitute the actual test ID, name, score, and status):

### [ID] Name
**Score:** N/100  **Status:** fail|partial

**What failed:**
One sentence describing which criterion failed and what the response actually did wrong.

**Root cause layer:**
Choose exactly one: `RETRIEVAL` | `PROMPT` | `MODEL` | `TEST`
- RETRIEVAL: the right data was not in the context Claude received (wrong tier fired, detection regex missed, scope filter excluded the right content)
- PROMPT: data was available but a behavioral rule in SYSTEM_PROMPT_BASE was not followed
- MODEL: the rule is present and data is available but Claude applied it inconsistently (may need stronger instruction wording)
- TEST: the criterion is overly strict, the rubric is ambiguous, or the expected behavior was wrong

**Where to look:**
Name the specific function, regex pattern, or SYSTEM_PROMPT_BASE section to investigate.

**Recommended fix:**
One to three sentences. Be specific: what to change and where.

**Priority:**
`BLOCKING` (core functionality broken), `NOTABLE` (wrong behavior, not broken), or `MONITOR` (minor or possibly a test issue)

---

After all individual diagnoses, add a final section:

## Prioritized Action List

List all BLOCKING items first, then NOTABLE, then MONITOR. For each, one line:
`[ID] fix description — location in main.py`
"""


def run_analysis_pass(run: dict, skip_semantic: bool) -> str:
    """Analyze all non-passing results and return a markdown diagnosis report."""
    from anthropic import Anthropic

    non_passing = [r for r in run["results"] if r["status"] not in ("pass",)]
    if not non_passing:
        return "## Analysis\n\nAll tests passed. No failures to diagnose.\n"

    # Build failure blocks
    failure_blocks = []
    for r in non_passing:
        failing_criteria = [
            cr for cr in r["criteria_results"]
            if cr.get("score") is not None and cr["score"] < 1.0
        ]
        skipped = [cr for cr in r["criteria_results"] if cr.get("score") is None]

        criteria_text = "\n".join(
            f"  - [{cr['type'].upper()}] {cr['description']}: score={cr['score']} — {cr['reason']}"
            for cr in failing_criteria
        )
        skipped_note = f"\n  ({len(skipped)} semantic criteria were skipped)" if skipped else ""

        block = (
            f"**[{r['id']}] {r['name']}**\n"
            f"Score: {r['score']}/100  Status: {r['status']}\n"
            f"Programs: {', '.join(r['programs']) or '(all)'}\n"
            f"Query: {r.get('response_preview', '')[:50]}...\n"
            f"Failing criteria:\n{criteria_text}{skipped_note}\n\n"
            f"Full response (first 800 chars):\n{r['response_full'][:800]}\n"
        )
        failure_blocks.append(block)

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        architecture=ARCHITECTURE_CONTEXT,
        failures="\n---\n".join(failure_blocks),
    )

    client = Anthropic()
    note = " (some semantic criteria were skipped — diagnosis may be incomplete)" if skip_semantic else ""
    header = (
        f"# PII Benchmark Analysis — {run['run_id']}\n"
        f"Overall score: {run['overall_score']}/100  "
        f"Non-passing: {len(non_passing)}/{run['tests_run']}{note}\n\n"
    )

    result = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return header + result.content[0].text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="PII Benchmark Runner")
    parser.add_argument("--url", default=BASE_URL, help="Base URL of PII server")
    parser.add_argument("--filter", help="Filter tests: user_type=X, entry_point=Y, or id=A,B,C")
    parser.add_argument("--skip-semantic", action="store_true", help="Skip semantic (LLM-judge) criteria")
    parser.add_argument("--dry-run", action="store_true", help="List tests without running them")
    parser.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"), help="Compare two result files")
    parser.add_argument("--verbose", action="store_true", help="Show response preview for failing tests")
    parser.add_argument("--skip-analysis", action="store_true", help="Skip the post-run diagnostic analysis pass")
    args = parser.parse_args()

    if args.compare:
        compare_runs(args.compare[0], args.compare[1])
        return

    # Load benchmarks
    benchmarks = yaml.safe_load(BENCHMARKS_FILE.read_text())
    tests = benchmarks["tests"]
    tests = apply_filter(tests, args.filter)

    if args.dry_run:
        print(f"\n{len(tests)} tests would run:\n")
        for t in tests:
            print(f"  [{t['id']}] {t.get('user_type', '')} / {t.get('entry_point', '')} — {t['name']}")
            print(f"    programs: {t.get('programs', [])}  multi_turn: {t.get('multi_turn', False)}")
        return

    # Health check
    if not check_health(args.url):
        print(c("red", f"Server not reachable at {args.url}. Start it with:"))
        print("  python3 -m uvicorn main:app --port 8000")
        sys.exit(1)

    print(c("bold", f"\nRunning {len(tests)} benchmarks against {args.url}...\n"))
    if args.skip_semantic:
        print(c("yellow", "  (semantic checks skipped)\n"))

    run_id = "run_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    for i, test in enumerate(tests, 1):
        print_progress(i, len(tests), f"{test['id']} — {test['name']}")
        try:
            result = run_test(test, args.url, args.skip_semantic)
            results.append(result)
            print_test_result(result, verbose=args.verbose)
        except Exception as e:
            print(c("red", f"\n  ERROR: {e}"))
            results.append({
                "id": test["id"],
                "name": test["name"],
                "user_type": test.get("user_type", ""),
                "entry_point": test.get("entry_point", ""),
                "programs": test.get("programs", []),
                "score": 0.0,
                "status": "error",
                "response_preview": str(e),
                "response_full": str(e),
                "criteria_results": [],
            })

    n = len(tests)
    print(f"\n[{'█' * 28}] {n}/{n} (100%) — complete\n")

    # Aggregate
    valid = [r for r in results if r["status"] != "error"]
    overall = round(sum(r["score"] for r in valid) / len(valid), 1) if valid else 0.0

    run = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "overall_score": overall,
        "tests_run": len(results),
        "tests_passed": sum(1 for r in results if r["status"] == "pass"),
        "tests_partial": sum(1 for r in results if r["status"] == "partial"),
        "tests_failed": sum(1 for r in results if r["status"] in ("fail", "error")),
        "category_scores": compute_category_scores(valid),
        "results": results,
        "result_file": "",
    }

    save_run(run)
    previous = load_latest_run(exclude_id=run_id)
    print_summary(run, previous)

    if not args.skip_analysis:
        print(c("cyan", "\nRunning analysis pass on non-passing tests..."))
        analysis = run_analysis_pass(run, args.skip_semantic)
        analysis_path = RESULTS_DIR / f"{run_id}_analysis.md"
        analysis_path.write_text(analysis)
        print(analysis)
        print(c("bold", f"\nAnalysis saved: {analysis_path}"))


if __name__ == "__main__":
    main()
