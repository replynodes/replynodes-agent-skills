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
SUPPORTED_PAGE_CATEGORIES = ("homepage", "product_features", "pricing_plans", "integrations", "about", "docs", "customers_case_studies", "changelog_blog")
ALWAYS_UNKNOWN_FIELDS = ("employee_count", "revenue", "funding", "icp_score", "lead_score", "probability_to_buy")
STOPWORDS = {"with", "that", "this", "from", "your", "their", "they", "have", "will", "into", "more", "than", "about", "other", "which", "these", "those", "been", "over", "such", "each", "most", "many", "some", "when", "what", "where", "while", "also", "using", "used"}
FILLER_PATTERNS = (
    "described in bounded", "observed in bounded", "bounded first-party text", "first-party text",
    "public company information", "response body omitted", "non-empty text", "current positioning observed",
    "public positioning is supported", "goal-relevant current positioning", "products described",
    "features described", "public users and teams", "software company.",
)


def is_filler(value):
    """True when a claim value is contract filler rather than body-derived text."""
    if not isinstance(value, str):
        return False
    low = value.strip().lower()
    if not low:
        return False
    if any(pattern in low for pattern in FILLER_PATTERNS):
        return True
    return bool(re.fullmatch(r"(?:software|technology|internet|public|general|various) company\.?", low))


def _tokens(value):
    return {token for token in re.findall(r"[a-z0-9]{4,}", value.lower()) if token not in STOPWORDS}


RAW_EXCERPT = re.compile(r"\]\(|https?://|www\.|\?\w+=|%[0-9A-Fa-f]{2}|<[a-z/][^>]*>", re.I)
CTA_TEXT = re.compile(r"^(?:get|sign|log|contact|try|learn|read|view|watch|start|book|download|see|explore|join|subscribe|talk|buy|request|schedule|apply|meet|discover|unlock)\b", re.I)
PRICE_TEXT = re.compile(r"[$€£]\s?\d|\d[\d.,]*\s?[€$£]|\b(?:USD|EUR|GBP)\b|\d[\d.,]*\s?%", re.I)
GENERIC_TEXT = re.compile(r"\b(?:logo|icon|menu|login|sign up|get started|learn more|read more|see more|view all|marketplace|ecosystem|integrations?|apps?|apis?|connectors?|faq|frequently asked questions|featured|additional|exclusive|compare features|add-ons?|clients?|partners?|customers?)\b", re.I)
PRODUCT_GENERIC = re.compile(r"\b(?:logo|icon|menu|login|sign up|get started|learn more|read more|see more|view all|marketplace|ecosystem|integrations?|faq|frequently asked questions|featured|additional|exclusive|compare features|add-ons?)\b", re.I)
ERROR_TEXT = re.compile(r"\b(?:not found|cannot be found|page not found|error while loading|access denied|something went wrong|temporarily unavailable|page you requested)\b", re.I)
ERROR_SUPPORT = re.compile(r"\b(?:unavailable|error/not-found|no claims derived|no readable content)\b", re.I)
SOCIAL_LABELS = {"facebook", "twitter", "x", "linkedin", "youtube", "instagram", "tiktok", "pinterest", "snapchat", "threads", "whatsapp", "telegram", "reddit", "discord", "twitch", "vimeo", "weibo", "wechat", "vk"}
NAME_CONNECTORS = {"of", "and", "the", "&", "de", "del", "la", "le", "van", "von", "der", "du", "den", "di"}


def _is_cta_text(value):
    return bool(CTA_TEXT.match(value.strip()))


def _looks_like_customer(value):
    v = re.sub(r"\s+", " ", str(value)).strip(" ·•|>-")
    if len(v) < 2 or len(v) > 40 or re.search(r"[.!?]$", v):
        return False
    if any(ch in v for ch in ",;|/—–"):
        return False
    words = v.split()
    if not (1 <= len(words) <= 3):
        return False
    for word in words:
        core = word.strip("&.-'’")
        if core and (core[0].isupper() or core.isupper()):
            continue
        if word.lower() in NAME_CONNECTORS:
            continue
        return False
    if v.lower() in SOCIAL_LABELS or GENERIC_TEXT.search(v) or re.search(r"\blogo\b|\bicon\b", v, re.I):
        return False
    return True


