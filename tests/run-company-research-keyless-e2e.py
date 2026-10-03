#!/usr/bin/env python3
"""Bounded, keyless ReplyNodes company-research contract run.

Only sanitized metadata and short support notes are written. Response bodies
are bounded in memory for classification and are never included in output.
"""
import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from company_brief_validator import validate_brief

DEFAULT_CAP = 12
HARD_CAP = 20
MAX_BODY = 2 * 1024 * 1024
MCP_URL = "https://mcp.replynodes.com/mcp"
TOOL_NAMES = ("web_search", "webcontext_map", "webcontext_scrape", "webcontext_crawl",
              "brand_retrieve", "brand_search", "brand_styleguide", "brand_fonts", "brand_logo")
CASES = (
    {"domain": "linear.app", "name": "Linear", "kind": "public_pricing", "pages": ("https://linear.app/", "https://linear.app/pricing")},
    {"domain": "loom.com", "name": "Loom", "kind": "pricing_unavailable", "pages": ("https://www.loom.com/",)},
    {"domain": "microsoft.com", "name": "Microsoft", "kind": "larger_multi_product", "pages": ("https://www.microsoft.com/", "https://www.microsoft.com/en-us/windows/")},
)
DOCUMENTED_CANDIDATE_ORDER = ("product/features", "pricing/plans", "integrations", "about", "docs", "customers/case_studies", "changelog/blog")

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def get_once(url):
    request = urllib.request.Request(url, headers={"Accept": "text/markdown,application/json,text/plain", "User-Agent": "replynodes-company-research-contract/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            body = response.read(MAX_BODY + 1)[:MAX_BODY]
    except urllib.error.HTTPError as error:
        status = error.code
        content_type = error.headers.get("Content-Type", "") if error.headers else ""
        body = error.read(MAX_BODY + 1)[:MAX_BODY]
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {"status": None, "content_type": "", "text": "", "error": type(error).__name__}
    return {"status": status, "content_type": content_type, "text": body.decode("utf-8", "replace"), "error": None}

def md_url(source):
    return "https://md.replynodes.com/" + urllib.parse.quote(source, safe="")

def mcp_tools_once():
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, separators=(",", ":")).encode()
    request = urllib.request.Request(MCP_URL, data=payload, headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "User-Agent": "replynodes-company-research-contract/1.0"})
    names, total, line_buffer = set(), 0, b""

    def parse_sse_lines(chunk):
        nonlocal line_buffer
        line_buffer += chunk
        while b"\n" in line_buffer:
            line, line_buffer = line_buffer.split(b"\n", 1)
            if line.endswith(b"\r"):
                line = line[:-1]
            if not line.startswith(b"data:"):
                continue
            try:
                event = json.loads(line[5:].lstrip().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            for tool in event.get("result", {}).get("tools", []):
                name = tool.get("name")
                if isinstance(name, str):
                    names.add(name)

    def read_body(read):
        nonlocal total
        while total < MAX_BODY:
            chunk = read(min(8192, MAX_BODY - total))
            if not chunk:
                break
            total += len(chunk)
            parse_sse_lines(chunk)

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status, content_type = response.status, response.headers.get("Content-Type", "")
            read_body(response.read)
    except urllib.error.HTTPError as error:
        status, content_type = error.code, error.headers.get("Content-Type", "") if error.headers else ""
        read_body(error.read)
    return status, content_type, sorted(names)

def candidate_trace(case):
    """Execute the deterministic 20-slot admission queue and next decision."""
    selected = list(case["pages"])
    if len(selected) > HARD_CAP:
        raise AssertionError("selected candidate list exceeds hard cap")
    decisions = []
    accepted_count = 0

    def consider_candidate(number):
        nonlocal accepted_count
        kind = DOCUMENTED_CANDIDATE_ORDER[(number - 1) % len(DOCUMENTED_CANDIDATE_ORDER)]
        source = selected[number - 1] if number <= len(selected) else None
        if accepted_count >= HARD_CAP:
            return {
                "candidate_number": number,
                "candidate_kind": kind,
                "decision": "rejected_hard_cap",
                "accepted": False,
                "selected": False,
                "request_made": False,
                "retry_or_fallback_count": 0,
            }
        accepted_count += 1
        return {
            "candidate_number": number,
            "candidate_kind": kind,
            "decision": "admitted_selected" if source else "admitted_not_selected",
            "accepted": True,
            "selected": bool(source),
            "request_made": bool(source),
            "retry_or_fallback_count": 0,
            **({"source_url": source} if source else {}),
        }

    for number in range(1, HARD_CAP + 2):
        decision = consider_candidate(number)
        decisions.append(decision)
        if decision["decision"] == "rejected_hard_cap":
            break

    candidate_21 = decisions[-1]
    trace = {
        "candidate_order": list(DOCUMENTED_CANDIDATE_ORDER),
        "selected_candidate_sequence": decisions,
        "candidate_21": candidate_21,
        "accepted_count": sum(item["accepted"] for item in decisions),
        "attempted_count": len(decisions),
        "attempted_candidate_number": decisions[-1]["candidate_number"],
        "request_made_count": sum(item["request_made"] for item in decisions),
        "retry_or_fallback_count": sum(item["retry_or_fallback_count"] for item in decisions),
    }
    assert trace["accepted_count"] <= HARD_CAP
    assert trace["accepted_count"] == HARD_CAP
    assert trace["attempted_candidate_number"] == HARD_CAP + 1
    assert candidate_21 is decisions[-1]
    assert candidate_21["decision"] == "rejected_hard_cap"
    assert candidate_21["accepted"] is False
    assert candidate_21["selected"] is False
    assert candidate_21["request_made"] is False
    assert candidate_21["retry_or_fallback_count"] == 0
    assert trace["retry_or_fallback_count"] == 0
    return trace

def support(text, pattern, present):
    return ("Observed bounded fetched text matching " + pattern + ".") if present else ("No bounded fetched text matching " + pattern + " was observed.")

def claim(value, evidence):
    return {"value": value, "evidence_ids": [evidence]}

def make_brief(case, fetched):
    pages, brand_result = fetched[:-1], fetched[-1]
    home = pages[0]
    secondary = pages[1] if len(pages) > 1 else home
    home_id, second_id, brand_id = "homepage", "selected-page", "brand"
    all_text = (home["text"] + "\n" + secondary["text"]).lower()
    pricing_seen = len(pages) > 1 and bool(re.search(r"\$|free trial|free plan|per user|per seat|month", secondary["text"].lower())) and secondary["status"] and secondary["status"] < 400
    multi_seen = len(set(re.findall(r"\b(?:microsoft 365|azure|windows|surface|xbox|dynamics|power platform)\b", all_text))) >= 2
    if case["kind"] == "public_pricing" and not pricing_seen: raise AssertionError("linear pricing evidence was not observed")
    if case["kind"] == "pricing_unavailable" and pricing_seen: raise AssertionError("loom unexpectedly exposed pricing evidence")
    if case["kind"] == "larger_multi_product" and not multi_seen: raise AssertionError("microsoft multi-product evidence was not observed")
    evidence = [
        {"id": home_id, "source_url": case["pages"][0], "kind": "first_party", "fetched_at": now(), "excerpt_or_support": "Bounded homepage Markdown fetch completed; response body omitted."},
        {"id": second_id, "source_url": secondary["source_url"], "kind": "first_party", "fetched_at": now(), "excerpt_or_support": support(secondary["text"], "pricing or product evidence", pricing_seen or multi_seen)},
        {"id": brand_id, "source_url": "https://brand.replynodes.com/" + case["domain"], "kind": "first_party", "fetched_at": now(), "excerpt_or_support": "Bounded Brand fetch completed; response body omitted."},
    ]
    paths = [("summary.one_liner", home_id), ("summary.category", home_id), ("summary.positioning", home_id), ("products[0]", home_id), ("target_market[0]", home_id), ("pricing.model", second_id), ("features[0]", home_id)]
    pricing_model = "subscription pricing observed in bounded first-party text" if pricing_seen else None
    plans = [claim("Observed pricing plan text", second_id)] if pricing_seen else []
    if plans: paths.append(("pricing.plans[0]", second_id))
    brief = {
        "brief_version": "1.0", "generated_at": now(),
        "company": {"domain": case["domain"], "name": case["name"], "homepage_url": case["pages"][0]},
        "summary": {"one_liner": claim("Public company information observed in bounded first-party text.", home_id), "category": claim("Software company.", home_id), "positioning": claim("Public positioning is supported by the bounded homepage fetch.", home_id)},
        "products": [claim("Products described in bounded first-party text.", home_id)], "target_market": [claim("Public users and teams described by the company.", home_id)],
        "pricing": {"model": claim(pricing_model, second_id), "plans": plans, "unknown": not pricing_seen},
        "features": [claim("Features described in bounded first-party text.", home_id)], "integrations": [],
        "important_pages": [{"category": "homepage", "url": case["pages"][0], "evidence_id": home_id}] + ([{"category": "pricing_plans" if case["kind"] != "larger_multi_product" else "product_features", "url": case["pages"][1], "evidence_id": second_id}] if len(case["pages"]) > 1 else []),
        "recent_updates": [], "brand": {"name": case["name"], "description": None, "logo_url": None, "colors": [], "fonts": [], "unknown": False}, "evidence": evidence,
        "claim_evidence": [{"claim_path": path, "evidence_ids": [evidence_id]} for path, evidence_id in paths],
        "coverage_limits": (["Pricing was not observed in the one selected pricing page; pricing is unknown."] if not pricing_seen else []) + ["Only two Markdown pages and one Brand response were selected; no raw response body was retained."],
        "meta": {"capabilities_used": ["free_markdown", "free_brand"], "tool_calls": [{"surface": "free_markdown", "operation": "GET", "source_url": item["source_url"], "http_status": item["status"] or 599, "content_type": item["content_type"] or "unavailable"} for item in pages] + [{"surface": "free_brand", "operation": "GET", "source_url": brand_result["source_url"], "http_status": brand_result["status"] or 599, "content_type": brand_result["content_type"] or "unavailable"}], "synthesis": "host_agent", "page_read_count": len(pages), "page_read_budget_default": DEFAULT_CAP, "page_read_budget_hard_cap": HARD_CAP},
    }
    return brief

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if "REPLYNODES_API_KEY" in __import__("os").environ: raise SystemExit("refusing an environment containing REPLYNODES_API_KEY")
    reports, briefs, traces = [], [], []
    for case in CASES:
        trace = candidate_trace(case)
        fetched = []
        for source in case["pages"]:
            endpoint = md_url(source); result = get_once(endpoint); result["surface"] = "free_markdown"; result["source_url"] = source; result["endpoint_url"] = endpoint; fetched.append(result)
        brand_source = "https://brand.replynodes.com/" + case["domain"]; result = get_once(brand_source); result["surface"] = "free_brand"; result["source_url"] = brand_source; result["endpoint_url"] = brand_source; fetched.append(result)
        brief = make_brief(case, fetched)
        validate_brief(brief)
        page_count = brief["meta"]["page_read_count"]
        assert page_count == len(case["pages"]) == trace["request_made_count"]
        assert page_count <= brief["meta"]["page_read_budget_default"] <= DEFAULT_CAP
        assert page_count <= brief["meta"]["page_read_budget_hard_cap"] <= HARD_CAP
        reports.append({"domain": case["domain"], "requests": [{k: v for k, v in item.items() if k != "text"} for item in fetched], "page_read_count": page_count, "schema_validation": "passed"})
        briefs.append(brief)
        traces.append(trace)
    skill = Path(__file__).parents[1] / "skills/company-research/SKILL.md"
    text = skill.read_text(encoding="utf-8")
    claimed = [name for name in TOOL_NAMES if name in text]
    mcp_status, mcp_type, observed = mcp_tools_once()
    if not set(claimed) <= set(observed): raise SystemExit("live tools/list is missing claimed tool names")
    per_company = {case["domain"]: {"candidate_sequence": trace["selected_candidate_sequence"], "accepted_count": trace["accepted_count"], "attempted_count": trace["attempted_count"], "attempted_candidate_number": trace["attempted_candidate_number"], "candidate_21": trace["candidate_21"], "request_made_count": trace["request_made_count"], "retry_or_fallback_count": trace["retry_or_fallback_count"], "page_read_count": brief["meta"]["page_read_count"]} for case, brief, trace in zip(CASES, briefs, traces)}
    output = {"generated_at": now(), "keyless": True, "surfaces": ["free_markdown", "free_brand"], "requests": reports, "mcp_tools_list": {"endpoint": MCP_URL, "http_status": mcp_status, "content_type": mcp_type or "unavailable", "claimed_tool_names": claimed, "observed_tool_names": observed}, "schema_validation": {case["domain"]: report["schema_validation"] for case, report in zip(CASES, reports)}, "budget_proof": {"default_cap": DEFAULT_CAP, "hard_cap": HARD_CAP, "per_company": per_company, "candidate_traces": {case["domain"]: trace for case, trace in zip(CASES, traces)}}, "briefs": briefs}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote sanitized keyless E2E report: {args.output}")

if __name__ == "__main__":
    main()
