#!/usr/bin/env python3
"""Deterministic V2 scenario coverage: sparse, partial failure, goal-aware."""
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

home = fetch(200, "Example public product homepage", case["homepage"])
brand = fetch(200, "Example identity", "https://brand.replynodes.com/example.test", "application/json", "free_brand")
discovery = fetch(200, "<a href='/pricing'>Pricing</a>", case["homepage"], "text/html", "free_homepage_discovery")
brief = runner.make_brief(case, [home, brand], [(case["homepage"], "homepage")], discovery)
runner.validate_brief(brief)
assert brief["meta"]["page_read_count"] == 1
assert brief["pricing"]["unknown"] is True

failed_home = fetch(503, "", case["homepage"])
partial = runner.make_brief(case, [failed_home, brand], [(case["homepage"], "homepage")], discovery)
runner.validate_brief(partial)
assert partial["meta"]["partial_failure_count"] == 1
from company_brief_validator import material_claims
assert all(item["value"] is None for item in material_claims(partial).values())

goal = runner.make_brief(case, [home, brand], [(case["homepage"], "homepage")], discovery, research_goal="understand developer platform positioning")
runner.validate_brief(goal)
assert goal["meta"]["research_goal"]
assert goal["notable_context"]
assert goal["summary"] == brief["summary"]
assert goal["products"] == brief["products"]
assert goal["pricing"] == brief["pricing"]
print("V2 scenarios passed: sparse, partial_failure, goal_aware")
