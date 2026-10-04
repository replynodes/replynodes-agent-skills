#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 - "$root" <<'PY'
import copy, json, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "tests"))
from company_brief_validator import check_contract, material_claims, validate_schema

schema = json.loads((root / "references/company-brief.schema.json").read_text())
fixture = json.loads((root / "tests/fixtures/company-brief.json").read_text())
check_contract(fixture, schema=schema)
meta = fixture["meta"]
assert meta["page_read_count"] <= meta["page_read_budget_default"] <= 12
assert meta["page_read_count"] <= meta["page_read_budget_hard_cap"] <= 20

def must_fail(label, mutate):
    candidate = copy.deepcopy(fixture)
    mutate(candidate)
    try: check_contract(candidate, schema=schema)
    except (AssertionError, KeyError): return
    raise AssertionError(f"negative case unexpectedly passed: {label}")

must_fail("duplicate evidence ID", lambda b: b["evidence"].__setitem__(1, dict(b["evidence"][0])))
must_fail("dangling claim evidence ID", lambda b: b["summary"]["one_liner"]["evidence_ids"].__setitem__(0, "missing"))
must_fail("dangling important-page evidence ID", lambda b: b["important_pages"][0].__setitem__("evidence_id", "missing"))
must_fail("dangling linkage evidence ID", lambda b: b["claim_evidence"][0]["evidence_ids"].__setitem__(0, "missing"))
must_fail("dangling claim path", lambda b: b["claim_evidence"].__setitem__(0, {"claim_path": "summary.missing", "evidence_ids": ["home"]}))
must_fail("unlinked material claim", lambda b: b["claim_evidence"].pop())
must_fail("unknown pricing with observed value", lambda b: b["pricing"]["model"].__setitem__("value", "per seat"))
must_fail("unknown pricing with plan", lambda b: b["pricing"]["plans"].append({"value": "Free", "evidence_ids": ["home"]}))
must_fail("homepage discovery capability missing", lambda b: b["meta"]["capabilities_used"].remove("free_homepage_discovery"))
must_fail("homepage discovery source mismatch", lambda b: b["meta"]["tool_calls"][0].__setitem__("source_url", "https://other.test/"))
must_fail("tool call endpoint missing", lambda b: b["meta"]["tool_calls"][0].pop("endpoint_url"))

observed = copy.deepcopy(fixture)
observed["pricing"]["unknown"] = False
observed["pricing"]["model"]["value"] = "subscription"
observed["pricing"]["plans"] = [{"value": "Free", "evidence_ids": ["home"]}]
observed["claim_evidence"].append({"claim_path": "pricing.plans[0]", "evidence_ids": ["home"]})
check_contract(observed, schema=schema)
must_fail("observed pricing without model", lambda b: (b["pricing"].__setitem__("unknown", False), b["pricing"]["plans"].append({"value": "Free", "evidence_ids": ["home"]})))
must_fail("observed pricing without plans", lambda b: (b["pricing"].__setitem__("unknown", False), b["pricing"]["model"].__setitem__("value", "subscription")))

negative = copy.deepcopy(fixture)
del negative["meta"]["page_read_budget_hard_cap"]
try: validate_schema(negative, schema=schema)
except AssertionError: pass
else: raise AssertionError("negative schema assertion unexpectedly passed")

import importlib.util
runner_spec = importlib.util.spec_from_file_location("company_research_runner", root / "tests/run-company-research-keyless-e2e.py")
runner = importlib.util.module_from_spec(runner_spec)
runner_spec.loader.exec_module(runner)
assert runner.sanitize_request_records([{"surface": "free_markdown", "source_url": "https://example.test/", "endpoint_url": "https://md.replynodes.com/x", "status": 200, "content_type": "text/markdown", "text": "secret body", "error": None}]) == [{"surface": "free_markdown", "source_url": "https://example.test/", "endpoint_url": "https://md.replynodes.com/x", "http_status": 200, "content_type": "text/markdown", "operation": "GET"}]

def fake_fetch(status, text, error=None, content_type="text/markdown"):
    return {"status": status, "content_type": content_type, "text": text, "error": error}

