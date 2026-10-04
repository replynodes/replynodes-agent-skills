"""Deterministic validator for the checked-in company brief contract."""
import datetime
import json
import re
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "references/company-brief.schema.json"


def load_schema(schema_path=SCHEMA_PATH):
    return json.loads(Path(schema_path).read_text(encoding="utf-8"))


def _resolve(node, schema):
    if "$ref" not in node:
        return node
    current = schema
    for part in node["$ref"].removeprefix("#/").split("/"):
        current = current[part]
    return current


def validate_schema(value, schema=None, node=None, path="$", schema_path=SCHEMA_PATH):
    schema = load_schema(schema_path) if schema is None else schema
    node = _resolve(schema if node is None else node, schema)
    kind = node.get("type")
    kinds = kind if isinstance(kind, list) else [kind] if kind else []
    actual = (
        "null" if value is None else
        "boolean" if isinstance(value, bool) else
        "integer" if isinstance(value, int) else
        "number" if isinstance(value, float) else
        "array" if isinstance(value, list) else
        "object" if isinstance(value, dict) else "string"
    )
    if kinds and actual not in kinds:
        raise AssertionError(f"{path}: expected {kinds}, got {actual}")
    if "const" in node and value != node["const"]:
        raise AssertionError(f"{path}: const mismatch")
    if "enum" in node and value not in node["enum"]:
        raise AssertionError(f"{path}: enum mismatch")
    if actual == "object":
        for required in node.get("required", []):
            if required not in value:
                raise AssertionError(f"{path}: missing {required}")
        if node.get("additionalProperties") is False:
            unknown = set(value) - set(node.get("properties", {}))
            if unknown:
                raise AssertionError(f"{path}: unexpected {sorted(unknown)}")
        for key, child in node.get("properties", {}).items():
            if key in value:
                validate_schema(value[key], schema, child, f"{path}.{key}")
    if actual == "array":
        if len(value) < node.get("minItems", 0):
            raise AssertionError(f"{path}: too few items")
        if node.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise AssertionError(f"{path}: items must be unique")
        for i, item in enumerate(value):
            validate_schema(item, schema, node.get("items", {}), f"{path}[{i}]")
    if actual == "string":
        if len(value) < node.get("minLength", 0) or len(value) > node.get("maxLength", 10**9):
            raise AssertionError(f"{path}: string length")
        if "pattern" in node and not re.search(node["pattern"], value):
            raise AssertionError(f"{path}: pattern mismatch")
        if node.get("format") == "uri" and not re.match(r"^https://[^\s]+$", value):
            raise AssertionError(f"{path}: URI format")
        if node.get("format") == "date-time":
            try:
                datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise AssertionError(f"{path}: date-time format")
    if actual in ("integer", "number") and value < node.get("minimum", value):
        raise AssertionError(f"{path}: below minimum")
    if actual == "integer" and value > node.get("maximum", value):
        raise AssertionError(f"{path}: above maximum")


def material_claims(brief):
    paths = [(f"summary.{key}", brief["summary"][key]) for key in ("one_liner", "category", "positioning")]
    for field in ("products", "target_market", "features", "integrations", "recent_updates"):
        paths.extend((f"{field}[{i}]", claim) for i, claim in enumerate(brief[field]))
    paths.append(("pricing.model", brief["pricing"]["model"]))
    paths.extend((f"pricing.plans[{i}]", claim) for i, claim in enumerate(brief["pricing"]["plans"]))
    return dict(paths)


def check_contract(brief, schema=None, schema_path=SCHEMA_PATH):
    validate_schema(brief, schema=schema, schema_path=schema_path)
    capabilities = set(brief["meta"]["capabilities_used"])
    discovery_calls = [call for call in brief["meta"]["tool_calls"] if call["surface"] == "free_homepage_discovery"]
    if "free_homepage_discovery" not in capabilities or len(discovery_calls) != 1:
        raise AssertionError("homepage discovery requires exactly one declared and recorded call")
    discovery_call = discovery_calls[0]
    if discovery_call["operation"] != "GET" or discovery_call["source_url"] != brief["company"]["homepage_url"] or discovery_call["endpoint_url"] != brief["company"]["homepage_url"]:
        raise AssertionError("homepage discovery call must GET the declared homepage")
    direct_calls = [call for call in brief["meta"]["tool_calls"] if call["surface"] == "free_direct_pricing"]
    if len(direct_calls) > 1:
        raise AssertionError("at most one direct pricing fallback is allowed")
    if direct_calls:
        direct = direct_calls[0]
        homepage_host = urllib.parse.urlparse(brief["company"]["homepage_url"]).hostname.removeprefix("www.").rstrip(".").lower()
        direct_host = urllib.parse.urlparse(direct["source_url"]).hostname
        if direct_host:
            direct_host = direct_host.removeprefix("www.").rstrip(".").lower()
        if "free_direct_pricing" not in capabilities or direct["operation"] != "GET" or direct["source_url"] != direct["endpoint_url"] or direct_host != homepage_host or not re.search(r"(?:^|[/_-])(pricing|plans?)(?:[/_-]|$)", urllib.parse.urlparse(direct["source_url"]).path.lower()) or not direct["content_type"].lower().startswith("text/html"):
            raise AssertionError("direct pricing fallback must use one exact first-party pricing URL")
        markdown = [call for call in brief["meta"]["tool_calls"] if call["surface"] == "free_markdown" and call["source_url"] == direct["source_url"]]
        if len(markdown) != 1 or markdown[0]["http_status"] != 429:
            raise AssertionError("direct pricing fallback requires the selected Markdown request to be HTTP 429")
    for call in brief["meta"]["tool_calls"]:
        if call["endpoint_url"] != call["source_url"] and call["surface"] != "free_markdown":
            raise AssertionError("only Markdown may use a transformed endpoint URL")
    evidence_ids = [item["id"] for item in brief["evidence"]]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise AssertionError("evidence IDs must be unique")
    evidence_set = set(evidence_ids)
    claims = material_claims(brief)
    linkage_paths = [item["claim_path"] for item in brief["claim_evidence"]]
    if len(linkage_paths) != len(set(linkage_paths)):
        raise AssertionError("claim paths must be linked once")
    if set(linkage_paths) != set(claims):
        raise AssertionError("every material claim must have exactly one linkage")
    for path, claim in claims.items():
        if not set(claim["evidence_ids"]) <= evidence_set:
            raise AssertionError(f"{path}: dangling claim evidence")
    for page in brief["important_pages"]:
        if page["evidence_id"] not in evidence_set:
            raise AssertionError("dangling important page evidence")
    for linkage in brief["claim_evidence"]:
        if linkage["claim_path"] not in claims:
            raise AssertionError("dangling claim path")
        if not set(linkage["evidence_ids"]) <= evidence_set:
            raise AssertionError("dangling linkage evidence")
    pricing = brief["pricing"]
    if pricing["unknown"]:
        if pricing["model"]["value"] is not None or pricing["plans"] != []:
            raise AssertionError("unknown pricing must be null/empty")
    elif pricing["model"]["value"] is None or not pricing["plans"]:
        raise AssertionError("observed pricing must have model/plans")


def validate_brief(brief, schema_path=SCHEMA_PATH):
    """Validate schema, claim/evidence integrity, and pricing invariants."""
    check_contract(brief, schema_path=schema_path)
