#!/usr/bin/env python3
"""Bounded, keyless ReplyNodes company-research contract run."""
import argparse
import datetime as dt
import html
import json
import re
import sys
from html.parser import HTMLParser
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
E2E_TARGET_READS = 4

CASES = (
    {"domain": "figma.com", "name": "Figma", "homepage": "https://www.figma.com/"},
    {"domain": "loom.com", "name": "Loom", "homepage": "https://www.loom.com/"},
    {"domain": "microsoft.com", "name": "Microsoft", "homepage": "https://www.microsoft.com/"},
)

def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def get_once(url, accept="text/markdown,application/json,text/plain"):
    request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "replynodes-company-research-contract/1.0"})
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

class HomepageHrefParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a": return
        for name, value in attrs:
            if name.lower() == "href" and value is not None:
                self.hrefs.append(value)

class PricingTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name.lower() in ("aria-label", "title") and value:
                self.parts.append(value)

    def handle_endtag(self, tag):
        if tag.lower() in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "li"}:
            self.parts.append("\n")

    def text(self):
        return " ".join(self.parts)


def discover_candidates(homepage, homepage_text, homepage_html=""):
    """Parse actual same-site Markdown and homepage HTML links."""
    base = urllib.parse.urlparse(homepage)
    found = [(homepage, "homepage")]
    raw_links = re.findall(r"\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))", homepage_text)
    html_parser = HomepageHrefParser()
    html_parser.feed(homepage_html)
    hrefs = [html.unescape(markdown_href or bare_href) for markdown_href, bare_href in raw_links]
    hrefs.extend(html_parser.hrefs)
    for href in hrefs:
        href = href.strip()
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
    """Keep the homepage and prioritize the first in-cap pricing candidate within DEFAULT_CAP."""
    if not candidates: return []
    homepage = candidates[0]
    in_cap = candidates[1:DEFAULT_CAP]
    pricing = next((candidate for candidate in in_cap if candidate[1] == "pricing_plans"), None)
    selected = [homepage]
    if pricing is not None:
        selected.append(pricing)
    selected.extend(candidate for candidate in in_cap if candidate != pricing and len(selected) < E2E_TARGET_READS)
    return selected

def claim(value, evidence): return {"value": value, "evidence_ids": [evidence]}

def failure_support(result, source_url, label):
    status = result.get("status") if result.get("status") is not None else "unavailable"
    return f"{label} unavailable; url={source_url}; status={status}; error={result.get('error') or 'none'}."

def success_support(label): return f"{label} succeeded with non-empty text; response body omitted."

def request_record(result):
    return {"surface": result.get("surface", "free_markdown"), "operation": "GET", "source_url": result["source_url"], "endpoint_url": result.get("endpoint_url", result["source_url"]), "http_status": result["status"] or 599, "content_type": result["content_type"] or "unavailable"}

def grounded_pricing(text):
    html_mode = bool(re.match(r"\s*(?:<!doctype\s+html|<html\b)", text, re.I))
    if html_mode:
        parser = PricingTextParser()
        parser.feed(text)
        text = parser.text()
    lower = text.lower()
    amount = r"(?:[$€£]\s*\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\s*(?:usd|eur|gbp)\b)"
    paid_plan = r"\b(?:free|starter|basic|pro|professional|business|enterprise|team|organization|collab|dev|full)\b"
    unavailable = r"\b(?:unavailable|not\s*[- ]\s*(?:publicly\s+)?available|no\s+pricing|no\s+plans?|(?:free|starter|basic|pro|business|enterprise|team)\s+plans?\s+(?:is\s+|are\s+)?(?:not|unavailable)|pricing\s+(?:is\s+)?(?:unavailable|not\s+public)|plans?\s+(?:are\s+)?(?:unavailable|not\s+public))\b"
    enterprise_cta = r"\benterprise(?:\s+plan)?\s*(?:[-—–:]\s*)?contact\s+sales\b|\bcontact\s+sales\s+(?:for\s+)?enterprise(?:\s+plan)?\b"
    if re.search(r"\bcontact\s+sales\s+(?:for\s+)?pricing\b", lower):
        return False
    searchable = re.sub(enterprise_cta, " ", lower)
    searchable = re.sub(r"\bcontact\s+sales\b", " ", searchable)
    if re.search(unavailable, searchable):
        return False
    for line in searchable.splitlines():
        if re.search(unavailable, line): continue
        if re.search(rf"\b(?:pricing|plans?|price|cost)\b[^.\n]{{0,160}}{amount}|{amount}[^.\n]{{0,160}}\b(?:pricing|plans?|price|cost)\b|{paid_plan}[^.\n]{{0,160}}{amount}|{amount}[^.\n]{{0,160}}{paid_plan}|{amount}\s*(?:per\s+)?(?:user|seat)\s*/\s*(?:month|year)", line):
            return True
    return False

