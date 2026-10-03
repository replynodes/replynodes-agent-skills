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
evidence_ids = {item["id"] for item in fixture["evidence"]}
for item in fixture["claim_evidence"]: assert set(item["evidence_ids"]) <= evidence_ids
negative = copy.deepcopy(fixture)
del negative["meta"]["page_read_budget_hard_cap"]
try: validate(negative, schema)
except AssertionError: pass
else: raise AssertionError("negative schema assertion unexpectedly passed")
print("company brief schema fixture passed (including budget and evidence linkage checks)")
PY