def content_quality_issues(brief):
    """Independent, field-aware content checks that reject wrong-type/noisy claims
    even when an excerpt trivially overlaps the claim text."""
    issues = []
    excerpts = {item["id"]: item["excerpt_or_support"] for item in brief["evidence"]}
    for path, item in material_claims(brief).items():
        value = item["value"]
        if value is None:
            continue
        value = str(value)
        if RAW_EXCERPT.search(value):
            issues.append(f"{path}: claim value contains raw markup/URL noise")
        if ERROR_TEXT.search(value):
            issues.append(f"{path}: claim value is error/not-found text")
        if path in ("summary.one_liner", "summary.positioning") and _is_cta_text(value):
            issues.append(f"{path}: CTA/imperative text is not positioning")
        if path.startswith("products[") and (PRICE_TEXT.search(value) or PRODUCT_GENERIC.fullmatch(value.strip()) or re.search(r"\blogo\b", value, re.I)):
            issues.append(f"{path}: product claim is not a product name")
        if path.startswith("integrations[") and (GENERIC_TEXT.search(value) or re.search(r"\blogo\b", value, re.I) or _is_cta_text(value)):
            issues.append(f"{path}: integration claim is not connector evidence")
        if path.startswith("customers[") and not _looks_like_customer(value):
            issues.append(f"{path}: customer claim is not a customer name")
        for eid in item["evidence_ids"]:
            if RAW_EXCERPT.search(str(excerpts.get(eid, ""))):
                issues.append(f"{path}: linked evidence excerpt contains raw markup/URL noise")
    seen_plans = set()
    for index, item in enumerate(brief["pricing"]["plans"]):
        value = item["value"]
        if value is None:
            continue
        value = str(value)
        key = re.sub(r"\W+", " ", value.lower()).strip()
        if key and key in seen_plans:
            issues.append(f"pricing.plans[{index}]: duplicate plan")
        seen_plans.add(key)
        if ERROR_TEXT.search(value) or len(value.split()) > 12 or value.count("—") > 1:
            issues.append(f"pricing.plans[{index}]: plan is not coherent plan evidence")
    return issues


def excerpt_supports(value, excerpt):
    if value is None or not excerpt:
        return False
    tokens = _tokens(value)
    if not tokens:
        return True
    return bool(tokens & set(re.findall(r"[a-z0-9]{4,}", excerpt.lower())))



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
    _check_claims_quality(brief)
    _check_unknown_coverage(brief)
    _check_meta(brief)
    _check_page_contribution(brief, claims)
    _check_goal(brief)


def _check_claims_quality(brief):
    """Reject filler, require meaningful text, and require evidence excerpts relevant to claims."""
    excerpts = {item["id"]: item["excerpt_or_support"] for item in brief["evidence"]}
    for path, item in material_claims(brief).items():
        value = item["value"]
        if value is None:
            continue
        if is_filler(value):
            raise AssertionError(f"{path}: filler claim text is not allowed")
        if len(value.strip()) < 2 or not re.search(r"[A-Za-z]", value):
            raise AssertionError(f"{path}: claim text is not meaningful")
        if path == "summary.category":
            if not any(len(str(excerpts.get(eid, "")).strip()) >= 8 for eid in item["evidence_ids"]):
                raise AssertionError(f"{path}: category requires a non-empty first-party source excerpt")
        elif not any(excerpt_supports(value, excerpts.get(eid, "")) for eid in item["evidence_ids"]):
            raise AssertionError(f"{path}: no linked evidence excerpt supports the claim text")
    for index, signal in enumerate(brief["signals"]):
        if is_filler(signal["summary"]):
            raise AssertionError(f"signals[{index}]: filler signal summary is not allowed")
    issues = content_quality_issues(brief)
    if issues:
        raise AssertionError(f"content quality: {issues[0]}")


def _check_unknown_coverage(brief):
    """Empty material fields and unknown pricing require an explicit unknowns entry."""
    unknown_fields = {item["field"] for item in brief["unknowns"]}
    for field in MATERIAL_FIELDS:
        if not brief[field] and field not in unknown_fields:
            raise AssertionError(f"{field}: empty material field requires an explicit unknown entry")
    if brief["pricing"]["unknown"] and "pricing" not in unknown_fields:
        raise AssertionError("unknown pricing requires an explicit pricing unknown entry")


def _check_page_contribution(brief, claims):
    contribution = brief["meta"].get("page_contribution")
    if contribution is None:
        raise AssertionError("meta.page_contribution is required to account for consumed pages")
    evidence_set = {item["id"] for item in brief["evidence"]}
    evidence_map = {item["id"]: item for item in brief["evidence"]}
    signal_paths = {f"signals[{index}]" for index in range(len(brief["signals"]))}
    notable_paths = {f"notable_context[{index}]" for index in range(len(brief.get("notable_context", [])))}
    known_paths = set(claims) | signal_paths | notable_paths
    seen = set()
    for item in contribution:
        if item["evidence_id"] not in evidence_set:
            raise AssertionError("page contribution references unknown evidence")
        if item["evidence_id"] in seen:
            raise AssertionError("page contribution evidence must be unique")
        seen.add(item["evidence_id"])
        if item["category"] not in PAGE_CATEGORIES:
            raise AssertionError("page contribution category outside canonical enum")
        if not item["read"] and item["claims"]:
            raise AssertionError("unread page contribution must not list claims")
        if item["read"] and item["category"] in SUPPORTED_PAGE_CATEGORIES and not item["claims"]:
            excerpt = evidence_map.get(item["evidence_id"], {}).get("excerpt_or_support", "")
            if len(str(excerpt).strip()) >= 8 and not is_filler(str(excerpt)) and not ERROR_SUPPORT.search(str(excerpt)):
                raise AssertionError("read page with a supported category must contribute at least one claim")
        for claim_path in item["claims"]:
            if claim_path not in known_paths:
                raise AssertionError(f"page contribution references unknown claim path {claim_path}")


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
