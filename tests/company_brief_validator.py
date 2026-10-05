"""Deterministic validator for the checked-in company brief V2 contract."""
import datetime
import json
import re
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCHEMA_PATH = ROOT / "references/company-brief.schema.json"

MATERIAL_FIELDS = ("products", "target_market", "features", "integrations", "customers")
PAGE_CATEGORIES = ("homepage", "product_features", "pricing_plans", "integrations", "about", "docs", "customers_case_studies", "changelog_blog", "careers", "unknown")
ALWAYS_UNKNOWN_FIELDS = ("employee_count", "revenue", "funding", "icp_score", "lead_score", "probability_to_buy")


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
    for field in MATERIAL_FIELDS:
        paths.extend((f"{field}[{i}]", claim) for i, claim in enumerate(brief[field]))
    paths.append(("pricing.model", brief["pricing"]["model"]))
    paths.extend((f"pricing.plans[{i}]", claim) for i, claim in enumerate(brief["pricing"]["plans"]))
    paths.extend((f"notable_context[{i}]", claim) for i, claim in enumerate(brief.get("notable_context", [])))
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
        direct_ok = 200 <= direct["http_status"] < 300
        if "free_direct_pricing" not in capabilities or direct["operation"] != "GET" or direct["source_url"] != direct["endpoint_url"] or direct_host != homepage_host or not re.search(r"(?:^|[/_-])(pricing|plans?)(?:[/_-]|$)", urllib.parse.urlparse(direct["source_url"]).path.lower()) or (direct_ok and not direct["content_type"].lower().startswith("text/html")):
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
    _check_signals(brief, evidence_set)
    _check_unknowns(brief)
    _check_meta(brief)
    _check_goal(brief)


def _check_signals(brief, evidence_set):
    known_types = {"product_launch", "product_direction", "pricing", "partnership", "hiring", "leadership", "market_expansion", "positioning", "customer_momentum", "other"}
    for signal in brief["signals"]:
        if signal["type"] not in known_types:
            raise AssertionError("signal type outside canonical enum")
        if not set(signal["evidence_ids"]) <= evidence_set:
            raise AssertionError("dangling signal evidence")
        if signal["recency"] == "dated":
            if "published_at" not in signal:
                raise AssertionError("dated signal requires published_at")
        elif signal["recency"] == "current_observation":
            if "published_at" in signal:
                raise AssertionError("current_observation signal must omit published_at")
        else:
            raise AssertionError("signal recency outside canonical enum")


def _check_unknowns(brief):
    fields = [item["field"] for item in brief["unknowns"]]
    if len(fields) != len(set(fields)):
        raise AssertionError("unknown fields must be unique")
    for item in brief["unknowns"]:
        if not item["field"].strip() or not item["reason"].strip():
            raise AssertionError("unknowns require field and reason")


def _check_meta(brief):
    meta = brief["meta"]
    if meta["synthesis"] != "host_agent":
        raise AssertionError("synthesis owner must remain host_agent")
    default, hard = meta["page_read_budget_default"], meta["page_read_budget_hard_cap"]
    read, attempted, discovered = meta["page_read_count"], meta["pages_attempted"], meta["pages_discovered"]
    if not (read <= default <= 8):
        raise AssertionError("default page budget must bound the read count at 8")
    if not (read <= hard <= 12):
        raise AssertionError("hard page cap must bound the read count at 12")
    if read > attempted or attempted > discovered:
        raise AssertionError("page counters must be monotonic: read <= attempted <= discovered")
    if meta["partial_failure_count"] > attempted:
        raise AssertionError("partial failure count cannot exceed attempted pages")
    if read != attempted - meta["partial_failure_count"]:
        raise AssertionError("page_read_count must count successful pages only")
    total_covered = sum(item["pages_read"] for item in meta["source_coverage"])
    if total_covered != read:
        raise AssertionError("source coverage must account for every consumed page")
    for item in meta["source_coverage"]:
        if item["category"] not in PAGE_CATEGORIES:
            raise AssertionError("source coverage category outside canonical enum")
    if meta["research_goal"] is not None and "notable_context" not in brief:
        raise AssertionError("goal-aware runs require a notable_context section")


def _check_goal(brief):
    goal = brief["meta"]["research_goal"]
    if goal is None and brief.get("notable_context"):
        raise AssertionError("notable_context is only populated for goal-aware runs")


def validate_brief(brief, schema_path=SCHEMA_PATH):
    """Validate schema, claim/evidence integrity, signals, unknowns, and budget invariants."""
    check_contract(brief, schema_path=schema_path)
