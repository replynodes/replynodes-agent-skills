#!/usr/bin/env python3
"""Deterministic V2 scenario coverage: extraction, sparse, partial failure, goal-aware."""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
p = Path(__file__).with_name("run-company-research-keyless-e2e.py")
spec = importlib.util.spec_from_file_location("runner", p)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

case = {"domain": "example.test", "name": "Example", "homepage": "https://example.test/"}


def fetch(status, text, source, content_type="text/markdown", surface="free_markdown"):
    return {"status": status, "text": text, "source_url": source, "endpoint_url": source,
            "content_type": content_type, "error": None if status == 200 else "HTTPError",
            "surface": surface, "attempts": []}


HOME = (
    "# Acme is a platform for modern data teams.\n\n"
    "Powering businesses of all sizes.\n\n"
    "## Build dashboards\n\n"
    "Integrate with Slack and GitHub to sync reporting across teams.\n"
)
home = fetch(200, HOME, case["homepage"])
brand = fetch(200, "Example identity", "https://brand.replynodes.com/example.test", "application/json", "free_brand")
discovery = fetch(200, "<a href='/pricing'>Pricing</a>", case["homepage"], "text/html", "free_homepage_discovery")

brief = runner.make_brief(case, [home, brand], [(case["homepage"], "homepage")], discovery)
runner.validate_brief(brief)
assert brief["meta"]["page_read_count"] == 1
assert brief["pricing"]["unknown"] is True
# Extraction is body-derived, not placeholder text.
assert brief["summary"]["one_liner"]["value"] == "Acme is a platform for modern data teams."
assert brief["summary"]["positioning"]["value"] == "Powering businesses of all sizes."
for claim in brief["target_market"] + brief["products"]:
    assert claim["value"] in HOME, claim
excerpts = {item["id"]: item["excerpt_or_support"] for item in brief["evidence"]}
for claim in brief["products"] + brief["target_market"]:
    assert any(claim["value"][:30] in excerpts[eid] or excerpts[eid] in claim["value"] for eid in claim["evidence_ids"])
assert {item["field"] for item in brief["unknowns"]} >= {"integrations", "customers", "pricing"}

# Sparse: a single readable page still produces a bounded, honest brief.
assert brief["meta"]["page_read_count"] == 1
assert all(not runner.is_filler(claim["value"]) for claim in brief["products"] + brief["target_market"])

# Partial failure: an unavailable homepage leaves material claims unknown.
failed_home = fetch(503, "", case["homepage"])
partial = runner.make_brief(case, [failed_home, brand], [(case["homepage"], "homepage")], discovery)
runner.validate_brief(partial)
assert partial["meta"]["partial_failure_count"] == 1
from company_brief_validator import material_claims
assert all(item["value"] is None for item in material_claims(partial).values())
assert any("homepage coverage is unavailable" in item.lower() for item in partial["coverage_limits"])

# Goal-aware: same core facts, added notable context, no scoring.
goal = runner.make_brief(case, [home, brand], [(case["homepage"], "homepage")], discovery, research_goal="understand developer platform positioning")
runner.validate_brief(goal)
assert goal["meta"]["research_goal"]
assert goal["notable_context"]
assert goal["summary"] == brief["summary"]
assert goal["products"] == brief["products"]
assert goal["target_market"] == brief["target_market"]
assert goal["pricing"] == brief["pricing"]

# Canonicalization/dedupe: locale, www, trailing dot, query are collapsed.
deduped = runner.discover_candidates("https://www.example.test/", "[EN](https://example.test/en-us/pricing) [FR](https://example.test/fr/pricing) [Q](https://example.test/pricing?utm_source=x)")
assert deduped == [("https://www.example.test/", "homepage"), ("https://example.test/pricing", "pricing_plans")]
assert runner.canonical_url("https://www.example.test./en-GB/pricing?utm=1") == "https://example.test/pricing"
assert runner.canonical_url("https://example.test/en-us/") == "https://example.test/"
assert runner.page_category("https://example.test/product-integrations") == "integrations"
assert runner.page_category("https://example.test/en-fr/customers/hertz") == "customers_case_studies"
assert runner.page_category("https://example.test/support-plans") == "pricing_plans"

# Extraction rejects filler body content instead of emitting a placeholder.
filler_home = fetch(200, "# Software company.\n\nProducts described in bounded first-party text.", case["homepage"])
filler_brief = runner.make_brief(case, [filler_home, brand], [(case["homepage"], "homepage")], discovery)
runner.validate_brief(filler_brief)
assert all(item["value"] is None for item in material_claims(filler_brief).values() if item["value"] != "Software company.")
assert not any(item["value"] == "Products described in bounded first-party text." for item in material_claims(filler_brief).values())

print("V2 scenarios passed: extraction, sparse, partial_failure, goal_aware, canonical_dedupe, filler_rejection")