def designated_pricing_page(page):
    return page.get("category") == "pricing_plans" and page_category(page.get("source_url", "")) == "pricing_plans"

def make_brief(case, fetched, candidates=None, discovery=None):
    pages, brand_result = fetched[:-1], fetched[-1]; home = pages[0]
    home_id, brand_id = "homepage", "brand"
    home_ok = successful(home)
    page_ids = [home_id] + ["selected-page" if index == 1 else f"selected-page-{index}" for index in range(1, len(pages))]
    page_ok = [successful(page) for page in pages]
    evidence = []
    for index, page in enumerate(pages):
        label = "Homepage Markdown fetch" if index == 0 else ("Direct first-party pricing HTML fetch" if page.get("surface") == "free_direct_pricing" else "Selected Markdown fetch")
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
    discovery = discovery or {"surface": "free_homepage_discovery", "source_url": case["homepage"], "endpoint_url": case["homepage"], "status": None, "content_type": "", "error": "not executed in fixture"}
    discovery_call = [request_record(discovery)]
    page_calls = [request_record(record) for page in pages for record in page.get("attempts", [page])]
    capabilities = ["free_markdown", "free_homepage_discovery", "free_brand"]
    if any(page.get("surface") == "free_direct_pricing" for page in pages): capabilities.append("free_direct_pricing")
    return {"brief_version": "1.0", "generated_at": now(), "company": {"domain": case["domain"], "name": case["name"], "homepage_url": case["homepage"]}, "summary": {"one_liner": claim(home_claim, home_id), "category": claim("Software company." if home_ok else None, home_id), "positioning": claim("Public positioning is supported by the bounded homepage fetch." if home_ok else None, home_id)}, "products": [claim("Products described in bounded first-party text." if home_ok else None, home_id)], "target_market": [claim("Public users and teams described by the company." if home_ok else None, home_id)], "pricing": {"model": pricing_model, "plans": plans, "unknown": not pricing_seen}, "features": [claim("Features described in bounded first-party text." if home_ok else None, home_id)], "integrations": [], "important_pages": selected_pages, "recent_updates": [], "brand": {"name": case["name"] if successful(brand_result) else None, "description": None, "logo_url": None, "colors": [], "fonts": [], "unknown": not successful(brand_result)}, "evidence": evidence, "claim_evidence": [{"claim_path": path, "evidence_ids": [evidence_id]} for path, evidence_id in paths], "coverage_limits": coverage, "meta": {"capabilities_used": capabilities, "tool_calls": discovery_call + page_calls + [request_record(brand_result)], "synthesis": "host_agent", "page_read_count": len(pages), "page_read_budget_default": DEFAULT_CAP, "page_read_budget_hard_cap": HARD_CAP}}

