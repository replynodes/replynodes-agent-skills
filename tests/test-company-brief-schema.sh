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
assert meta["page_read_count"] <= meta["page_read_budget_default"] <= 8
assert meta["page_read_count"] <= meta["page_read_budget_hard_cap"] <= 12

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
must_fail("successful page count includes failure", lambda b: b["meta"].update({"pages_attempted": 2, "partial_failure_count": 1, "page_read_count": 2}))
must_fail("source coverage count mismatch", lambda b: b["meta"]["source_coverage"].__setitem__(0, {"category": "homepage", "pages_read": 0}))
must_fail("dated signal without publication date", lambda b: b["signals"].__setitem__(0, {"type": "positioning", "summary": "x", "observed_at": "2026-01-01T00:00:00Z", "recency": "dated", "evidence_ids": ["home"]}))
must_fail("current observation with publication date", lambda b: b["signals"].__setitem__(0, {"type": "positioning", "summary": "x", "observed_at": "2026-01-01T00:00:00Z", "published_at": "2026-01-01", "recency": "current_observation", "evidence_ids": ["home"]}))

# Phase 2 quality gates: filler, meaningless text, irrelevant excerpts, explicit unknowns, contribution.
must_fail("filler claim text", lambda b: b["products"][0].__setitem__("value", "Products described in bounded first-party text."))
must_fail("meaningless claim text", lambda b: b["products"][0].__setitem__("value", " 5 "))
must_fail("evidence excerpt unrelated to claim", lambda b: b["evidence"][0].__setitem__("excerpt_or_support", "completely unrelated zebra content"))
must_fail("empty material field without explicit unknown", lambda b: b["unknowns"].__setitem__(slice(None), [u for u in b["unknowns"] if u["field"] not in ("integrations", "customers")]))
must_fail("unknown pricing without pricing unknown entry", lambda b: b["unknowns"].__setitem__(slice(None), [u for u in b["unknowns"] if u["field"] != "pricing"]))
must_fail("read supported page without contribution", lambda b: b["meta"]["page_contribution"][1].__setitem__("claims", []))
must_fail("page contribution references unknown claim path", lambda b: b["meta"]["page_contribution"][0]["claims"].append("products[9]"))
must_fail("unread page contribution lists claims", lambda b: b["meta"]["page_contribution"].append({"evidence_id": "home", "category": "homepage", "read": False, "claims": ["products[0]"]}))

observed = copy.deepcopy(fixture)
observed["pricing"]["unknown"] = False
observed["pricing"]["model"] = {"value": "Public web tools", "evidence_ids": ["home"]}
observed["pricing"]["plans"] = [{"value": "Starter — $19 /month", "evidence_ids": ["pricing-unknown"]}]
observed["evidence"][1]["excerpt_or_support"] = "Example offers a Starter plan for $19 /month."
observed["unknowns"] = [u for u in observed["unknowns"] if u["field"] != "pricing"]
observed["claim_evidence"].append({"claim_path": "pricing.plans[0]", "evidence_ids": ["pricing-unknown"]})
check_contract(observed, schema=schema)
must_fail("observed pricing without model", lambda b: (b["pricing"].__setitem__("unknown", False), b["pricing"]["plans"].append({"value": "Public web tools", "evidence_ids": ["home"]}), b["unknowns"].__setitem__(slice(None), [u for u in b["unknowns"] if u["field"] != "pricing"]), b["claim_evidence"].append({"claim_path": "pricing.plans[0]", "evidence_ids": ["home"]})))
must_fail("observed pricing without plans", lambda b: (b["pricing"].__setitem__("unknown", False), b["pricing"]["model"].__setitem__("value", "Public web tools"), b["unknowns"].__setitem__(slice(None), [u for u in b["unknowns"] if u["field"] != "pricing"])))

negative = copy.deepcopy(fixture)
del negative["meta"]["page_read_budget_hard_cap"]
try: validate_schema(negative, schema=schema)
except AssertionError: pass
else: raise AssertionError("negative schema assertion unexpectedly passed")