failed_home = fake_fetch(503, "Public company information observed in bounded first-party text.", "HTTPError")
failed_home.update({"source_url": "https://example.test/", "category": "homepage"})
successful_brand = fake_fetch(200, "Brand identity")
successful_brand.update({"source_url": "https://brand.replynodes.com/example.test"})
failed_case = {"domain": "example.test", "name": "Example", "homepage": "https://example.test/"}
failed_home_brief = runner.make_brief(failed_case, [failed_home, successful_brand])
assert all(item["value"] is None for item in material_claims(failed_home_brief).values())
assert any("homepage coverage is unavailable" in item.lower() for item in failed_home_brief["coverage_limits"])
assert "unavailable" in failed_home_brief["evidence"][0]["excerpt_or_support"].lower()
assert "succeeded" in failed_home_brief["evidence"][-1]["excerpt_or_support"].lower()
assert all(word not in failed_home_brief["evidence"][0]["excerpt_or_support"].lower() for word in ("successful", "observed", "completed"))

successful_home = fake_fetch(200, "Homepage text")
successful_home.update({"source_url": "https://example.test/", "category": "homepage"})
failed_brand = fake_fetch(None, "", "URLError", "")
failed_brand.update({"source_url": "https://brand.replynodes.com/example.test"})
failed_brand_brief = runner.make_brief(failed_case, [successful_home, failed_brand])
assert failed_brand_brief["brand"]["name"] is None
assert failed_brand_brief["brand"]["description"] is None
assert failed_brand_brief["brand"]["logo_url"] is None
assert failed_brand_brief["brand"]["colors"] == [] and failed_brand_brief["brand"]["fonts"] == []
assert failed_brand_brief["brand"]["unknown"] is True
assert all(item["value"] is not None for path, item in material_claims(failed_brand_brief).items() if path != "pricing.model")
assert "succeeded" in failed_brand_brief["evidence"][0]["excerpt_or_support"].lower()
assert "unavailable" in failed_brand_brief["evidence"][-1]["excerpt_or_support"].lower()

failed_page = fake_fetch(502, "Pricing plan observed at $99.", "HTTPError")
failed_page.update({"source_url": "https://example.test/pricing/plans", "category": "pricing_plans"})
failed_page_brief = runner.make_brief(failed_case, [successful_home, failed_page, successful_brand])
assert failed_page_brief["pricing"] == {"model": {"value": None, "evidence_ids": ["selected-page"]}, "plans": [], "unknown": True}
assert "unavailable" in failed_page_brief["evidence"][1]["excerpt_or_support"].lower()
assert "succeeded" not in failed_page_brief["evidence"][1]["excerpt_or_support"].lower()
runner.validate_brief(failed_page_brief)

product_page = fake_fetch(200, "Our plans include a free trial and $ symbol month text.")
product_page.update({"source_url": "https://example.test/en-us/windows/", "category": "product_features"})
generic_pricing_brief = runner.make_brief(failed_case, [successful_home, product_page, successful_brand])
assert generic_pricing_brief["pricing"] == {"model": {"value": None, "evidence_ids": ["selected-page"]}, "plans": [], "unknown": True}
runner.validate_brief(generic_pricing_brief)

pricing_page = fake_fetch(200, "Pricing plans start at $19 USD per month.")
pricing_page.update({"source_url": "https://example.test/pricing/plans", "category": "pricing_plans"})
grounded_pricing_brief = runner.make_brief(failed_case, [successful_home, pricing_page, successful_brand])
assert grounded_pricing_brief["pricing"]["unknown"] is False
assert grounded_pricing_brief["pricing"]["plans"]
runner.validate_brief(grounded_pricing_brief)

markdown_429 = fake_fetch(429, "", "HTTPError")
markdown_429.update({"surface": "free_markdown", "source_url": pricing_page["source_url"], "endpoint_url": "https://md.replynodes.com/https%3A%2F%2Fexample.test%2Fpricing%2Fplans", "category": "pricing_plans"})
direct_pricing = fake_fetch(200, "Pricing plans start at $19 USD per month.", content_type="text/html; charset=utf-8")
direct_pricing.update({"surface": "free_direct_pricing", "source_url": pricing_page["source_url"], "endpoint_url": pricing_page["source_url"], "category": "pricing_plans"})
direct_pricing["attempts"] = [markdown_429, direct_pricing.copy()]
direct_pricing_brief = runner.make_brief(failed_case, [successful_home, direct_pricing, successful_brand])
assert "free_direct_pricing" in direct_pricing_brief["meta"]["capabilities_used"]
assert [call["surface"] for call in direct_pricing_brief["meta"]["tool_calls"]].count("free_direct_pricing") == 1
runner.validate_brief(direct_pricing_brief)

