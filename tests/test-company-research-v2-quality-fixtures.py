#!/usr/bin/env python3
"""Regression fixtures for the phase-2 content-quality findings.

Each fixture reproduces one blocking finding from the independent review and
asserts the conservative, fail-closed behavior. Extraction must keep real
intelligence while rejecting wrong-type/noisy claims instead of emitting them as
explicit-looking claims.
"""
import copy
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from company_brief_validator import content_quality_issues, excerpt_supports

p = Path(__file__).with_name("run-company-research-keyless-e2e.py")
spec = importlib.util.spec_from_file_location("runner", p)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

CASE = {"domain": "example.test", "name": "Example", "homepage": "https://example.test/"}


def fetch(status, text, source="https://example.test/", content_type="text/markdown", surface="free_markdown", category=None):
    item = {"status": status, "text": text, "source_url": source, "endpoint_url": source,
            "content_type": content_type, "error": None if status == 200 else "HTTPError",
            "surface": surface, "attempts": []}
    if category:
        item["category"] = category
    return item


BRAND = fetch(200, "Brand identity", "https://brand.replynodes.com/example.test", "application/json", "free_brand")


def brief_for(body, category=None, homepage="https://example.test/", name="Example"):
    case = {"domain": "example.test", "name": name, "homepage": homepage}
    home = fetch(200, body, homepage, category=category)
    return runner.make_brief(case, [home, BRAND], [(homepage, category or "homepage")])


# --- Finding 1: benchmark is no longer false-green from token overlap alone --------
base = brief_for("# Example makes public web tools.\n\n## Build dashboards\n\nConnect Example to Slack to sync reporting across teams.\n")
assert not content_quality_issues(base)
tampered = copy.deepcopy(base)
tampered["products"][0]["value"] = "Stripe logo"                      # wrong-type claim
for ev in tampered["evidence"]:                                        # excerpt == claim -> overlap passes
    if ev["id"] in tampered["products"][0]["evidence_ids"]:
        ev["excerpt_or_support"] = "Stripe logo"
assert content_quality_issues(tampered), "overlap-only content must still be rejected"
assert runner.benchmark_row(tampered)["quality_pass"] is False, "benchmark must not false-green on overlap"

cta = copy.deepcopy(base)
cta["summary"]["positioning"]["value"] = "Get Loom for free"
for ev in cta["evidence"]:
    if ev["id"] in cta["summary"]["positioning"]["evidence_ids"]:
        ev["excerpt_or_support"] = "Get Loom for free"
assert any("CTA" in issue for issue in content_quality_issues(cta))
assert runner.benchmark_row(cta)["quality_pass"] is False

# --- Finding 2: customers only from explicit customer context ----------------------
microsoft = brief_for(
    "# Groß denken, leicht reisen\n\n"
    "![Ein Microsoft Teams-Videoanruf.](https://cdn.example/card.png)\n\n"
    "![Facebook](https://cdn.example/fb.png)\n![LinkedIn](https://cdn.example/li.png)\n"
    "![Youtube](https://cdn.example/yt.png)\n![Instagram](https://cdn.example/ig.png)\n",
    name="Microsoft",
)
assert microsoft["customers"] == [], microsoft["customers"]
assert any(u["field"] == "customers" for u in microsoft["unknowns"])

cued = brief_for(
    "# Acme makes tools for teams.\n\n"
    "## Millions of teams call Acme home\n\n"
    "![Duolingo](https://cdn.example/duolingo.png)\n![Gartner](https://cdn.example/gartner.png)\n",
    name="Acme",
)
assert "Duolingo" in [c["value"] for c in cued["customers"]]
assert all(runner.looks_like_customer_name(c["value"], "Acme") for c in cued["customers"])
twilio_logo_body = "# Twilio\n\n## Customers\n\n![Ibm.Png](https://cdn.example/Ibm.Png)\n![Toyota.jpg](https://cdn.example/Toyota.jpg)\n"
twilio_logo = brief_for(twilio_logo_body, name="Twilio")
assert twilio_logo["customers"] == [], twilio_logo["customers"]

# --- Finding 3: integrations need explicit connector evidence, not logo alts -------
integrations_body = (
    "# Stripe logo\n\n"
    "## Integrations and marketplace\n\n"
    "- Jira Service Desk\n- Confluence\n- GitHub\n- Upwork\n"
)
blocks, alts = runner.block_units(integrations_body)
alts = alts + ["Stripe logo", "Facebook"]
values = runner.extract_integrations(blocks, alts, "integrations", "Stripe", True)
assert "Stripe logo" not in values and not any("stripe" in v.lower() for v in values)
assert "Facebook" not in values
assert {"Jira Service Desk", "Confluence", "GitHub", "Upwork"} <= set(values), values

# --- Finding 4: pricing plans are coherent, deduped, and never raw sentences -------
vercel = "## Hobby\n\n$0 /mo.\n\n## Pro\n\n$20 /mo.\n\n## Enterprise Custom\n"
plan = runner.extract_pricing(vercel)
assert plan is not None
names = {v.split(" — ")[0] for v, _ in plan[2]}
assert names == {"Hobby", "Pro"}, names
assert not any("Enterprise" in v for v, _ in plan[2])
assert not any("$4" in v for v, _ in plan[2])

