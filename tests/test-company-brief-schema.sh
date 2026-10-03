#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 - "$root" <<'PY'
import copy, json, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "tests"))
from company_brief_validator import check_contract, validate_schema

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
print("company brief schema fixture passed (schema, claim/evidence integrity, pricing, and negative cases)")
PY