negative = copy.deepcopy(fixture)
del negative["meta"]["page_contribution"]
try: validate_schema(negative, schema=schema)
except AssertionError: pass
else: raise AssertionError("missing page_contribution unexpectedly passed schema")

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
runner.validate_brief(failed_home_brief)
assert all(item["value"] is None for item in material_claims(failed_home_brief).values())
assert any("homepage coverage is unavailable" in item.lower() for item in failed_home_brief["coverage_limits"])
assert "unavailable" in failed_home_brief["evidence"][0]["excerpt_or_support"].lower()
brand_evidence = next(item for item in failed_home_brief["evidence"] if item["id"] == "brand")
assert "succeeded" in brand_evidence["excerpt_or_support"].lower()
assert all(word not in failed_home_brief["evidence"][0]["excerpt_or_support"].lower() for word in ("successful", "observed", "completed"))

BODY = "# Example makes public web tools.\n\nPowering teams everywhere.\n\n## Build dashboards\n\nConnect Example to Slack to sync reporting across teams.\n"
successful_home = fake_fetch(200, BODY)
successful_home.update({"source_url": "https://example.test/", "category": "homepage"})
failed_brand = fake_fetch(None, "", "URLError", "")
failed_brand.update({"source_url": "https://brand.replynodes.com/example.test"})
failed_brand_brief = runner.make_brief(failed_case, [successful_home, failed_brand])
runner.validate_brief(failed_brand_brief)
assert failed_brand_brief["summary"]["one_liner"]["value"] == "Example makes public web tools."
assert failed_brand_brief["brand"]["name"] is None
assert failed_brand_brief["brand"]["description"] is None
assert set(failed_brand_brief["brand"]) == {"name", "description", "unknown"}
assert failed_brand_brief["brand"]["unknown"] is True
assert {"integrations", "customers", "pricing"} <= {item["field"] for item in failed_brand_brief["unknowns"]}
failed_brand_evidence = next(item for item in failed_brand_brief["evidence"] if item["id"] == "brand")
assert "succeeded" not in failed_brand_evidence["excerpt_or_support"].lower()
assert "unavailable" in failed_brand_evidence["excerpt_or_support"].lower()

failed_page = fake_fetch(502, "Pricing plan observed at $99.", "HTTPError")
failed_page.update({"source_url": "https://example.test/pricing/plans", "category": "pricing_plans"})
failed_page_brief = runner.make_brief(failed_case, [successful_home, failed_page, successful_brand])
assert failed_page_brief["pricing"] == {"model": {"value": None, "evidence_ids": ["homepage"]}, "plans": [], "unknown": True}
assert "unavailable" in failed_page_brief["evidence"][1]["excerpt_or_support"].lower()
assert "succeeded" not in failed_page_brief["evidence"][1]["excerpt_or_support"].lower()
runner.validate_brief(failed_page_brief)

product_page = fake_fetch(200, "Our plans include a free trial and $ symbol month text.")
product_page.update({"source_url": "https://example.test/en-us/windows/", "category": "product_features"})
generic_pricing_brief = runner.make_brief(failed_case, [successful_home, product_page, successful_brand])
assert generic_pricing_brief["pricing"]["unknown"] is True
assert generic_pricing_brief["pricing"]["plans"] == []
runner.validate_brief(generic_pricing_brief)

pricing_page = fake_fetch(200, "Starter plan: $19 USD per month.")
pricing_page.update({"source_url": "https://example.test/pricing/plans", "category": "pricing_plans"})
grounded_pricing_brief = runner.make_brief(failed_case, [successful_home, pricing_page, successful_brand])
assert grounded_pricing_brief["pricing"]["unknown"] is False
assert grounded_pricing_brief["pricing"]["plans"]
assert all("$19" in plan["value"] or "19" in plan["value"] for plan in grounded_pricing_brief["pricing"]["plans"])
runner.validate_brief(grounded_pricing_brief)

