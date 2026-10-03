#!/usr/bin/env bash
set -euo pipefail
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 - "$root" <<'PY'
import copy, datetime, json, re, sys
from pathlib import Path
root = Path(sys.argv[1])
schema = json.loads((root / "references/company-brief.schema.json").read_text())
fixture = json.loads((root / "tests/fixtures/company-brief.json").read_text())

def resolve(node):
    if "$ref" not in node: return node
    current = schema
    for part in node["$ref"].removeprefix("#/").split("/"): current = current[part]
    return current

def validate(value, node, path="$"):
    node = resolve(node)
    kind = node.get("type")
    kinds = kind if isinstance(kind, list) else [kind] if kind else []
    actual = "null" if value is None else "boolean" if isinstance(value, bool) else "integer" if isinstance(value, int) else "number" if isinstance(value, float) else "array" if isinstance(value, list) else "object" if isinstance(value, dict) else "string"
    if kinds and actual not in kinds: raise AssertionError(f"{path}: expected {kinds}, got {actual}")
    if "const" in node and value != node["const"]: raise AssertionError(f"{path}: const mismatch")
    if "enum" in node and value not in node["enum"]: raise AssertionError(f"{path}: enum mismatch")
    if actual == "object":
        for required in node.get("required", []):
            if required not in value: raise AssertionError(f"{path}: missing {required}")
        if node.get("additionalProperties") is False:
            unknown = set(value) - set(node.get("properties", {}))
            if unknown: raise AssertionError(f"{path}: unexpected {sorted(unknown)}")
        for key, child in node.get("properties", {}).items():
            if key in value: validate(value[key], child, f"{path}.{key}")
    if actual == "array":
        if len(value) < node.get("minItems", 0): raise AssertionError(f"{path}: too few items")
        if node.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise AssertionError(f"{path}: items must be unique")
        for i, item in enumerate(value): validate(item, node.get("items", {}), f"{path}[{i}]")
    if actual == "string":
        if len(value) < node.get("minLength", 0) or len(value) > node.get("maxLength", 10**9): raise AssertionError(f"{path}: string length")
        if "pattern" in node and not re.search(node["pattern"], value): raise AssertionError(f"{path}: pattern mismatch")
        if node.get("format") == "uri" and not re.match(r"^https://[^\s]+$", value): raise AssertionError(f"{path}: URI format")
        if node.get("format") == "date-time":
            try: datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError: raise AssertionError(f"{path}: date-time format")
    if actual in ("integer", "number") and value < node.get("minimum", value): raise AssertionError(f"{path}: below minimum")
    if actual == "integer" and value > node.get("maximum", value): raise AssertionError(f"{path}: above maximum")

validate(fixture, schema)
meta = fixture["meta"]
assert meta["page_read_count"] <= meta["page_read_budget_default"] <= 12
assert meta["page_read_count"] <= meta["page_read_budget_hard_cap"] <= 20

def material_claims(brief):
    paths = [(f"summary.{key}", brief["summary"][key]) for key in ("one_liner", "category", "positioning")]
    for field in ("products", "target_market", "features", "integrations", "recent_updates"):
        paths.extend((f"{field}[{i}]", claim) for i, claim in enumerate(brief[field]))
    paths.append(("pricing.model", brief["pricing"]["model"]))
    paths.extend((f"pricing.plans[{i}]", claim) for i, claim in enumerate(brief["pricing"]["plans"]))
    return dict(paths)

def check_contract(brief):
    validate(brief, schema)
    evidence_ids = [item["id"] for item in brief["evidence"]]
    assert len(evidence_ids) == len(set(evidence_ids)), "evidence IDs must be unique"
    evidence_set = set(evidence_ids)
    claims = material_claims(brief)
    linkage_paths = [item["claim_path"] for item in brief["claim_evidence"]]
    assert len(linkage_paths) == len(set(linkage_paths)), "claim paths must be linked once"
    assert set(linkage_paths) == set(claims), "every material claim must have exactly one linkage"
    for path, claim in claims.items():
        assert set(claim["evidence_ids"]) <= evidence_set, f"{path}: dangling claim evidence"
    for page in brief["important_pages"]:
        assert page["evidence_id"] in evidence_set, "dangling important page evidence"
    for linkage in brief["claim_evidence"]:
        assert linkage["claim_path"] in claims, "dangling claim path"
        assert set(linkage["evidence_ids"]) <= evidence_set, "dangling linkage evidence"
    pricing = brief["pricing"]
    if pricing["unknown"]:
        assert pricing["model"]["value"] is None and pricing["plans"] == [], "unknown pricing must be null/empty"
    else:
        assert pricing["model"]["value"] is not None and pricing["plans"], "observed pricing must have model/plans"

check_contract(fixture)

def must_fail(label, mutate):
    candidate = copy.deepcopy(fixture)
    mutate(candidate)
    try: check_contract(candidate)
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
check_contract(observed)
must_fail("observed pricing without model", lambda b: (b["pricing"].__setitem__("unknown", False), b["pricing"]["plans"].append({"value": "Free", "evidence_ids": ["home"]})))
must_fail("observed pricing without plans", lambda b: (b["pricing"].__setitem__("unknown", False), b["pricing"]["model"].__setitem__("value", "subscription")))

negative = copy.deepcopy(fixture)
del negative["meta"]["page_read_budget_hard_cap"]
try: validate(negative, schema)
except AssertionError: pass
else: raise AssertionError("negative schema assertion unexpectedly passed")
print("company brief schema fixture passed (schema, claim/evidence integrity, pricing, and negative cases)")
PY