github = ("## Free\n\n### $ 0 USD per month\n\n## Team\n\n### $ 4 USD per user/month\n\n"
          "## Enterprise\n\n### $ 21 USD per user/month\n\n- Unlimited $0 spend limit\n")
plan = runner.extract_pricing(github)
values = [v for v, _ in plan[2]]
assert len({v.lower() for v in values}) == len(values), values
assert not any("unlimited" in v.lower() for v in values), values
assert sum(v.startswith("Enterprise") for v in values) == 1, values

assert runner.extract_pricing("Starts at $0.0002/1k characters for conversation ingestion.") is None
assert runner.extract_pricing("Pricing plans start at $19 USD per month.") is None
assert runner.extract_pricing("## Custom\n") is None
assert runner.extract_pricing("## Enterprise\n\nContact sales for pricing.\n") is None
twilio = brief_for("# Twilio\n\nStarts at $0.0002/1k characters for conversation ingestion.\n",
                   category="pricing_plans")
assert twilio["pricing"]["unknown"] is True

# --- Finding 5: error/not-found bodies are not signals or pricing ------------------
notfound = "We are sorry, the page you requested cannot be found."
assert runner.is_error_page(notfound)
assert runner.extract_pricing(notfound) is None
assert runner.extract_signals(runner.block_units(notfound)[0], runner.clean_block(notfound), "pricing_plans", "x") == []
error_brief = brief_for(notfound, category="pricing_plans")
assert error_brief["pricing"]["unknown"] is True
assert not any(notfound in s["summary"] for s in error_brief["signals"])

# --- Finding 6: positioning rejects CTA/imperative/signup text ---------------------
cta_blocks, _ = runner.block_units("# Get Loom for free\n\nLoom is a video messaging platform for teams.\n")
positioning = runner.extract_positioning(cta_blocks, None, "Loom")
assert positioning == "Loom is a video messaging platform for teams.", positioning
only_cta, _ = runner.block_units("Get Loom for free\n")
assert runner.extract_positioning(only_cta, None, "Loom") is None
product_blocks, _ = runner.block_units("## Enable any billing model\n## Automate your path to production\n## Powering businesses of all sizes\n## Atlas Payments\n")
assert "Enable any billing model" not in runner.extract_products(product_blocks, "Stripe")
assert "Automate your path to production" not in runner.extract_products(product_blocks, "GitHub")
assert "Powering businesses of all sizes" not in runner.extract_products(product_blocks, "Stripe")
assert "Atlas Payments" in runner.extract_products(product_blocks, "Example")
legit_blocks, _ = runner.block_units("## Power BI\n## Power Platform\n## Embedded Payments\n## Streamline Ops\n")
legit_products = runner.extract_products(legit_blocks, "Example")
assert {"Power BI", "Power Platform", "Embedded Payments", "Streamline Ops"}.issubset(set(legit_products)), legit_products
assert any("plan is not coherent" in issue for issue in content_quality_issues({**copy.deepcopy(base), "pricing": {**copy.deepcopy(base["pricing"]), "unknown": False, "plans": [{"value": "Enterprise — Custom", "evidence_ids": []}]}}))

# --- Finding 7: excerpts are normalized/auditable -----------------------------------
cleaned = runner.normalize_excerpt("![Cover](https://x/y.png) Hello [World](https://a.b/c) <b>bold</b>")
assert "http" not in cleaned and "](" not in cleaned and "<b>" not in cleaned, cleaned
assert "Hello World bold" in cleaned, cleaned
bad = copy.deepcopy(base)
for ev in bad["evidence"]:
    if ev["id"] in bad["products"][0]["evidence_ids"]:
        ev["excerpt_or_support"] = "[Read more](https://example.test/x?utm=1)"
assert any("excerpt" in issue for issue in content_quality_issues(bad))
assert runner.benchmark_row(bad)["criteria"]["excerpt_noise_free"] is False

# --- Finding 8: adjacent sibling text nodes keep token boundaries ------------------
# HTML text nodes that are siblings with an inline element between them used to fuse
# into one token (`MCP Registry` + `Integrate external tools` -> `RegistryIntegrate`),
# which made an otherwise-grounded integration claim fail its evidence token check.
adjacent = "<div><span>MCP Registry</span><span>Integrate external tools</span></div>"
adjacent_text = runner.html_to_text(adjacent)
assert "MCP Registry" in adjacent_text and "Integrate external tools" in adjacent_text, adjacent_text
assert "RegistryIntegrate" not in adjacent_text, adjacent_text
assert excerpt_supports("MCP Registry", adjacent_text), adjacent_text
assert excerpt_supports("Integrate external tools", adjacent_text), adjacent_text

# Control: legitimate inline formatting/words keep the author's explicit boundaries.
assert runner.html_to_text("<p>Hello <b>world</b> today</p>").strip() == "Hello world today"
assert runner.html_to_text("<p>Deploy your <em>apps</em> fast</p>").strip() == "Deploy your apps fast"
assert runner.html_to_text("<span>Acme</span> <span>Inc</span>").strip() == "Acme Inc"
assert runner.html_to_text("<h2>Build dashboards</h2><p>Track metrics.</p>").strip() == "## Build dashboards\n\nTrack metrics."

print("quality fixtures passed: benchmark_false_green, customers_context, integrations_evidence, "
      "pricing_coherence, error_page, positioning_cta, excerpt_normalization, text_node_boundaries")