figma_pricing_page = fake_fetch(200, "Professional Monthly $16 /mo; Organization $55 /mo. Enterprise plan — contact sales.")
figma_pricing_page.update({"source_url": "https://example.test/pricing", "category": "pricing_plans"})
assert runner.grounded_pricing(figma_pricing_page["text"]) is True
assert runner.grounded_pricing("Free plan") is False
assert runner.grounded_pricing("<h3>Free</h3><span>$0</span><span aria-label='$6 per user/month'></span>") is True

product_page = fake_fetch(200, "Product details and feature overview.")
product_page.update({"source_url": "https://example.test/product", "category": "product_features"})
later_pricing_page = fake_fetch(200, "Plans start at $29 USD per month.")
later_pricing_page.update({"source_url": "https://example.test/pricing/plans", "category": "pricing_plans"})
later_pricing_brief = runner.make_brief(failed_case, [successful_home, product_page, later_pricing_page, successful_brand])
assert later_pricing_brief["pricing"]["unknown"] is False
assert later_pricing_brief["pricing"]["model"]["evidence_ids"] == ["selected-page-2"]
assert later_pricing_brief["pricing"]["plans"][0]["evidence_ids"] == ["selected-page-2"]
assert {item["evidence_id"] for item in later_pricing_brief["important_pages"]} >= {"selected-page", "selected-page-2"}
assert later_pricing_brief["important_pages"][2]["url"] == later_pricing_page["source_url"]
runner.validate_brief(later_pricing_brief)

unavailable_page = fake_fetch(200, "Pricing unavailable in this region.")
unavailable_page.update({"source_url": "https://example.test/pricing", "category": "pricing_plans"})
unavailable_brief = runner.make_brief(failed_case, [successful_home, product_page, unavailable_page, successful_brand])
assert unavailable_brief["pricing"] == {"model": {"value": None, "evidence_ids": ["selected-page-2"]}, "plans": [], "unknown": True}
assert any("pricing" in item.lower() and "unknown" in item.lower() for item in unavailable_brief["coverage_limits"])
runner.validate_brief(unavailable_brief)

for text in ("Contact sales for pricing.", "Pricing is not publicly available.", "Free plan not available.", "Pro/Enterprise plan unavailable/not publicly available."):
    non_positive_page = fake_fetch(200, text)
    non_positive_page.update({"source_url": "https://example.test/pricing", "category": "pricing_plans"})
    non_positive_brief = runner.make_brief(failed_case, [successful_home, non_positive_page, successful_brand])
    assert non_positive_brief["pricing"]["unknown"] is True
    assert non_positive_brief["pricing"]["model"]["value"] is None
    assert non_positive_brief["pricing"]["plans"] == [], text
    runner.validate_brief(non_positive_brief)

for text in ("Free plan not available; Pro $20/month.", "Enterprise plan: not publicly available. $99/month", "Pro/Enterprise plan unavailable/not publicly available.", "Professional $16/month; Enterprise plan unavailable; contact sales.", "Plans unavailable — contact sales.", "Contact sales for pricing.\nProfessional plan $20/month.", "Pricing unavailable. Starter $10/month.", "No pricing information available.", "No plans offered.", "Free plan not available.", "Pricing not publicly available."):
    assert runner.grounded_pricing(text) is False