# A bare starting-price sentence with no plan name is not a plan and stays unknown.
sentence_pricing_page = fake_fetch(200, "Pricing plans start at $19 USD per month.")
sentence_pricing_page.update({"source_url": "https://example.test/pricing/plans", "category": "pricing_plans"})
sentence_pricing_brief = runner.make_brief(failed_case, [successful_home, sentence_pricing_page, successful_brand])
assert sentence_pricing_brief["pricing"]["unknown"] is True
assert sentence_pricing_brief["pricing"]["plans"] == []
runner.validate_brief(sentence_pricing_brief)

markdown_429 = fake_fetch(429, "", "HTTPError")
markdown_429.update({"surface": "free_markdown", "source_url": pricing_page["source_url"], "endpoint_url": "https://md.replynodes.com/https%3A%2F%2Fexample.test%2Fpricing%2Fplans", "category": "pricing_plans"})
direct_pricing = fake_fetch(200, "Pricing plans start at $19 USD per month.", content_type="text/html; charset=utf-8")
direct_pricing.update({"surface": "free_direct_pricing", "source_url": pricing_page["source_url"], "endpoint_url": pricing_page["source_url"], "category": "pricing_plans"})
direct_pricing["attempts"] = [markdown_429, direct_pricing.copy()]
direct_pricing_brief = runner.make_brief(failed_case, [successful_home, direct_pricing, successful_brand])
assert "free_direct_pricing" in direct_pricing_brief["meta"]["capabilities_used"]
assert [call["surface"] for call in direct_pricing_brief["meta"]["tool_calls"]].count("free_direct_pricing") == 1
runner.validate_brief(direct_pricing_brief)
direct_failed = fake_fetch(None, "", "URLError", "")
direct_failed.update({"surface": "free_direct_pricing", "source_url": pricing_page["source_url"], "endpoint_url": pricing_page["source_url"], "category": "pricing_plans"})
direct_failed["attempts"] = [markdown_429, direct_failed.copy()]
direct_failed_brief = runner.make_brief(failed_case, [successful_home, direct_failed, successful_brand])
assert direct_failed_brief["pricing"]["unknown"] is True
runner.validate_brief(direct_failed_brief)

figma_pricing_page = fake_fetch(200, "Professional Monthly $16 /mo; Organization $55 /mo. Enterprise plan — contact sales.")
assert runner.extract_pricing(figma_pricing_page["text"]) is not None
assert runner.extract_pricing("Free plan") is None
assert runner.extract_pricing("<h3>Free</h3><span>$0</span><span aria-label='$6 per user/month'></span>") is not None

product_page = fake_fetch(200, "Product details and feature overview.")
product_page.update({"source_url": "https://example.test/product", "category": "product_features"})
later_pricing_page = fake_fetch(200, "Team plan: $29 USD per month.")
later_pricing_page.update({"source_url": "https://example.test/pricing/plans", "category": "pricing_plans"})
later_pricing_brief = runner.make_brief(failed_case, [successful_home, product_page, later_pricing_page, successful_brand])
assert later_pricing_brief["pricing"]["unknown"] is False
assert all(eid.startswith("selected-page-2") for eid in later_pricing_brief["pricing"]["model"]["evidence_ids"])
assert all(eid.startswith("selected-page-2") for eid in later_pricing_brief["pricing"]["plans"][0]["evidence_ids"])
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