def sanitize_request_records(records):
    return [request_record(record) for record in records]

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True, type=Path); args = parser.parse_args()
    if "REPLYNODES_API_KEY" in __import__("os").environ: raise SystemExit("refusing an environment containing REPLYNODES_API_KEY")
    reports, briefs, traces = [], [], []
    for case in CASES:
        endpoint = md_url(case["homepage"]); home = get_once(endpoint); home.update({"surface": "free_markdown", "source_url": case["homepage"], "endpoint_url": endpoint}); home["attempts"] = [home.copy()]
        discovery = get_once(case["homepage"], "text/html,application/xhtml+xml"); discovery.update({"surface": "free_homepage_discovery", "source_url": case["homepage"], "endpoint_url": case["homepage"]})
        candidates = discover_candidates(case["homepage"], home["text"] if successful(home) else "", discovery["text"] if successful(discovery) else "")
        selected = select_candidates(candidates)
        execution = {case["homepage"]: {"selected": True, "request_made": True, "retry_or_fallback_count": 0}}
        fetched = [home]
        direct_pricing_used = False
        for source, category in selected[1:]:
            execution[source] = {"selected": True, "request_made": True, "retry_or_fallback_count": 0}
            endpoint = md_url(source); markdown = get_once(endpoint); markdown.update({"surface": "free_markdown", "source_url": source, "endpoint_url": endpoint, "category": category})
            result = markdown; result["attempts"] = [markdown.copy()]
            if category == "pricing_plans" and markdown.get("status") == 429 and not direct_pricing_used:
                direct_pricing_used = True
                execution[source]["retry_or_fallback_count"] = 1
                direct = get_once(source, "text/html,application/xhtml+xml,text/plain")
                direct.update({"surface": "free_direct_pricing", "source_url": source, "endpoint_url": source, "category": category})
                result = direct; result["attempts"] = [markdown.copy(), direct.copy()]
            fetched.append(result)
        trace = candidate_trace(candidates, execution)
        brand_source = "https://brand.replynodes.com/" + case["domain"]; brand_result = get_once(brand_source); brand_result.update({"surface": "free_brand", "source_url": brand_source, "endpoint_url": brand_source}); brand_result["attempts"] = [brand_result.copy()]; fetched.append(brand_result)
        brief = make_brief(case, fetched, candidates, discovery); validate_brief(brief); assert brief["meta"]["page_read_count"] <= DEFAULT_CAP <= brief["meta"]["page_read_budget_default"]
        sanitized_requests = sanitize_request_records([discovery] + [record for page in fetched for record in page.get("attempts", [page])] + [brand_result])
        assert all("text" not in record and "error" not in record and "status" not in record for record in sanitized_requests)
        reports.append({"domain": case["domain"], "requests": sanitized_requests, "page_read_count": brief["meta"]["page_read_count"], "schema_validation": "passed"}); briefs.append(brief); traces.append(trace)
    if not any(not brief["pricing"]["unknown"] for brief in briefs):
        raise SystemExit("live keyless E2E found no grounded public-pricing case")
    skill = Path(__file__).parents[1] / "skills/company-research/SKILL.md"; claimed = [name for name in TOOL_NAMES if name in skill.read_text(encoding="utf-8")]; mcp_status, mcp_type, observed = mcp_tools_once()
    if not set(claimed) <= set(observed): raise SystemExit("live tools/list is missing claimed tool names")
    per_company = {case["domain"]: {"candidate_sequence": trace["selected_candidate_sequence"], "accepted_count": trace["accepted_count"], "attempted_count": trace["attempted_count"], "attempted_candidate_number": trace["attempted_candidate_number"], "candidate_21": trace["candidate_21"], "request_made_count": trace["request_made_count"], "retry_or_fallback_count": trace["retry_or_fallback_count"], "page_read_count": brief["meta"]["page_read_count"]} for case, brief, trace in zip(CASES, briefs, traces)}
    output = {"generated_at": now(), "keyless": True, "surfaces": ["free_markdown", "free_homepage_discovery", "free_direct_pricing", "free_brand"], "requests": reports, "mcp_tools_list": {"endpoint": MCP_URL, "http_status": mcp_status, "content_type": mcp_type or "unavailable", "claimed_tool_names": claimed, "observed_tool_names": observed}, "schema_validation": {case["domain"]: report["schema_validation"] for case, report in zip(CASES, reports)}, "budget_proof": {"default_cap": DEFAULT_CAP, "hard_cap": HARD_CAP, "per_company": per_company, "candidate_traces": {case["domain"]: trace for case, trace in zip(CASES, traces)}}, "briefs": briefs}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"); print(f"wrote sanitized keyless E2E report: {args.output}")

if __name__ == "__main__": main()