discovery_text = "[Product](/product) [Pricing](https://example.test/pricing/plans) [External](https://other.test/about)"
discovered = runner.discover_candidates(failed_case["homepage"], discovery_text)
assert discovered == [(failed_case["homepage"], "homepage"), ("https://example.test/product", "product_features"), ("https://example.test/pricing/plans", "pricing_plans")]
html_discovered = runner.discover_candidates(failed_case["homepage"], "", '<a href="/pricing">Pricing</a><a href="https://other.test/pricing">External</a>')
assert html_discovered == [(failed_case["homepage"], "homepage"), ("https://example.test/pricing", "pricing_plans")]
www_homepage = "https://www.example.test/"
www_discovery = runner.discover_candidates(www_homepage, "[Canonical](https://example.test/pricing) [Typo](https://ww.example.test/plans) [External](https://other.test/pricing)")
assert www_discovery == [(www_homepage, "homepage"), ("https://example.test/pricing", "pricing_plans")]
dot_homepage = "https://www.example.test./"
dot_discovery = runner.discover_candidates(dot_homepage, "[Pricing](https://example.test./pricing)")
assert dot_discovery == [(dot_homepage, "homepage"), ("https://example.test./pricing", "pricing_plans")]
assert runner.normalized_hostname("https://example.test./pricing") == "example.test"
assert runner.normalized_hostname("https://www.example.test.:443/") == "example.test"
assert runner.normalized_hostname("https://www.example.test.") == "example.test"
assert runner.normalized_hostname("https://example.test.") == "example.test"
www_dot_port_discovery = runner.discover_candidates("https://www.example.test.:443/", "[Pricing](https://example.test.:443/pricing) [Wrong port](https://example.test.:8443/pricing)")
assert www_dot_port_discovery == [("https://www.example.test.:443/", "homepage"), ("https://example.test.:443/pricing", "pricing_plans")]
prioritized = [(failed_case["homepage"], "homepage")] + [(f"https://example.test/page-{i}", "unknown") for i in range(1, 4)] + [("https://example.test/pricing", "pricing_plans")] + [(f"https://example.test/page-{i}", "unknown") for i in range(4, 11)]
selected = runner.select_candidates(prioritized)
assert len(selected) == runner.E2E_TARGET_READS
assert selected[1:] == [("https://example.test/pricing", "pricing_plans")] + [(f"https://example.test/page-{i}", "unknown") for i in range(1, runner.E2E_TARGET_READS - 1)]
prioritized_trace = runner.candidate_trace(prioritized, {source: {"selected": True, "request_made": True} for source, _ in selected})
pricing_trace = next(item for item in prioritized_trace["selected_candidate_sequence"] if item["source_url"] == "https://example.test/pricing")
assert pricing_trace["selected"] is True and pricing_trace["request_made"] is True
prioritized_13 = [(failed_case["homepage"], "homepage")] + [(f"https://example.test/page-{i}", "unknown") for i in range(1, 12)] + [("https://example.test/pricing", "pricing_plans")]
selected_13 = runner.select_candidates(prioritized_13)
assert len(selected_13) == runner.E2E_TARGET_READS
assert all(source != "https://example.test/pricing" for source, _ in selected_13)
prioritized_13_trace = runner.candidate_trace(prioritized_13, {source: {"selected": True, "request_made": True} for source, _ in selected_13})
pricing_trace_13 = next(item for item in prioritized_13_trace["selected_candidate_sequence"] if item["source_url"] == "https://example.test/pricing")
assert pricing_trace_13["selected"] is False and pricing_trace_13["request_made"] is False
many = [(failed_case["homepage"], "homepage")] + [(f"https://example.test/page-{i}", "unknown") for i in range(1, 21)]
trace = runner.candidate_trace(many, {failed_case["homepage"]: {"selected": True, "request_made": True, "retry_or_fallback_count": 0}})
assert trace["accepted_count"] == 20 and trace["candidate_21"]["accepted"] is False
assert trace["candidate_21"]["selected"] is False and trace["candidate_21"]["request_made"] is False
assert trace["attempted_count"] == 21 and trace["attempted_candidate_number"] == 21
short = many[:5]
short_trace = runner.candidate_trace(short, {failed_case["homepage"]: {"selected": True, "request_made": True, "retry_or_fallback_count": 0}})
assert short_trace["candidate_21"] is None
assert short_trace["attempted_count"] == len(short) and short_trace["attempted_candidate_number"] == len(short)
print("company brief schema fixture passed (schema, claim/evidence integrity, pricing, and negative cases)")
PY