for text in ("Contact sales for pricing.", "Pricing is not publicly available.", "No pricing information available.", "No plans offered.", "Pricing not publicly available."):
    assert runner.extract_pricing(text) is None, text

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
assert dot_discovery == [(dot_homepage, "homepage"), ("https://example.test/pricing", "pricing_plans")]
assert runner.normalized_hostname("https://example.test./pricing") == "example.test"
assert runner.normalized_hostname("https://www.example.test.:443/") == "example.test"
assert runner.normalized_hostname("https://www.example.test.") == "example.test"
assert runner.normalized_hostname("https://example.test.") == "example.test"
www_dot_port_discovery = runner.discover_candidates("https://www.example.test.:443/", "[Pricing](https://example.test.:443/pricing) [Wrong port](https://example.test.:8443/pricing)")
assert www_dot_port_discovery == [("https://www.example.test.:443/", "homepage"), ("https://example.test/pricing", "pricing_plans")]
# Canonical dedupe: locale and query variants collapse to one logical candidate.
locale_discovery = runner.discover_candidates("https://www.example.test/", "[EN](https://example.test/en-us/pricing) [FR](https://example.test/fr/pricing) [Q](https://example.test/pricing?utm_source=x)")
assert locale_discovery == [("https://www.example.test/", "homepage"), ("https://example.test/pricing", "pricing_plans")]
assert runner.canonical_url("https://www.example.test./en-GB/pricing?utm=1") == "https://example.test/pricing"
assert runner.canonical_url("https://example.test/en-us/") == "https://example.test/"
assert runner.page_category("https://example.test/product-integrations") == "integrations"
assert runner.page_category("https://example.test/en-fr/customers/hertz") == "customers_case_studies"

# deterministic extraction produces body-derived, evidence-backed claims
extracted = runner.make_brief(failed_case, [successful_home, successful_brand], [(failed_case["homepage"], "homepage")])
values = {item["value"] for item in material_claims(extracted).values() if item["value"]}
assert "Example makes public web tools." in values
assert all(value in BODY or BODY.find(value) >= 0 for value in values if value in BODY), values

prioritized = [(failed_case["homepage"], "homepage")] + [(f"https://example.test/page-{i}", "unknown") for i in range(1, 4)] + [("https://example.test/pricing", "pricing_plans")] + [(f"https://example.test/page-{i}", "unknown") for i in range(4, 11)]
selected = runner.select_candidates(prioritized)
assert len(selected) <= runner.E2E_TARGET_READS
assert selected == [(failed_case["homepage"], "homepage"), ("https://example.test/pricing", "pricing_plans"), ("https://example.test/page-1", "unknown"), ("https://example.test/page-2", "unknown")]
out_of_order = [(failed_case["homepage"], "homepage"), ("https://example.test/about", "about"), ("https://example.test/integrations", "integrations"), ("https://example.test/product", "product_features"), ("https://example.test/pricing", "pricing_plans")]
assert runner.select_candidates(out_of_order)[1:] == [("https://example.test/product", "product_features"), ("https://example.test/pricing", "pricing_plans"), ("https://example.test/integrations", "integrations"), ("https://example.test/about", "about")]
prioritized_trace = runner.candidate_trace(prioritized, {source: {"selected": True, "request_made": True} for source, _ in selected})
pricing_trace = next(item for item in prioritized_trace["selected_candidate_sequence"] if item["source_url"] == "https://example.test/pricing")
assert pricing_trace["selected"] is True and pricing_trace["request_made"] is True
many = [(failed_case["homepage"], "homepage")] + [(f"https://example.test/page-{i}", "unknown") for i in range(1, 21)]
trace = runner.candidate_trace(many, {failed_case["homepage"]: {"selected": True, "request_made": True, "retry_or_fallback_count": 0}})
assert trace["accepted_count"] == 12
candidate_13 = trace["selected_candidate_sequence"][12]
assert candidate_13["accepted"] is False
assert candidate_13["selected"] is False and candidate_13["request_made"] is False
assert trace["attempted_count"] == 13 and trace["attempted_candidate_number"] == 13
short = many[:5]
short_trace = runner.candidate_trace(short, {failed_case["homepage"]: {"selected": True, "request_made": True, "retry_or_fallback_count": 0}})
assert short_trace["hard_cap_rejection"] is None
assert short_trace["attempted_count"] == len(short) and short_trace["attempted_candidate_number"] == len(short)
print("company brief schema fixture passed (schema, claim/evidence integrity, extraction quality, pricing, and negative cases)")
PY
