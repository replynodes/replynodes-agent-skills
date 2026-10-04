#!/usr/bin/env python3
"""Bounded, keyless ReplyNodes company-research contract run."""
import argparse
import datetime as dt
import html
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
TOOL_NAMES = ("web_search", "webcontext_map", "webcontext_scrape", "webcontext_crawl", "brand_retrieve", "brand_search", "brand_styleguide", "brand_fonts", "brand_logo")
CASES = (
    {"domain": "linear.app", "name": "Linear", "homepage": "https://linear.app/"},
    {"domain": "loom.com", "name": "Loom", "homepage": "https://www.loom.com/"},
    {"domain": "microsoft.com", "name": "Microsoft", "homepage": "https://www.microsoft.com/"},
)

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def get_once(url):
    request = urllib.request.Request(url, headers={"Accept": "text/markdown,application/json,text/plain", "User-Agent": "replynodes-company-research-contract/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status, content_type = response.status, response.headers.get("Content-Type", "")
            body = response.read(MAX_BODY + 1)[:MAX_BODY]
    except urllib.error.HTTPError as error:
        status, content_type = error.code, error.headers.get("Content-Type", "") if error.headers else ""
        body = error.read(MAX_BODY + 1)[:MAX_BODY]
        return {"status": status, "content_type": content_type, "text": body.decode("utf-8", "replace"), "error": type(error).__name__}
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {"status": None, "content_type": "", "text": "", "error": type(error).__name__}
    return {"status": status, "content_type": content_type, "text": body.decode("utf-8", "replace"), "error": None}

def successful(result):
    return isinstance(result.get("status"), int) and 200 <= result["status"] < 300 and bool(result.get("text", "").strip())

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
            if line.endswith(b"\r"): line = line[:-1]
            if not line.startswith(b"data:"): continue
            try: event = json.loads(line[5:].lstrip().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError): continue
            for tool in event.get("result", {}).get("tools", []):
                if isinstance(tool.get("name"), str): names.add(tool["name"])
    def read_body(read):
        nonlocal total
        while total < MAX_BODY:
            chunk = read(min(8192, MAX_BODY - total))
            if not chunk: break
            total += len(chunk); parse_sse_lines(chunk)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status, content_type = response.status, response.headers.get("Content-Type", ""); read_body(response.read)
    except urllib.error.HTTPError as error:
        status, content_type = error.code, error.headers.get("Content-Type", "") if error.headers else ""; read_body(error.read)
    return status, content_type, sorted(names)

def page_category(url):
    path = urllib.parse.urlparse(url).path.lower().strip("/")
    for pattern, category in ((r"(^|[/_-])(pricing|plans?)([/_-]|$)", "pricing_plans"), (r"(^|[/_-])(product|features?|platform|windows)([/_-]|$)", "product_features"), (r"(^|[/_-])integrations?([/_-]|$)", "integrations"), (r"(^|[/_-])about([/_-]|$)", "about"), (r"(^|[/_-])(docs?|documentation)([/_-]|$)", "docs"), (r"(^|[/_-])(customers?|case-stud(?:y|ies))([/_-]|$)", "customers_case_studies"), (r"(^|[/_-])(blog|changelog|news)([/_-]|$)", "changelog_blog")):
        if re.search(pattern, path): return category
    return "unknown"

def normalized_hostname(url):
    hostname = urllib.parse.urlparse(url).hostname
    if hostname is None: return None
    hostname = hostname.lower()
    if hostname.endswith("."): hostname = hostname[:-1]
    return hostname[4:] if hostname.startswith("www.") else hostname

def discover_candidates(homepage, homepage_text):
    """Parse actual same-site Markdown links from the fetched homepage."""
    base = urllib.parse.urlparse(homepage)
    found = [(homepage, "homepage")]
    raw_links = re.findall(r"\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))", homepage_text)
    for markdown_href, bare_href in raw_links:
        href = html.unescape(markdown_href or bare_href).strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")): continue
        parsed = urllib.parse.urlparse(urllib.parse.urljoin(homepage, href))
        try: same_port = parsed.port == base.port
        except ValueError: same_port = False
        if parsed.scheme != "https" or normalized_hostname(parsed.geturl()) != normalized_hostname(homepage) or not same_port: continue
        normalized = urllib.parse.urlunparse(("https", parsed.netloc.lower(), parsed.path or "/", "", parsed.query, ""))
        if normalized not in [item[0] for item in found]: found.append((normalized, page_category(normalized)))
    return found

def candidate_trace(candidates, execution):
    """Trace discovered candidates and the decisions actually made for them."""
    decisions = []
    for number, (source, category) in enumerate(candidates[:HARD_CAP + 1], 1):
        over_cap = number > HARD_CAP
        actual = execution.get(source, {})
        accepted = not over_cap
        selected = bool(actual.get("selected", False)) if accepted else False
        decisions.append({"candidate_number": number, "candidate_kind": category, "decision": "rejected_hard_cap" if over_cap else ("admitted_selected" if selected else "admitted_not_selected"), "accepted": accepted, "rejected": over_cap, "selected": selected, "request_made": accepted and bool(actual.get("request_made", False)), "retry_or_fallback_count": int(actual.get("retry_or_fallback_count", 0)) if accepted else 0, "source_url": source})
    attempted_count = len(decisions)
    return {"candidate_order": [{"source_url": source, "category": category} for source, category in candidates[:HARD_CAP + 1]], "selected_candidate_sequence": decisions, "candidate_21": decisions[HARD_CAP] if len(decisions) > HARD_CAP else None, "accepted_count": sum(item["accepted"] for item in decisions), "attempted_count": attempted_count, "attempted_candidate_number": attempted_count or None, "request_made_count": sum(item["request_made"] for item in decisions), "retry_or_fallback_count": sum(item["retry_or_fallback_count"] for item in decisions)}

def select_candidates(candidates):
    """Keep homepage first, then prioritize discovered pricing pages within the cap."""
    if not candidates: return []
    homepage, remainder = candidates[0], candidates[1:HARD_CAP]
    pricing = [candidate for candidate in remainder if candidate[1] == "pricing_plans"]
    non_pricing = [candidate for candidate in remainder if candidate[1] != "pricing_plans"]
    return [homepage] + (pricing + non_pricing)[:DEFAULT_CAP - 1]

def claim(value, evidence): return {"value": value, "evidence_ids": [evidence]}

def failure_support(result, source_url, label):
    status = result.get("status") if result.get("status") is not None else "unavailable"
    return f"{label} unavailable; url={source_url}; status={status}; error={result.get('error') or 'none'}."

def success_support(label): return f"{label} succeeded with non-empty text; response body omitted."

def grounded_pricing(text):
    lower = text.lower()
    named_plan = r"\b(?:free|starter|basic|pro|business|enterprise)(?:\s*/\s*(?:free|starter|basic|pro|business|enterprise))*\s+plans?\b"
    if re.search(rf"\b(?:pricing|plans?)\s+(?:is\s+)?(?:unavailable|not\s+available|not\s+publicly\s+available)\b|\bnot\s+publicly\s+available\b|\bcontact\s+sales\b|{named_plan}\s+(?:is\s+|are\s+)?(?:unavailable|not\s+available|not\s+publicly\s+available)\b", lower): return False
    amount = r"(?:[$€£]\s*\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\s*(?:usd|eur|gbp)\b)"
    price_context = rf"\b(?:pricing|plans?|price|cost)\b[^.\n]{{0,100}}{amount}|{amount}[^.\n]{{0,100}}\b(?:pricing|plans?|price|cost)\b"
    positive_named_plan = rf"{named_plan}(?!\s+(?:is\s+|are\s+)?(?:unavailable|not\s+available|not\s+publicly\s+available)\b)"
    return bool(re.search(price_context, lower) or re.search(positive_named_plan, lower))

def designated_pricing_page(page):
    return page.get("category") == "pricing_plans" and page_category(page.get("source_url", "")) == "pricing_plans"

def make_brief(case, fetched, candidates=None):
    pages, brand_result = fetched[:-1], fetched[-1]; home = pages[0]
    home_id, brand_id = "homepage", "brand"
    home_ok = successful(home)
    page_ids = [home_id] + ["selected-page" if index == 1 else f"selected-page-{index}" for index in range(1, len(pages))]
    page_ok = [successful(page) for page in pages]
    evidence = []
    for index, page in enumerate(pages):
        label = "Homepage Markdown fetch" if index == 0 else "Selected Markdown fetch"
        evidence.append({"id": page_ids[index], "source_url": page["source_url"], "kind": "first_party", "fetched_at": now(), "excerpt_or_support": success_support(label) if page_ok[index] else failure_support(page, page["source_url"], label)})
    evidence.append({"id": brand_id, "source_url": brand_result["source_url"], "kind": "first_party", "fetched_at": now(), "excerpt_or_support": success_support("Brand fetch") if successful(brand_result) else failure_support(brand_result, brand_result["source_url"], "Brand fetch")})
    pricing_candidate = next((index for index, page in enumerate(pages) if page_ok[index] and designated_pricing_page(page)), None)
    pricing_match = next((index for index, page in enumerate(pages) if page_ok[index] and designated_pricing_page(page) and grounded_pricing(page.get("text", ""))), None)
    pricing_seen = pricing_match is not None
    pricing_evidence = page_ids[pricing_match if pricing_seen else pricing_candidate] if (pricing_seen or pricing_candidate is not None) else (page_ids[1] if len(pages) > 1 else home_id)
    pricing_model = claim("subscription pricing grounded in a designated pricing page", pricing_evidence) if pricing_seen else claim(None, pricing_evidence)
    plans = [claim("Observed pricing plan text from a designated pricing page", pricing_evidence)] if pricing_seen else []
    paths = [("summary.one_liner", home_id), ("summary.category", home_id), ("summary.positioning", home_id), ("products[0]", home_id), ("target_market[0]", home_id), ("pricing.model", pricing_evidence), ("features[0]", home_id)]
    if plans: paths.append(("pricing.plans[0]", pricing_evidence))
    selected_pages = [{"category": page.get("category", "homepage") if index else "homepage", "url": page["source_url"], "evidence_id": page_ids[index]} for index, page in enumerate(pages)]
    coverage = []
    if not home_ok: coverage.append("Homepage coverage is unavailable; material company claims remain unknown.")
    if len(pages) == 1: coverage.append("No bounded homepage link with a selected page category was available; pricing is unknown.")
    elif not pricing_seen: coverage.append("No grounded pricing evidence succeeded from a pricing-designated page; pricing is unknown.")
    coverage.append("Brand coverage is unavailable; identity metadata is unknown." if not successful(brand_result) else "Brand output is limited to identity metadata; no brand claims were inferred.")
    coverage.append("Only bounded homepage-link candidates and selected pages were requested; no raw response body was retained.")
    home_claim = "Public company information observed in bounded first-party text." if home_ok else None
    return {"brief_version": "1.0", "generated_at": now(), "company": {"domain": case["domain"], "name": case["name"], "homepage_url": case["homepage"]}, "summary": {"one_liner": claim(home_claim, home_id), "category": claim("Software company." if home_ok else None, home_id), "positioning": claim("Public positioning is supported by the bounded homepage fetch." if home_ok else None, home_id)}, "products": [claim("Products described in bounded first-party text." if home_ok else None, home_id)], "target_market": [claim("Public users and teams described by the company." if home_ok else None, home_id)], "pricing": {"model": pricing_model, "plans": plans, "unknown": not pricing_seen}, "features": [claim("Features described in bounded first-party text." if home_ok else None, home_id)], "integrations": [], "important_pages": selected_pages, "recent_updates": [], "brand": {"name": case["name"] if successful(brand_result) else None, "description": None, "logo_url": None, "colors": [], "fonts": [], "unknown": not successful(brand_result)}, "evidence": evidence, "claim_evidence": [{"claim_path": path, "evidence_ids": [evidence_id]} for path, evidence_id in paths], "coverage_limits": coverage, "meta": {"capabilities_used": ["free_markdown", "free_brand"], "tool_calls": [{"surface": "free_markdown", "operation": "GET", "source_url": item["source_url"], "http_status": item["status"] or 599, "content_type": item["content_type"] or "unavailable"} for item in pages] + [{"surface": "free_brand", "operation": "GET", "source_url": brand_result["source_url"], "http_status": brand_result["status"] or 599, "content_type": brand_result["content_type"] or "unavailable"}], "synthesis": "host_agent", "page_read_count": len(pages), "page_read_budget_default": DEFAULT_CAP, "page_read_budget_hard_cap": HARD_CAP}}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True, type=Path); args = parser.parse_args()
    if "REPLYNODES_API_KEY" in __import__("os").environ: raise SystemExit("refusing an environment containing REPLYNODES_API_KEY")
    reports, briefs, traces = [], [], []
    for case in CASES:
        endpoint = md_url(case["homepage"]); home = get_once(endpoint); home.update({"surface": "free_markdown", "source_url": case["homepage"], "endpoint_url": endpoint})
        candidates = discover_candidates(case["homepage"], home["text"] if successful(home) else "")
        selected = select_candidates(candidates)
        execution = {case["homepage"]: {"selected": True, "request_made": True, "retry_or_fallback_count": 0}}
        fetched = [home]
        for source, category in selected[1:]:
            execution[source] = {"selected": True, "request_made": True, "retry_or_fallback_count": 0}
            endpoint = md_url(source); result = get_once(endpoint); result.update({"surface": "free_markdown", "source_url": source, "endpoint_url": endpoint, "category": category}); fetched.append(result)
        trace = candidate_trace(candidates, execution)
        brand_source = "https://brand.replynodes.com/" + case["domain"]; result = get_once(brand_source); result.update({"surface": "free_brand", "source_url": brand_source, "endpoint_url": brand_source}); fetched.append(result)
        brief = make_brief(case, fetched, candidates); validate_brief(brief); assert brief["meta"]["page_read_count"] <= DEFAULT_CAP <= brief["meta"]["page_read_budget_default"]
        reports.append({"domain": case["domain"], "requests": [{k: v for k, v in item.items() if k != "text"} for item in fetched], "page_read_count": brief["meta"]["page_read_count"], "schema_validation": "passed"}); briefs.append(brief); traces.append(trace)
    skill = Path(__file__).parents[1] / "skills/company-research/SKILL.md"; claimed = [name for name in TOOL_NAMES if name in skill.read_text(encoding="utf-8")]; mcp_status, mcp_type, observed = mcp_tools_once()
    if not set(claimed) <= set(observed): raise SystemExit("live tools/list is missing claimed tool names")
    per_company = {case["domain"]: {"candidate_sequence": trace["selected_candidate_sequence"], "accepted_count": trace["accepted_count"], "attempted_count": trace["attempted_count"], "attempted_candidate_number": trace["attempted_candidate_number"], "candidate_21": trace["candidate_21"], "request_made_count": trace["request_made_count"], "retry_or_fallback_count": trace["retry_or_fallback_count"], "page_read_count": brief["meta"]["page_read_count"]} for case, brief, trace in zip(CASES, briefs, traces)}
    output = {"generated_at": now(), "keyless": True, "surfaces": ["free_markdown", "free_brand"], "requests": reports, "mcp_tools_list": {"endpoint": MCP_URL, "http_status": mcp_status, "content_type": mcp_type or "unavailable", "claimed_tool_names": claimed, "observed_tool_names": observed}, "schema_validation": {case["domain"]: report["schema_validation"] for case, report in zip(CASES, reports)}, "budget_proof": {"default_cap": DEFAULT_CAP, "hard_cap": HARD_CAP, "per_company": per_company, "candidate_traces": {case["domain"]: trace for case, trace in zip(CASES, traces)}}, "briefs": briefs}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"); print(f"wrote sanitized keyless E2E report: {args.output}")

if __name__ == "__main__": main()
