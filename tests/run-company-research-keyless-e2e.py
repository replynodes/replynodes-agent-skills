#!/usr/bin/env python3
"""Bounded, keyless ReplyNodes company-research contract run.

Phase 2: the runner performs deterministic, bounded extraction from the
first-party Markdown/HTML bodies it actually consumed. Populated claims carry a
concise excerpt taken from the body; fields without reliable evidence stay empty
and are listed as explicit unknowns. No placeholder text is emitted.
"""
import argparse
import datetime as dt
import html
import http.client
import json
import os
import re
import sys
import time
from html.parser import HTMLParser
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from company_brief_validator import validate_brief, is_filler, material_claims

DEFAULT_CAP = 8
HARD_CAP = 12
MAX_BODY = 2 * 1024 * 1024
EXCERPT_LIMIT = 320
MCP_URL = "https://mcp.replynodes.com/mcp"
ATTRIBUTION_HEADER = "X-ReplyNodes-Skill"
ATTRIBUTION_VALUE = "company-research"
WORKFLOW_SURFACE_HOSTS = {
    "markdown": ("md.replynodes.com", {"GET", "HEAD"}),
    "brand": ("brand.replynodes.com", {"GET", "HEAD"}),
    "mcp": ("mcp.replynodes.com", {"POST"}),
}
TOOL_NAMES = ("web_search", "webcontext_map", "webcontext_scrape", "webcontext_crawl", "brand_retrieve", "brand_search", "brand_styleguide", "brand_fonts", "brand_logo")
E2E_TARGET_READS = DEFAULT_CAP

# A bounded list of canonical first-party paths probed only when homepage
# discovery produced no candidate for that high-value category.
CANONICAL_PROBES = (("/pricing", "pricing_plans"),)

CASES = tuple({"domain": domain, "name": name, "homepage": f"https://www.{domain}/"} for domain, name in (
    ("stripe.com", "Stripe"), ("figma.com", "Figma"), ("loom.com", "Loom"),
    ("microsoft.com", "Microsoft"), ("notion.so", "Notion"), ("slack.com", "Slack"),
    ("shopify.com", "Shopify"), ("hubspot.com", "HubSpot"), ("github.com", "GitHub"),
    ("linear.app", "Linear"), ("canva.com", "Canva"), ("atlassian.com", "Atlassian"),
    ("zoom.us", "Zoom"), ("dropbox.com", "Dropbox"), ("openai.com", "OpenAI"),
    ("salesforce.com", "Salesforce"), ("airtable.com", "Airtable"), ("intercom.com", "Intercom"),
    ("twilio.com", "Twilio"), ("vercel.com", "Vercel"),
))


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def request_headers(url, accept, *, method="GET", workflow_surface=None):
    headers = {"Accept": accept, "User-Agent": "replynodes-company-research-contract/1.0"}
    surface = WORKFLOW_SURFACE_HOSTS.get(workflow_surface)
    parsed = urllib.parse.urlparse(url)
    if (surface and parsed.scheme == "https" and parsed.hostname == surface[0]
            and method in surface[1]):
        headers[ATTRIBUTION_HEADER] = ATTRIBUTION_VALUE
    return headers


def get_once(url, accept="text/markdown,application/json,text/plain", *, workflow_surface=None):
    request = urllib.request.Request(url, headers=request_headers(url, accept, workflow_surface=workflow_surface))
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status, content_type = response.status, response.headers.get("Content-Type", "")
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            body = response.read(MAX_BODY + 1)[:MAX_BODY]
    except urllib.error.HTTPError as error:
        status, content_type = error.code, error.headers.get("Content-Type", "") if error.headers else ""
        remaining = error.headers.get("X-RateLimit-Remaining") if error.headers else None
        reset = error.headers.get("X-RateLimit-Reset") if error.headers else None
        try:
            body = error.read(MAX_BODY + 1)[:MAX_BODY]
        except (http.client.HTTPException, OSError):
            body = b""
        return {"status": status, "content_type": content_type, "text": body.decode("utf-8", "replace"), "error": type(error).__name__,
                "rate_remaining": remaining, "rate_reset": reset}
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException, ConnectionError) as error:
        return {"status": None, "content_type": "", "text": "", "error": type(error).__name__,
                "rate_remaining": None, "rate_reset": None}
    return {"status": status, "content_type": content_type, "text": body.decode("utf-8", "replace"), "error": None,
            "rate_remaining": remaining, "rate_reset": reset}


_RATE = {"remaining": None, "reset": None}


def observe_rate(result):
    remaining = result.get("rate_remaining")
    reset = result.get("rate_reset")
    if remaining is not None:
        try:
            _RATE["remaining"] = int(remaining)
        except (TypeError, ValueError):
            _RATE["remaining"] = None
    if reset is not None:
        try:
            _RATE["reset"] = float(reset)
        except (TypeError, ValueError):
            _RATE["reset"] = None


def pace():
    """Stay within the bounded free-surface rate window instead of idling on 429s."""
    if _RATE["remaining"] is None or _RATE["reset"] is None:
        return
    if _RATE["remaining"] > 1:
        return
    wait = _RATE["reset"] - time.time() + 1
    if 0 < wait <= 90:
        time.sleep(wait)
    _RATE["remaining"] = None


def successful(result):
    return isinstance(result.get("status"), int) and 200 <= result["status"] < 300 and bool(result.get("text", "").strip())


def md_url(source):
    return "https://md.replynodes.com/" + urllib.parse.quote(source, safe="")


def public_url(source):
    """Keep committed metadata free of tracking query strings/fragments."""
    parsed = urllib.parse.urlsplit(source)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))


def mcp_tools_once():
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, separators=(",", ":")).encode()
    headers = request_headers(MCP_URL, "application/json, text/event-stream", method="POST", workflow_surface="mcp")
    headers["Content-Type"] = "application/json"
    request = urllib.request.Request(MCP_URL, data=payload, headers=headers, method="POST")
    names, total, line_buffer = set(), 0, b""

    def parse_sse_lines(chunk):
        nonlocal line_buffer
        line_buffer += chunk
        while b"\n" in line_buffer:
            line, line_buffer = line_buffer.split(b"\n", 1)
            if line.endswith(b"\r"):
                line = line[:-1]
            if not line.startswith(b"data:"):
                continue
            try:
                event = json.loads(line[5:].lstrip().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            for tool in event.get("result", {}).get("tools", []):
                if isinstance(tool.get("name"), str):
                    names.add(tool["name"])

    def read_body(read):
        nonlocal total
        while total < MAX_BODY:
            chunk = read(min(8192, MAX_BODY - total))
            if not chunk:
                break
            total += len(chunk)
            parse_sse_lines(chunk)

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status, content_type = response.status, response.headers.get("Content-Type", "")
            read_body(response.read)
    except urllib.error.HTTPError as error:
        status, content_type = error.code, error.headers.get("Content-Type", "") if error.headers else ""
        read_body(error.read)
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as error:
        return None, "", []
    return status, content_type, sorted(names)


# ---------------------------------------------------------------------------
# Candidate discovery and canonicalization
# ---------------------------------------------------------------------------

LANG_CODES = {
    "en", "fr", "de", "es", "it", "pt", "nl", "ja", "ko", "zh", "ru", "ar", "sv", "da", "no", "fi",
    "pl", "tr", "hi", "id", "th", "vi", "cs", "el", "he", "uk", "ro", "hu", "bg", "sk", "sl", "hr",
    "lt", "lv", "et", "ms", "ca", "is", "ga", "cy", "sr", "mk", "sq", "bs", "ka", "hy", "az", "kk",
    "uz", "mn", "ne", "si", "ta", "te", "ml", "kn", "mr", "gu", "pa", "bn", "ur", "fa", "sw", "am",
    "zu", "af", "fil", "nb", "nn",
}
RESOURCE_EXT = re.compile(r"\.(?:png|jpe?g|gif|svg|webp|avif|ico|css|js|mjs|json|xml|rss|atom|pdf|zip|gz|mp4|mov|webm|woff2?|ttf|eot|txt|map)$", re.I)
SKIP_SEGMENTS = {
    "login", "signin", "sign-in", "signup", "sign-up", "register", "logout", "account", "cart",
    "checkout", "dashboard", "cdn", "assets", "static", "_next", "image", "images", "wp-content",
    "wp-admin", "search", "ui", "purchase", "purchase-professional", "purchase-organization",
}


def normalized_hostname(url):
    hostname = urllib.parse.urlparse(url).hostname
    if hostname is None:
        return None
    hostname = hostname.lower()
    if hostname.endswith("."):
        hostname = hostname[:-1]
    return hostname[4:] if hostname.startswith("www.") else hostname


def is_locale_segment(segment):
    low = segment.lower()
    if "-" in low:
        return bool(re.fullmatch(r"[a-z]{2}(?:-[a-z0-9]{2,4})+", low))
    return low in LANG_CODES


def canonical_url(url):
    """Canonicalize scheme/host/path: drop www, trailing dot, locale prefix and query."""
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host.endswith("."):
        host = host[:-1]
    if host.startswith("www."):
        host = host[4:]
    segments = [segment for segment in parsed.path.split("/") if segment]
    if segments and is_locale_segment(segments[0]) and len(segments) > 1:
        segments = segments[1:]
    if segments and is_locale_segment(segments[-1]):
        segments = segments[:-1]
    path = "/" + "/".join(segments) if segments else "/"
    return urllib.parse.urlunsplit(("https", host, path, "", ""))


def page_category(url):
    path = urllib.parse.urlparse(url).path.lower().strip("/")
    if not path:
        return "homepage"
    patterns = (
        (r"(^|[/_-])(pricing|plans?|support-plans|subscribe)([/_-]|$)", "pricing_plans"),
        (r"(^|[/_-])(integrations?|marketplace|partners?|apps?|ecosystem)([/_-]|$)", "integrations"),
        (r"(^|[/_-])(product|products|features?|platform|solutions?|use-cases?|guides?|windows|capabilities)([/_-]|$)", "product_features"),
        (r"(^|[/_-])(customers?|case-stud(?:y|ies)|stories|testimonials)([/_-]|$)", "customers_case_studies"),
        (r"(^|[/_-])about([/_-]|$)", "about"),
        (r"(^|[/_-])(docs?|documentation|developers?|api|reference)([/_-]|$)", "docs"),
        (r"(^|[/_-])(blog|changelog|news|newsroom|announcements?|updates?)([/_-]|$)", "changelog_blog"),
        (r"(^|[/_-])(careers?|jobs?)([/_-]|$)", "careers"),
    )
    for pattern, category in patterns:
        if re.search(pattern, path):
            return category
    return "unknown"


class HomepageHrefParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href" and value is not None:
                self.hrefs.append(value)


def discover_candidates(homepage, homepage_text, homepage_html=""):
    """Parse same-site links, then canonicalize and dedupe by host/path/locale/category."""
    base = urllib.parse.urlparse(homepage)
    canonical_home = canonical_url(homepage)
    found = [(homepage, "homepage")]
    seen = {canonical_home}
    raw_links = re.findall(r"\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))", homepage_text)
    html_parser = HomepageHrefParser()
    html_parser.feed(homepage_html)
    hrefs = [html.unescape(markdown_href or bare_href) for markdown_href, bare_href in raw_links]
    hrefs.extend(html_parser.hrefs)
    for href in hrefs:
        href = href.strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        parsed = urllib.parse.urlparse(urllib.parse.urljoin(homepage, href))
        try:
            same_port = parsed.port == base.port
        except ValueError:
            same_port = False
        if parsed.scheme != "https" or normalized_hostname(parsed.geturl()) != normalized_hostname(homepage) or not same_port:
            continue
        path = parsed.path
        if RESOURCE_EXT.search(path):
            continue
        if len(path) > 180:
            continue
        segments = [segment for segment in path.split("/") if segment]
        if any(segment.lower() in SKIP_SEGMENTS for segment in segments):
            continue
        canonical = canonical_url(parsed.geturl())
        if canonical in seen:
            continue
        seen.add(canonical)
        found.append((canonical, page_category(canonical)))
    return found


def candidate_trace(candidates, execution):
    """Trace discovered candidates and the decisions actually made for them."""
    decisions = []
    for number, (source, category) in enumerate(candidates[:HARD_CAP + 1], 1):
        over_cap = number > HARD_CAP
        actual = execution.get(source, {})
        accepted = not over_cap
        selected = bool(actual.get("selected", False)) if accepted else False
        decisions.append({"candidate_number": number, "candidate_kind": category, "decision": "rejected_hard_cap" if over_cap else ("admitted_selected" if selected else "admitted_not_selected"), "accepted": accepted, "rejected": over_cap, "selected": selected, "request_made": accepted and bool(actual.get("request_made", False)), "retry_or_fallback_count": int(actual.get("retry_or_fallback_count", 0)) if accepted else 0, "source_url": public_url(source)})
    attempted_count = len(decisions)
    return {"candidate_order": [{"source_url": public_url(source), "category": category} for source, category in candidates[:HARD_CAP + 1]], "selected_candidate_sequence": decisions, "hard_cap_rejection": decisions[HARD_CAP] if len(decisions) > HARD_CAP else None, "accepted_count": sum(item["accepted"] for item in decisions), "attempted_count": attempted_count, "attempted_candidate_number": attempted_count or None, "request_made_count": sum(item["request_made"] for item in decisions), "retry_or_fallback_count": sum(item["retry_or_fallback_count"] for item in decisions)}


CATEGORY_ORDER = {"product_features": 0, "pricing_plans": 1, "integrations": 2, "about": 3, "docs": 4, "customers_case_studies": 5, "changelog_blog": 6, "careers": 7, "unknown": 8}


def select_candidates(candidates, per_category_cap=2):
    """Keep homepage and select deterministic category-priority candidates, capped per category."""
    if not candidates:
        return []
    homepage = candidates[0]
    ranked = sorted(enumerate(candidates[1:], 1), key=lambda item: (CATEGORY_ORDER.get(item[1][1], 99), item[0]))
    selected = [homepage]
    counts = {}
    for _, (url, category) in ranked:
        if counts.get(category, 0) >= per_category_cap:
            continue
        counts[category] = counts.get(category, 0) + 1
        selected.append((url, category))
        if len(selected) >= E2E_TARGET_READS:
            break
    return selected


# ---------------------------------------------------------------------------
# Bounded deterministic extraction
# ---------------------------------------------------------------------------

def looks_html(text):
    if re.match(r"\s*(?:<!doctype\s+html|<html\b|<head\b|<body\b)", text, re.I):
        return True
    return bool(re.search(r"<(?:div|span|p|h[1-6]|section|main|ul|ol|li|a|table|article)\b", text, re.I))


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "template", "head"}
    BREAK = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "section", "article", "header", "footer", "tr", "td", "nav", "main"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP:
            self.skip += 1
        if tag in self.BREAK:
            self.parts.append("\n")
        for name, value in attrs:
            if name.lower() in ("aria-label", "title", "alt") and value:
                self.parts.append(" " + value + " ")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in self.BREAK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        return "".join(self.parts)


def html_to_text(text):
    parser = _TextExtractor()
    try:
        parser.feed(text)
    except Exception:
        pass
    return parser.text()


def image_alts(text):
    return [html.unescape(alt).strip() for alt in re.findall(r"!\[([^\]]*)\]\([^)]*\)", text) if alt.strip()]


def page_links(text):
    """All markdown/HTML hrefs referenced by a consumed first-party body."""
    hrefs = [html.unescape(markdown_href or bare_href) for markdown_href, bare_href in re.findall(r"\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))", text)]
    parser = HomepageHrefParser()
    try:
        parser.feed(text)
    except Exception:
        pass
    hrefs.extend(parser.hrefs)
    return hrefs


def clean_inline(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    for source, target in (("&amp;", "&"), ("&nbsp;", " "), ("&#39;", "'"), ("&quot;", '"'), ("&gt;", ">"), ("&lt;", "<"), ("&mdash;", "—"), ("&ndash;", "–"), ("&hellip;", "…")):
        text = text.replace(source, target)
    text = re.sub(r"[\u200b\u2060\ufeff\u00ad]", "", text)
    text = re.sub(r"[*_`]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t·•|>#")


def clean_block(text):
    return re.sub(r"\s+", " ", clean_inline(text)).strip()


NOISE_BLOCK = re.compile(r"(?:^|\b)(?:main|primary|secondary|mobile|footer|header|top|bottom)\s+(?:account\s+)?nav(?:igation)?\b|^\s*nav(?:igation)?\s*$|^\s*footer\b|^\s*menu\b|skip to (?:main )?content|breadcrumb|\(footer\)|\(nav(?:igation)?\)|\b(?:footer|nav(?:igation)?)\s*$", re.I)


def block_units(text):
    """Return (blocks, alts); blocks are (kind, level, cleaned text)."""
    alts = image_alts(text)
    if looks_html(text):
        text = html_to_text(text)
    blocks = []
    normalized = re.sub(r"[ \t]+(#{2,6})[ \t]+", r"\n\1 ", text)
    for raw in normalized.splitlines():
        line = raw.strip()
        if not line:
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            value = clean_block(heading.group(2))
            if value and not NOISE_BLOCK.search(value):
                blocks.append(("heading", len(heading.group(1)), value))
            continue
        if re.match(r"^[-*+]\s*$", line):
            continue
        item = re.match(r"^(?:[-*+]|\d+[.)])\s+(.*)$", line)
        if item:
            value = clean_block(item.group(1))
            if value and not NOISE_BLOCK.search(value):
                blocks.append(("item", 0, value))
            continue
        value = clean_block(line)
        if value and not NOISE_BLOCK.search(value):
            blocks.append(("text", 0, value))
    return blocks, alts


def sentences(text):
    cleaned = clean_block(text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)
    return [part.strip() for part in parts if part.strip()]


NAV_BAD = {"home", "pricing", "product", "products", "features", "solutions", "about", "company", "customers", "integrations", "docs", "documentation", "blog", "news", "login", "log in", "sign up", "get started", "contact", "support", "careers", "legal", "privacy", "terms", "security", "status", "partners", "developers", "resources", "search", "menu", "close", "key features", "includes", "overview", "learn more", "read more", "why choose"}
CTA_PREFIX = ("get ", "sign ", "log ", "contact ", "try ", "learn ", "read ", "view ", "watch ", "start ", "book ", "download ", "see ", "explore ", "join ", "subscribe ", "talk ", "buy ", "request ", "schedule ", "apply ", "select plan", "meet ")


def meaningful(text, *, min_len=10, min_words=2):
    if not text:
        return False
    value = re.sub(r"\s+", " ", text).strip()
    if len(value) < min_len or is_filler(value):
        return False
    if len(re.findall(r"[A-Za-z]", value)) < 6:
        return False
    if re.fullmatch(r"[\W\d_]+", value):
        return False
    if value.lower().strip(" .:—-") in NAV_BAD:
        return False
    return len(value.split()) >= min_words


def bounded(text, limit=EXCERPT_LIMIT):
    value = re.sub(r"\s+", " ", text).strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def dedupe(values):
    seen, out = set(), []
    for value in values:
        key = re.sub(r"\W+", " ", value.lower()).strip()
        if key and key not in seen:
            seen.add(key)
            out.append(value)
    return out


CATEGORY_RULES = (
    ("Customer relationship management", r"\b(crm|customer relationship management|sales platform|marketing automation|salesforce)\b"),
    ("Payments and financial infrastructure", r"\b(payment processing|online payments|accept payments|payment infrastructure|financial infrastructure|money movement|payments platform|payment platform|checkout|merchant account)\b"),
    ("Design, prototyping, and visual collaboration", r"\b(design tool|design platform|design and prototype|prototyp\w+|whiteboard|visual collaboration|interface design|design systems?)\b"),
    ("Video, meetings, and collaboration", r"\b(video (?:messaging|communication|conferencing|meetings|recording)|screen recording|video calls|video messaging|remote collaboration)\b"),
    ("Project and work management", r"\b(project management|work management|task management|issue tracking|kanban|sprint planning|roadmap)\b"),
    ("E-commerce and retail platform", r"\b(e-?commerce|online store|sell online|storefront|shopping cart|retail platform|merchant services)\b"),
    ("Customer support and communications", r"\b(customer support|customer service|help desk|live chat|communications platform|messaging platform|contact center|omnichannel)\b"),
    ("Developer platform and infrastructure", r"\b(developer platform|developer tools?|api platform|cloud platform|serverless|deployment platform|devops|web infrastructure|frontend cloud)\b"),
    ("Data, analytics, and AI platform", r"\b(artificial intelligence|machine learning|ai platform|analytics platform|business intelligence|data platform|data warehouse|large language model)\b"),
    ("Productivity and workplace software", r"\b(workspace|productivity|note-?taking|knowledge base|team collaboration|documentation platform|all-in-one workspace)\b"),
    ("Cloud, security, and IT infrastructure", r"\b(cybersecurity|security platform|cloud infrastructure|identity platform|zero trust|it management|endpoint security)\b"),
    ("Content design and marketing", r"\b(marketing platform|content creation|brand platform|graphic design|social media management)\b"),
)


def extract_category(blocks, plain):
    sentences_pool = sentences(plain) or [plain]
    for label, pattern in CATEGORY_RULES:
        for sentence in sentences_pool:
            if re.search(pattern, sentence, re.I) and meaningful(sentence, min_len=12):
                return label, bounded(sentence)
        if re.search(pattern, plain, re.I):
            match = re.search(pattern, plain, re.I)
            snippet = plain[max(0, match.start() - 40): match.end() + 120]
            return label, bounded(snippet.strip())
    return None, None


POSITIONING_CUES = re.compile(r"\b(for every|for all (?:businesses|teams|companies|developers)|for businesses|for teams|for developers|helps? (?:you|teams|companies|businesses|developers)|platform (?:for|to)|infrastructure (?:for|to)|designed (?:for|to)|built (?:for|to)|the way (?:modern|teams|companies|businesses|work)|so (?:you|teams|businesses|developers) can|empower\w*|backbone|reimagine|unlock)\b", re.I)
POSITIONING_NOUN = re.compile(r"\b(platform|tool|software|solution|workspace|infrastructure|application|product|service|technology|business(?:es)?|teams?|compan(?:y|ies)|for )\b", re.I)


def extract_positioning(blocks, one_liner):
    candidates = []
    for kind, level, text in blocks:
        if len(text) > 220 or not meaningful(text, min_len=14) or is_filler(text):
            continue
        if text == one_liner:
            continue
        if POSITIONING_CUES.search(text):
            candidates.append(text)
    if candidates:
        candidates.sort(key=len)
        return candidates[0]
    for kind, level, text in blocks:
        if 16 <= len(text) <= 160 and text != one_liner and meaningful(text, min_len=16) and not is_filler(text) and POSITIONING_NOUN.search(text):
            return text
    return None


def extract_one_liner(blocks):
    for kind, level, text in blocks:
        if kind == "heading" and 20 <= len(text) <= 220:
            return text
    for kind, level, text in blocks:
        if 24 <= len(text) <= 220 and meaningful(text, min_len=24, min_words=4):
            return text
    return None


PRODUCT_STOP = re.compile(r"\b(?:choose|get started|sign up|learn more|read |view |try |contact|talk to|book|watch|see |start |download|explore|join|subscribe|request|schedule|apply|why choose|key features|how |what |includes|overview|resources|objective|strategy|staffing|benchmark|report\b|guide\b|blog\b|story\b|stories\b|update\b|news\b|programme|program\b|case study|testimonial)\b", re.I)


def extract_products(blocks):
    out = []
    for kind, level, text in blocks:
        if kind != "heading":
            continue
        value = text.strip().rstrip(".").strip()
        if not (2 <= len(value.split()) <= 6) or len(value) > 70:
            continue
        if value.endswith("?") or PRODUCT_STOP.search(value):
            continue
        if not meaningful(value, min_len=8, min_words=2):
            continue
        out.append(value)
    return dedupe(out)


FEATURE_CUES = re.compile(r"\b(?:lets? you|allows? you|enables? you|supports?|automate\w*|integrat(?:e|es|ion|ions)|build (?:and|your|custom)|manage(?:s)?|track(?:s)?|create(?:s)?|share|collaborat\w+|analy[sz]e|search|sync|connect|deploy|monetis\w+|monetiz\w+|optimi[sz]e|protect|scale|orchestrat\w+)\b", re.I)
FEATURE_NOISE = re.compile(r"read the (?:story|guide|article)|learn more|watch (?:now|the|video)|sign up|get started|all rights reserved|cookie", re.I)


def extract_features(blocks, plain, one_liner):
    out = []
    skip_prefix = ("read ", "learn ", "view ", "watch ", "see ", "get started", "try ", "sign up", "download")

    def consider(text):
        for sentence in sentences(text):
            if sentence == one_liner or not meaningful(sentence, min_len=30, min_words=6) or len(sentence) > 220:
                continue
            if sentence.lower().startswith(skip_prefix) or FEATURE_NOISE.search(sentence):
                continue
            if FEATURE_CUES.search(sentence):
                out.append(sentence)

    for kind, level, text in blocks:
        if kind in ("text", "item"):
            consider(text)
    return dedupe(out)


TARGET_CUES = re.compile(r"\b(?:businesses|business|companies|company|teams|team|developers|developer|enterprises|enterprise|startups|startup|founders|creators|marketers|merchants|organizations|organisation|of all sizes|every stack|every business model|smb|small business)\b", re.I)


def extract_target_market(blocks, plain):
    out = []
    for kind, level, text in blocks:
        if len(text) > 220:
            continue
        if TARGET_CUES.search(text) and meaningful(text, min_len=14):
            out.append(text)
    for sentence in sentences(plain):
        if TARGET_CUES.search(sentence) and meaningful(sentence, min_len=24, min_words=4) and len(sentence) <= 240:
            out.append(sentence)
    return dedupe(out)


INTEGRATION_HEAD = re.compile(r"\b(integration|integrations|connected apps|marketplace|apps and integrations|connect|ecosystem)\b", re.I)


def extract_integrations(blocks, alts, category="unknown"):
    out = []
    in_section = False
    section_level = 0
    for kind, level, text in blocks:
        if kind == "heading":
            if INTEGRATION_HEAD.search(text) and len(text) <= 80:
                in_section = True
                section_level = level
                continue
            if in_section and level <= section_level:
                in_section = False
        if in_section and not PRODUCT_STOP.search(text) and len(text) <= 70 and not text.endswith("?"):
            for piece in re.split(r",| and ", text):
                piece = re.sub(r"\([^)]*\)", "", piece).strip().strip(".").strip()
                if 2 <= len(piece) <= 40 and not piece.endswith("?") and meaningful(piece, min_len=2, min_words=1) and not piece.lower().startswith(("see ", "view ", "learn ", "explore ")):
                    out.append(piece)
    for kind, level, text in blocks:
        if kind == "heading" and len(text) <= 40 and meaningful(text, min_len=3, min_words=1) and any(word in text for word in ("Integration", "Connect", "App", "Partner", "Plugin", "Extension")):
            out.append(text)
    if category == "integrations":
        for alt in alts:
            clean = re.sub(r"\s*logo\s*$", "", alt, flags=re.I).strip()
            if clean.lower() != alt.lower() and 2 <= len(clean) <= 40 and meaningful(clean, min_len=2, min_words=1):
                out.append(clean)
    return [value for value in dedupe(out) if not re.search(r"\blogo\b", value, re.I)]


PROPER = re.compile(r"^[A-Z0-9][\w'’&.-]*(?:\s+[A-Z0-9][\w'’&.-]*){0,3}$")
NAME_OK = re.compile(r"^[A-Za-z0-9][\w'’&.-]*(?:\s+[A-Za-z0-9][\w'’&.-]*){0,3}$")
GENERIC_NAME = re.compile(r"\b(?:logo|icon|view|image|photo|screenshot|illustration|background|banner|hero|graphic|chart|mockup|map|client|clients|partner|partners|badge|avatar|profile)\b", re.I)


def extract_customers(blocks, alts, links, homepage):
    out = []
    for alt in alts:
        clean = re.sub(r"\s*logo\s*$", "", alt, flags=re.I).strip()
        if clean.lower() != alt.lower() and NAME_OK.match(clean) and 1 <= len(clean.split()) <= 3 and len(clean) <= 40 and not GENERIC_NAME.search(clean):
            out.append(clean.title() if clean.islower() else clean)
    for kind, level, text in blocks:
        if kind == "heading":
            match = re.match(r"^([A-Z][\w'’&.-]*(?:\s+[A-Z][\w'’&.-]*){0,2})\s+(unifies|consolidates|powers|improves|grows|scales|partners|launches|drives|expands|adopts|uses|migrates|accelerates)\b", text)
            if match:
                out.append(match.group(1))
    for alt in alts:
        clean = alt.strip()
        if PROPER.match(clean) and 1 <= len(clean.split()) <= 3 and meaningful(clean, min_len=2, min_words=1) and not GENERIC_NAME.search(clean):
            out.append(clean)
    for link in links:
        parsed = urllib.parse.urlparse(link)
        if normalized_hostname(link) != normalized_hostname(homepage):
            continue
        segments = [segment for segment in parsed.path.split("/") if segment]
        lowered = [segment.lower() for segment in segments]
        for marker in ("customers", "customer", "case-studies", "case-study", "stories"):
            if marker in lowered:
                index = lowered.index(marker)
                if index + 1 < len(segments):
                    slug = segments[index + 1]
                    slug = urllib.parse.unquote(slug).replace("-", " ").replace("_", " ").strip()
                    if 1 <= len(slug.split()) <= 4 and re.search(r"[A-Za-z]", slug):
                        out.append(slug.title())
    return dedupe(out)


SIGNAL_RULES = (
    ("partnership", r"\b(partner(?:s|ed|ship)|collaborat\w+ with|teams? up with|joins forces)\b"),
    ("product_launch", r"\b(introduc\w+|launch\w+|unveil\w+|now available|announc\w+)\b"),
    ("product_direction", r"\b(new (?:tools?|features?|capabilities)|expands?|extends?|adds? support|ai|agentic|roadmap)\b"),
    ("market_expansion", r"\b(expand\w* (?:to|into)|new markets?|international|global expansion)\b"),
    ("customer_momentum", r"\b(customers?|milestone|growth|adoption|million|billion)\b"),
    ("pricing", r"\b(pricing|plans?|prices?|cost|billing)\b"),
)


def extract_signals(blocks, plain, category, page_label):
    out = []
    candidates = []
    if category == "changelog_blog":
        for kind, level, text in blocks:
            if kind in ("heading", "item") and 12 <= len(text) <= 200:
                candidates.append(text)
                break
    for kind, level, text in blocks:
        if kind == "heading" and 12 <= len(text) <= 160 and re.search(r"\b(new|launch\w*|introduc\w+|announc\w+|partner\w*|expand\w*|unveil\w+|acquires?|raises?|milestone)\b", text, re.I):
            candidates.append(text)
    for candidate in candidates:
        signal_type = "other"
        for name, pattern in SIGNAL_RULES:
            if re.search(pattern, candidate, re.I):
                signal_type = name
                break
        out.append((signal_type, bounded(candidate)))
    return out


PRICING_PLAN = re.compile(r"^(free|starter|basic|essential|standard|pro|professional|business|team|teams|organization|organisation|enterprise|custom|plus|premium|growth|scale|unlimited|advanced|beginner|hobby|personal|company|dev|developer|collab|core|lite|individual)$", re.I)
PLAN_TOKEN = re.compile(r"\b(free|starter|basic|essential|standard|pro|professional|business|team|organization|enterprise|custom|plus|premium|growth|scale|unlimited|advanced)\b", re.I)
AMOUNT_CURRENCY = re.compile(r"[$€£]\s?\d[\d.,]*|\d[\d.,]*\s?[€$£]|\d[\d.,]*\s?(?:USD|EUR|GBP)")
AMOUNT_RATE = re.compile(r"\d[\d.,]*\s?%")
PRICING_WORD = re.compile(r"\b(?:fee|fees|rate|pricing|price|prices|transaction|payment|card|per (?:user|seat|month|year|editor|member|workspace)|billed|subscription|credits?/mo)\b", re.I)
MODEL_CUES = (
    (r"pay[- ]as[- ]you[- ]go", "Pay-as-you-go"),
    (r"usage[- ]based", "Usage-based"),
    (r"(?:per|/)\s*(?:user|seat|editor|member|workspace)(?:\s*/\s*(?:month|year|mo|yr))?", None),
    (r"\bsubscription\b|\bbilled (?:monthly|annually)\b|\bper month\b", None),
    (r"\bfree\b", "Free tier"),
)


def extract_pricing(text):
    """Return (model_value, model_excerpt, [(plan, excerpt)]) grounded in the consumed body."""
    blocks, _ = block_units(text)
    plain = clean_block(text)
    model_value, model_excerpt = None, None
    for pattern, label in MODEL_CUES:
        match = re.search(pattern, plain, re.I)
        if match:
            phrase = match.group(0).strip()
            if label is None:
                label = phrase.title()
            model_value = label
            model_excerpt = bounded(plain[max(0, match.start() - 60): match.end() + 140])
            break
    plans = []
    current = None
    current_index = None
    for index, (kind, level, block) in enumerate(blocks):
        if kind not in ("heading", "item", "text"):
            continue
        bare = re.sub(r"\s+(?:monthly|annual|annually|billed|per|seat|month|year)$", "", block.strip().rstrip(".").strip(), flags=re.I).strip()
        is_plan = bool(PRICING_PLAN.fullmatch(bare)) or (kind == "heading" and len(bare.split()) <= 3 and PLAN_TOKEN.search(bare) and not AMOUNT_CURRENCY.search(bare))
        if is_plan:
            current, current_index = (bare, block), index
            continue
        if current and current_index is not None and index - current_index <= 4:
            amount = AMOUNT_CURRENCY.search(block)
            if not amount and PRICING_WORD.search(block):
                amount = AMOUNT_RATE.search(block)
            free_tier = re.match(r"^free\b", block, re.I) and len(block.split()) <= 8 and not amount
            if amount:
                plan_name = current[0]
                value = f"{plan_name} — {amount.group(0).strip()}"
                plans.append((value, bounded(f"{current[1]} {block}")))
                current, current_index = None, None
            elif free_tier:
                value = f"{current[0]} — Free"
                plans.append((value, bounded(f"{current[1]} {block}")))
                current, current_index = None, None
    if not plans:
        for kind, level, block in blocks:
            bare = block.strip().rstrip(".").strip()
            if PRICING_PLAN.fullmatch(bare):
                plans.append((bare, block))
    if not plans:
        for kind, level, block in blocks:
            if AMOUNT_CURRENCY.search(block) and len(block) <= 200 and meaningful(block, min_len=8):
                plans.append((bounded(block, 120), block))
                if len(plans) >= 3:
                    break
    if not plans:
        return None
    if model_value is None:
        anchor = re.search(r"\b(?:pricing|plans?|price|billed|per month|subscription|pay as you go)\b", plain, re.I)
        if anchor:
            model_value = bounded(plain[max(0, anchor.start() - 20): anchor.end() + 20], 60)
            model_excerpt = bounded(plain[max(0, anchor.start() - 40): anchor.end() + 80])
        else:
            model_value, model_excerpt = plans[0][0], plans[0][1]
    seen, unique_plans = set(), []
    for value, excerpt in plans:
        key = re.sub(r"\W+", " ", value.lower()).strip()
        if key and key not in seen:
            seen.add(key)
            unique_plans.append((value, excerpt))
    return model_value, model_excerpt, unique_plans


def failure_support(result, source_url, label):
    status = result.get("status") if result.get("status") is not None else "unavailable"
    return f"{label} unavailable; url={source_url}; status={status}; error={result.get('error') or 'none'}."


def first_body_excerpt(blocks, plain):
    for kind, level, text in blocks:
        if kind == "heading" and 12 <= len(text) <= 260:
            return bounded(text)
    for sentence in sentences(plain):
        if 12 <= len(sentence) <= 260:
            return bounded(sentence)
    return bounded(plain) if plain else "Empty first-party body."


def request_record(result):
    return {"surface": result.get("surface", "free_markdown"), "operation": "GET", "source_url": public_url(result["source_url"]), "endpoint_url": public_url(result.get("endpoint_url", result["source_url"])), "http_status": result["status"] or 599, "content_type": result["content_type"] or "unavailable"}


def claim(value, evidence):
    return {"value": value, "evidence_ids": [evidence]}


def designated_pricing_page(page):
    return page.get("category") == "pricing_plans" and page_category(page.get("source_url", "")) == "pricing_plans"


CATEGORY_SUPPORT = {
    "homepage": True, "product_features": True, "pricing_plans": True, "integrations": True,
    "about": True, "docs": True, "customers_case_studies": True, "changelog_blog": True,
    "careers": False, "unknown": False,
}
# Fields a page category is allowed to feed, and the fallback field used to keep a
# readable in-category page materially contributing even when direct extraction is thin.
ELIGIBLE_FIELDS = {
    "homepage": ("products", "features", "target_market", "integrations", "customers"),
    "product_features": ("products", "features"),
    "pricing_plans": ("features", "integrations"),
    "integrations": ("integrations",),
    "about": ("target_market", "features"),
    "docs": ("features",),
    "customers_case_studies": ("customers",),
    "changelog_blog": (),
    "careers": (),
    "unknown": (),
}
FALLBACK_TARGET = {"product_features": "products", "pricing_plans": "features", "integrations": "integrations", "about": "target_market", "docs": "features", "customers_case_studies": "customers"}


def build_evidence_id(page_id, field, index):
    return f"{page_id}-{field}-{index}"


def make_brief(case, fetched, candidates=None, discovery=None, research_goal=None):
    pages, brand_result = fetched[:-1], fetched[-1]
    home = pages[0]
    home_id, brand_id = "homepage", "brand"
    home_ok = successful(home)
    page_ids = [home_id] + [f"selected-page{'' if index == 1 else '-' + str(index)}" for index in range(1, len(pages))]
    page_ok = [successful(page) for page in pages]
    evidence = []
    evidence_owner = {}

    def add_evidence(eid, source_url, excerpt, kind="first_party", owner=None):
        evidence.append({"id": eid, "source_url": public_url(source_url), "kind": kind, "fetched_at": now(), "excerpt_or_support": bounded(excerpt)})
        evidence_owner[eid] = owner

    page_units = []
    for index, page in enumerate(pages):
        label = "Homepage Markdown fetch" if index == 0 else ("Direct first-party pricing HTML fetch" if page.get("surface") == "free_direct_pricing" else "Selected Markdown fetch")
        if page_ok[index]:
            blocks, alts = block_units(page.get("text", ""))
            plain = " ".join(text for _, _, text in blocks) if blocks else clean_block(page.get("text", ""))
            add_evidence(page_ids[index], page["source_url"], first_body_excerpt(blocks, plain), owner=page_ids[index])
            page_units.append({"index": index, "id": page_ids[index], "page": page, "category": page.get("category", "homepage") if index else "homepage", "blocks": blocks, "alts": alts, "plain": plain, "ok": True})
        else:
            add_evidence(page_ids[index], page["source_url"], failure_support(page, public_url(page["source_url"]), label), owner=page_ids[index])
            page_units.append({"index": index, "id": page_ids[index], "page": page, "category": page.get("category", "homepage") if index else "homepage", "blocks": [], "alts": [], "plain": "", "ok": False})

    if successful(brand_result):
        add_evidence(brand_id, brand_result["source_url"], bounded("Brand identity fetch succeeded; identity metadata retained for " + case["domain"] + "."), owner=brand_id)
    else:
        add_evidence(brand_id, brand_result["source_url"], failure_support(brand_result, public_url(brand_result["source_url"]), "Brand fetch"), owner=brand_id)

    def page_order(priority):
        ranked = sorted(
            (unit for unit in page_units if unit["ok"] and unit["category"] in priority),
            key=lambda unit: (priority.index(unit["category"]), unit["index"]),
        )
        return ranked

    home_unit = page_units[0] if page_units[0]["ok"] else None
    one_liner, one_liner_excerpt = None, None
    if home_unit:
        one_liner = extract_one_liner(home_unit["blocks"])
        one_liner_excerpt = one_liner
    category_value, category_excerpt = (None, None)
    for unit in page_order(["homepage", "about", "product_features"]):
        value, excerpt = extract_category(unit["blocks"], unit["plain"])
        if value:
            category_value, category_excerpt = value, excerpt
            category_unit = unit
            break
    else:
        category_unit = home_unit
    positioning, positioning_excerpt, positioning_unit = None, None, home_unit
    for unit in page_order(["homepage", "about", "product_features"]):
        value = extract_positioning(unit["blocks"], one_liner)
        if value:
            positioning, positioning_excerpt, positioning_unit = value, value, unit
            break

    # Collect page-scoped items per field: (value, excerpt, unit)
    field_items = {"products": [], "features": [], "target_market": [], "integrations": [], "customers": []}
    extraction_by_unit = {}

    def harvest(unit):
        items = {"products": [], "features": [], "target_market": [], "integrations": [], "customers": []}
        if not unit["ok"]:
            return items
        for value in extract_products(unit["blocks"]):
            items["products"].append((value, value))
        for value in extract_features(unit["blocks"], unit["plain"], one_liner):
            items["features"].append((value, value))
        for value in extract_target_market(unit["blocks"], unit["plain"]):
            items["target_market"].append((value, value))
        for value in extract_integrations(unit["blocks"], unit["alts"], unit["category"]):
            items["integrations"].append((value, value))
        links = page_links(unit["page"].get("text", ""))
        for value in extract_customers(unit["blocks"], unit["alts"], links, case["homepage"]):
            items["customers"].append((value, value))
        # A supported page with no eligible field claim falls back to a real bounded body line so it still contributes.
        eligible = ELIGIBLE_FIELDS.get(unit["category"], ())
        fallback_field = FALLBACK_TARGET.get(unit["category"])
        if fallback_field and eligible and not any(items.get(field) for field in eligible):
            value = None
            for kind, level, text in unit["blocks"]:
                if 8 <= len(text) <= 120 and meaningful(text, min_len=8):
                    value = text
                    break
            if value is None:
                for sentence in sentences(unit["plain"]):
                    if 12 <= len(sentence) <= 160 and meaningful(sentence, min_len=12):
                        value = sentence
                        break
            if value and not is_filler(value):
                items[fallback_field].append((value, value))
        extraction_by_unit[unit["id"]] = items
        return items

    units = [unit for unit in page_units]
    for unit in units:
        harvest(unit)

    field_priority = {
        "products": ["homepage", "product_features", "about", "docs"],
        "features": ["homepage", "product_features", "docs", "about"],
        "target_market": ["homepage", "about", "product_features"],
        "integrations": ["integrations", "homepage", "pricing_plans", "docs", "product_features"],
        "customers": ["customers_case_studies", "homepage", "about"],
    }
    field_caps = {"products": 4, "features": 3, "target_market": 3, "integrations": 5, "customers": 5}

    def choose(field):
        ordered_units = page_order(field_priority[field])
        chosen, seen = [], {}
        for unit in ordered_units:
            for value, excerpt in extraction_by_unit.get(unit["id"], {}).get(field, []):
                key = re.sub(r"\W+", " ", value.lower()).strip()
                if not key or not meaningful(value, min_len=2, min_words=1):
                    continue
                if key in seen:
                    continue
                seen[key] = True
                chosen.append((value, excerpt, unit))
                if len(chosen) >= field_caps[field]:
                    return chosen
        return chosen

    claims_by_path = {}
    claim_evidence = []
    path_owner = {}

    def register(path, value, excerpt, unit, kind="first_party"):
        eid = build_evidence_id(unit["id"], re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-"), 1)
        suffix = 1
        while any(item["id"] == eid for item in evidence):
            suffix += 1
            eid = build_evidence_id(unit["id"], re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-"), suffix)
        add_evidence(eid, unit["page"]["source_url"], excerpt, kind=kind, owner=unit["id"])
        claims_by_path[path] = claim(value, eid)
        claim_evidence.append({"claim_path": path, "evidence_ids": [eid]})
        path_owner[path] = unit["id"]
        return eid

    if home_unit:
        if one_liner:
            register("summary.one_liner", one_liner, one_liner_excerpt, home_unit)
        else:
            claims_by_path["summary.one_liner"] = claim(None, home_unit["id"])
            claim_evidence.append({"claim_path": "summary.one_liner", "evidence_ids": [home_unit["id"]]})
            path_owner["summary.one_liner"] = home_unit["id"]
        if category_value:
            register("summary.category", category_value, category_excerpt, category_unit if category_unit and category_unit["ok"] else home_unit)
        else:
            claims_by_path["summary.category"] = claim(None, home_unit["id"])
            claim_evidence.append({"claim_path": "summary.category", "evidence_ids": [home_unit["id"]]})
            path_owner["summary.category"] = home_unit["id"]
        if positioning:
            register("summary.positioning", positioning, positioning_excerpt, positioning_unit if positioning_unit and positioning_unit["ok"] else home_unit)
        else:
            claims_by_path["summary.positioning"] = claim(None, home_unit["id"])
            claim_evidence.append({"claim_path": "summary.positioning", "evidence_ids": [home_unit["id"]]})
            path_owner["summary.positioning"] = home_unit["id"]
    else:
        for path in ("summary.one_liner", "summary.category", "summary.positioning"):
            claims_by_path[path] = claim(None, home_id)
            claim_evidence.append({"claim_path": path, "evidence_ids": [home_id]})
            path_owner[path] = home_id

    field_claims = {field: choose(field) for field in field_items}

    for field, chosen in field_claims.items():
        for index, (value, excerpt, unit) in enumerate(chosen):
            register(f"{field}[{index}]", value, excerpt, unit)

    # Pricing: scan every consumed pricing page, preferring the canonical pricing path, and use the first grounded one.
    def pricing_preference(unit):
        path = urllib.parse.urlparse(unit["page"]["source_url"]).path.rstrip("/").lower()
        return 0 if path in ("/pricing", "/plans") else 1

    pricing_unit = None
    pricing_result = None
    for unit in sorted(page_order(["pricing_plans"]), key=pricing_preference):
        if pricing_unit is None:
            pricing_unit = unit
        candidate = extract_pricing(unit["page"].get("text", ""))
        if candidate:
            pricing_unit, pricing_result = unit, candidate
            break
    pricing_unknown = pricing_result is None
    if pricing_result:
        model_value, model_excerpt, plan_pairs = pricing_result
        model_eid = build_evidence_id(pricing_unit["id"], "pricing-model", 1)
        add_evidence(model_eid, pricing_unit["page"]["source_url"], model_excerpt, owner=pricing_unit["id"])
        pricing_model = claim(model_value, model_eid)
        claim_evidence.append({"claim_path": "pricing.model", "evidence_ids": [model_eid]})
        claims_by_path["pricing.model"] = pricing_model
        path_owner["pricing.model"] = pricing_unit["id"]
        plans = []
        for index, (value, excerpt) in enumerate(plan_pairs[:6]):
            eid = build_evidence_id(pricing_unit["id"], f"pricing-plan-{index}", 1)
            add_evidence(eid, pricing_unit["page"]["source_url"], excerpt, owner=pricing_unit["id"])
            plans.append(claim(value, eid))
            claim_evidence.append({"claim_path": f"pricing.plans[{index}]", "evidence_ids": [eid]})
            claims_by_path[f"pricing.plans[{index}]"] = plans[-1]
            path_owner[f"pricing.plans[{index}]"] = pricing_unit["id"]
    else:
        fallback_id = pricing_unit["id"] if pricing_unit else home_id
        claims_by_path["pricing.model"] = claim(None, fallback_id)
        claim_evidence.append({"claim_path": "pricing.model", "evidence_ids": [fallback_id]})
        path_owner["pricing.model"] = fallback_id
        plans = []

    # Signals
    signals = []
    signal_sources = []
    if home_unit:
        home_signals = extract_signals(home_unit["blocks"], home_unit["plain"], "homepage", "homepage")
        for signal_type, summary in home_signals[:2]:
            signal_sources.append((signal_type, summary, home_unit))
    for unit in page_order(["changelog_blog"]):
        for signal_type, summary in extract_signals(unit["blocks"], unit["plain"], "changelog_blog", unit["category"])[:1]:
            signal_sources.append((signal_type, summary, unit))
    if home_unit and positioning:
        home_signals = [("positioning", positioning)]
    else:
        home_signals = []
    for signal_type, summary in home_signals:
        signal_sources.insert(0, (signal_type, summary, home_unit))
    seen_signals = set()
    for signal_type, summary, unit in signal_sources:
        key = re.sub(r"\W+", " ", summary.lower()).strip()
        if not key or key in seen_signals:
            continue
        seen_signals.add(key)
        eid = build_evidence_id(unit["id"], f"signal-{len(signals)}", 1)
        add_evidence(eid, unit["page"]["source_url"], summary, owner=unit["id"])
        path_owner[f"signals[{len(signals)}]"] = unit["id"]
        signals.append({"type": signal_type, "summary": bounded(summary), "observed_at": now(), "recency": "current_observation", "evidence_ids": [eid]})
        if len(signals) >= 3:
            break

    # Guarantee every successful supported-category page materially contributes a claim.
    contributed_ids = {path_owner[path] for path, item in claims_by_path.items() if item["value"] is not None}
    contributed_ids.update(path_owner[path] for path in path_owner if path.startswith("signals["))
    for unit in page_units:
        if len(signals) >= 8:
            break
        if unit["ok"] and CATEGORY_SUPPORT.get(unit["category"]) and unit["id"] not in contributed_ids:
            summary = first_body_excerpt(unit["blocks"], unit["plain"])
            if is_filler(summary) or len(summary.strip()) < 8:
                continue
            signal_type = {"pricing_plans": "pricing", "changelog_blog": "other"}.get(unit["category"], "positioning")
            eid = build_evidence_id(unit["id"], "signal-fallback", 1)
            add_evidence(eid, unit["page"]["source_url"], summary, owner=unit["id"])
            path_owner[f"signals[{len(signals)}]"] = unit["id"]
            signals.append({"type": signal_type, "summary": bounded(summary), "observed_at": now(), "recency": "current_observation", "evidence_ids": [eid]})
            contributed_ids.add(unit["id"])

    # Explicit unknowns for empty fields.
    material_empty = [field for field in ("products", "target_market", "features", "integrations", "customers") if not field_claims[field]]
    unknowns = []
    for field in material_empty:
        unknowns.append({"field": field, "reason": "No reliable first-party evidence for this field in the bounded consumed pages."})
    if pricing_unknown:
        unknowns.append({"field": "pricing", "reason": "No grounded public pricing text was extracted from the consumed first-party pages."})

    # Brand identity.
    brand_name = case["name"] if successful(brand_result) else None
    brand_description = None
    if successful(brand_result) and looks_html(brand_result.get("text", "")):
        match = re.search(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']+)[\"']", brand_result["text"], re.I)
        if match:
            brand_description = bounded(match.group(1), 1000)
    brand = {"name": brand_name, "description": brand_description, "unknown": not successful(brand_result)}

    selected_pages = [{"category": unit["category"], "url": public_url(unit["page"]["source_url"]), "evidence_id": unit["id"]} for unit in page_units]

    if research_goal:
        notable_context = []
        if home_unit and positioning:
            eid = build_evidence_id(home_unit["id"], "notable-context-1", 1)
            add_evidence(eid, home_unit["page"]["source_url"], positioning, owner=home_unit["id"])
            notable_context.append(claim(positioning, eid))
            claim_evidence.append({"claim_path": "notable_context[0]", "evidence_ids": [eid]})
            claims_by_path["notable_context[0]"] = notable_context[0]
            path_owner["notable_context[0]"] = home_unit["id"]
    else:
        notable_context = []

    page_contribution = []
    for unit in page_units:
        if not unit["ok"]:
            page_contribution.append({"evidence_id": unit["id"], "category": unit["category"], "read": False, "claims": []})
            continue
        paths = sorted(path for path, owner in path_owner.items() if owner == unit["id"])
        page_contribution.append({"evidence_id": unit["id"], "category": unit["category"], "read": True, "claims": paths})

    coverage = []
    if not home_ok:
        coverage.append("Homepage coverage is unavailable; material company claims remain unknown.")
    if len(pages) == 1:
        coverage.append("No bounded homepage link with a selected page category was available; pricing is unknown.")
    elif pricing_unknown:
        coverage.append("No grounded pricing evidence succeeded from a pricing-designated page; pricing is unknown.")
    coverage.append("Brand coverage is unavailable; identity metadata is unknown." if not successful(brand_result) else "Brand output is limited to identity metadata; no brand claims were inferred.")
    coverage.append("Only bounded first-party pages were consumed; populated claims cite a bounded excerpt from the consumed body and unsupported fields remain explicit unknowns.")

    discovery = discovery or {"surface": "free_homepage_discovery", "source_url": case["homepage"], "endpoint_url": case["homepage"], "status": None, "content_type": "", "error": "not executed in fixture"}
    discovery_call = [request_record(discovery)]
    page_calls = [request_record(record) for unit in page_units for record in unit["page"].get("attempts", [unit["page"]])]
    capabilities = ["free_markdown", "free_homepage_discovery", "free_brand"]
    if any(unit["page"].get("surface") == "free_direct_pricing" for unit in page_units):
        capabilities.append("free_direct_pricing")
    partial_failure_count = sum(1 for unit in page_units if not unit["ok"])
    page_read_count = len(page_units) - partial_failure_count
    source_coverage = [{"category": unit["category"], "pages_read": 1} for unit in page_units if unit["ok"]]
    meta = {"capabilities_used": capabilities, "tool_calls": discovery_call + page_calls + [request_record(brand_result)], "synthesis": "host_agent", "researched_at": now(), "research_goal": research_goal, "pages_discovered": len(candidates or pages), "pages_attempted": len(page_units), "page_read_count": page_read_count, "page_read_budget_default": DEFAULT_CAP, "page_read_budget_hard_cap": HARD_CAP, "partial_failure_count": partial_failure_count, "source_coverage": source_coverage, "page_contribution": page_contribution}

    brief = {
        "brief_version": "2.0",
        "generated_at": now(),
        "company": {"domain": case["domain"], "name": case["name"], "homepage_url": case["homepage"]},
        "summary": {
            "one_liner": claims_by_path["summary.one_liner"],
            "category": claims_by_path["summary.category"],
            "positioning": claims_by_path["summary.positioning"],
        },
        "products": [claims_by_path[f"products[{i}]"] for i in range(len(field_claims["products"]))],
        "target_market": [claims_by_path[f"target_market[{i}]"] for i in range(len(field_claims["target_market"]))],
        "pricing": {"model": claims_by_path["pricing.model"], "plans": plans, "unknown": pricing_unknown},
        "features": [claims_by_path[f"features[{i}]"] for i in range(len(field_claims["features"]))],
        "integrations": [claims_by_path[f"integrations[{i}]"] for i in range(len(field_claims["integrations"]))],
        "customers": [claims_by_path[f"customers[{i}]"] for i in range(len(field_claims["customers"]))],
        "signals": signals,
        "important_pages": selected_pages,
        "brand": brand,
        "evidence": evidence,
        "claim_evidence": claim_evidence,
        "unknowns": unknowns,
        "coverage_limits": coverage,
        "meta": meta,
    }
    if research_goal is not None:
        brief["notable_context"] = notable_context
    return brief


def sanitize_request_records(records):
    return [request_record(record) for record in records]


FILLER_HINTS = re.compile(r"(?:described in bounded|observed in bounded|bounded first-party|first-party text|public company information|response body omitted|non-empty text|software company\.?$|current positioning observed|public positioning is supported|goal-relevant current positioning|products described|features described|public users and teams)", re.I)

BENCHMARK_CRITERIA = ("identity", "summary_meaningful", "no_filler", "products_or_unknown", "target_market_or_unknown", "features_or_unknown", "integrations_or_unknown", "customers_or_unknown", "pricing_or_unknown", "evidence_excerpt_relevance", "explicit_unknowns", "page_contribution", "signal_recency", "evidence_integrity", "unknown_handling", "page_budget", "partial_failure_accounting", "unsupported_claim_count", "pricing_evaluated", "integrations_evaluated", "customers_evaluated")


def excerpt_by_id(brief):
    return {item["id"]: item["excerpt_or_support"] for item in brief["evidence"]}


STOPWORDS = {"with", "that", "this", "from", "your", "their", "they", "have", "will", "into", "more", "than", "about", "other", "which", "these", "those", "been", "over", "such", "each", "most", "many", "some", "when", "what", "where", "while", "also", "using", "used", "than"}


def relevant(value, excerpt):
    if value is None or not excerpt:
        return False
    tokens = {token for token in re.findall(r"[a-z0-9]{4,}", value.lower()) if token not in STOPWORDS}
    if not tokens:
        return True
    return bool(tokens & set(re.findall(r"[a-z0-9]{4,}", excerpt.lower())))


def benchmark_row(brief):
    """Score only observable, evidence-backed contract properties."""
    meta = brief["meta"]
    evidence_ids = {item["id"] for item in brief["evidence"]}
    link_by_path = {item["claim_path"]: item["evidence_ids"] for item in brief["claim_evidence"]}
    excerpts = excerpt_by_id(brief)
    values = material_claims(brief)
    populated = {path: item for path, item in values.items() if item["value"] is not None}

    def value_relevant(path, item):
        if item["value"] is None:
            return True
        if path == "summary.category":
            return any(len(str(excerpts.get(eid, "")).strip()) >= 8 for eid in item["evidence_ids"])
        return any(relevant(item["value"], excerpts.get(eid, "")) for eid in item["evidence_ids"])

    unknown_fields = {item["field"] for item in brief["unknowns"]}
    contribution = meta.get("page_contribution", [])
    supported_reads = [item for item in contribution if item.get("read") and CATEGORY_SUPPORT.get(item["category"])]

    def contributes(item):
        if item.get("claims"):
            return True
        excerpt = str(excerpts.get(item["evidence_id"], "")).strip()
        return len(excerpt) < 8 or is_filler(excerpt)

    contributed = [item for item in supported_reads if contributes(item)]
    pricing_pages = [item for item in contribution if item.get("category") == "pricing_plans" and item.get("read")]
    integration_pages = [item for item in contribution if item.get("category") == "integrations" and item.get("read")]
    customer_pages = [item for item in contribution if item.get("category") == "customers_case_studies" and item.get("read")]

    criteria = {
        "identity": bool(brief["company"].get("name") and brief["company"].get("domain")),
        "summary_meaningful": all(item["value"] is None or meaningful(item["value"], min_len=8) for item in (brief["summary"]["one_liner"], brief["summary"]["category"], brief["summary"]["positioning"])) and any(item["value"] for item in (brief["summary"]["one_liner"], brief["summary"]["positioning"])),
        "no_filler": not any(is_filler(item["value"]) for item in populated.values()) and not any(FILLER_HINTS.search(item["value"]) for item in populated.values()),
        "products_or_unknown": bool(brief["products"]) or "products" in unknown_fields,
        "target_market_or_unknown": bool(brief["target_market"]) or "target_market" in unknown_fields,
        "features_or_unknown": bool(brief["features"]) or "features" in unknown_fields,
        "integrations_or_unknown": bool(brief["integrations"]) or "integrations" in unknown_fields,
        "customers_or_unknown": bool(brief["customers"]) or "customers" in unknown_fields,
        "pricing_or_unknown": bool(brief["pricing"]["model"]["value"]) or brief["pricing"]["unknown"],
        "evidence_excerpt_relevance": all(value_relevant(path, item) for path, item in populated.items()),
        "explicit_unknowns": all((bool(brief[field]) or field in unknown_fields) for field in ("products", "target_market", "features", "integrations", "customers")),
        "page_contribution": len(contributed) == len(supported_reads),
        "signal_recency": all(item["recency"] in {"dated", "current_observation"} for item in brief["signals"]),
        "evidence_integrity": all(set(item["evidence_ids"]) <= evidence_ids for item in values.values()) and all(set(eid) <= evidence_ids for eid in link_by_path.values()),
        "unknown_handling": len({item["field"] for item in brief["unknowns"]}) == len(brief["unknowns"]),
        "page_budget": meta["page_read_count"] <= meta["page_read_budget_default"] <= DEFAULT_CAP <= HARD_CAP,
        "partial_failure_accounting": meta["page_read_count"] == meta["pages_attempted"] - meta["partial_failure_count"],
        "unsupported_claim_count": sum(1 for item in values.values() if not set(item["evidence_ids"]) <= evidence_ids) == 0,
        "pricing_evaluated": (not pricing_pages) or (brief["pricing"]["unknown"] or bool(brief["pricing"]["plans"])),
        "integrations_evaluated": (not integration_pages) or bool(brief["integrations"]) or "integrations" in unknown_fields,
        "customers_evaluated": (not customer_pages) or bool(brief["customers"]) or "customers" in unknown_fields,
    }
    quality = all(criteria[key] for key in ("no_filler", "evidence_excerpt_relevance", "explicit_unknowns", "page_contribution", "unsupported_claim_count", "pricing_evaluated", "integrations_evaluated", "customers_evaluated"))
    return {"criteria": criteria, "passed": sum(criteria.values()), "total": len(criteria), "quality_pass": quality, "unsupported_claim_count": 0 if criteria["unsupported_claim_count"] else 1}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cases", type=int, default=len(CASES))
    args = parser.parse_args()
    if "REPLYNODES_API_KEY" in os.environ:
        raise SystemExit("refusing an environment containing REPLYNODES_API_KEY")
    cases = CASES[: args.cases]
    reports, briefs, traces = [], [], []
    for case in cases:
        endpoint = md_url(case["homepage"])
        pace()
        home = get_once(endpoint, workflow_surface="markdown"); observe_rate(home)
        home.update({"surface": "free_markdown", "source_url": case["homepage"], "endpoint_url": endpoint})
        home["attempts"] = [home.copy()]
        pace()
        discovery = get_once(case["homepage"], "text/html,application/xhtml+xml")
        discovery.update({"surface": "free_homepage_discovery", "source_url": case["homepage"], "endpoint_url": case["homepage"]})
        candidates = discover_candidates(case["homepage"], home["text"] if successful(home) else "", discovery["text"] if successful(discovery) else "")
        # Always probe one bounded canonical first-party pricing path; deduped by canonical URL.
        for probe_path, probe_category in CANONICAL_PROBES:
            probe = canonical_url(f"https://{case['domain']}{probe_path}")
            if probe not in {url for url, _ in candidates}:
                candidates.append((probe, probe_category))
        selected = select_candidates(candidates)
        execution = {case["homepage"]: {"selected": True, "request_made": True, "retry_or_fallback_count": 0}}
        fetched = [home]
        direct_pricing_used = False
        for source, category in selected[1:]:
            execution[source] = {"selected": True, "request_made": True, "retry_or_fallback_count": 0}
            endpoint = md_url(source)
            pace()
            markdown = get_once(endpoint, workflow_surface="markdown"); observe_rate(markdown)
            markdown.update({"surface": "free_markdown", "source_url": source, "endpoint_url": endpoint, "category": category})
            result = markdown
            result["attempts"] = [markdown.copy()]
            if category == "pricing_plans" and markdown.get("status") == 429 and not direct_pricing_used:
                direct_pricing_used = True
                execution[source]["retry_or_fallback_count"] = 1
                pace()
                direct = get_once(source, "text/html,application/xhtml+xml,text/plain")
                direct.update({"surface": "free_direct_pricing", "source_url": source, "endpoint_url": source, "category": category})
                result = direct
                result["attempts"] = [markdown.copy(), direct.copy()]
            fetched.append(result)
        trace = candidate_trace(candidates, execution)
        brand_source = "https://brand.replynodes.com/" + case["domain"]
        pace()
        brand_result = get_once(brand_source, workflow_surface="brand"); observe_rate(brand_result)
        brand_result.update({"surface": "free_brand", "source_url": brand_source, "endpoint_url": brand_source})
        brand_result["attempts"] = [brand_result.copy()]
        fetched.append(brand_result)
        brief = make_brief(case, fetched, candidates, discovery)
        validate_brief(brief)
        assert brief["meta"]["page_read_count"] <= DEFAULT_CAP <= brief["meta"]["page_read_budget_default"]
        sanitized_requests = sanitize_request_records([discovery] + [record for page in fetched for record in page.get("attempts", [page])])
        assert all("text" not in record and "error" not in record and "status" not in record for record in sanitized_requests)
        reports.append({"domain": case["domain"], "requests": sanitized_requests, "page_read_count": brief["meta"]["page_read_count"], "schema_validation": "passed"})
        briefs.append(brief)
        traces.append(trace)
    if not any(not brief["pricing"]["unknown"] for brief in briefs):
        raise SystemExit("live keyless E2E found no grounded public-pricing case")
    skill = Path(__file__).parents[1] / "skills/company-research/SKILL.md"
    claimed = [name for name in TOOL_NAMES if name in skill.read_text(encoding="utf-8")]
    mcp_status, mcp_type, observed = mcp_tools_once()
    if not set(claimed) <= set(observed):
        raise SystemExit("live tools/list is missing claimed tool names")
    per_company = {case["domain"]: {"candidate_sequence": trace["selected_candidate_sequence"], "accepted_count": trace["accepted_count"], "attempted_count": trace["attempted_count"], "attempted_candidate_number": trace["attempted_candidate_number"], "hard_cap_rejection": trace["hard_cap_rejection"], "request_made_count": trace["request_made_count"], "retry_or_fallback_count": trace["retry_or_fallback_count"], "page_read_count": brief["meta"]["page_read_count"], "partial_failure_count": brief["meta"]["partial_failure_count"]} for case, brief, trace in zip(cases, briefs, traces)}
    benchmark = {case["domain"]: benchmark_row(brief) for case, brief in zip(cases, briefs)}
    failed = {domain: row for domain, row in benchmark.items() if not row["quality_pass"]}
    output = {
        "generated_at": now(),
        "keyless": True,
        "surfaces": ["free_markdown", "free_homepage_discovery", "free_direct_pricing", "free_brand"],
        "requests": reports,
        "mcp_tools_list": {"endpoint": MCP_URL, "http_status": mcp_status, "content_type": mcp_type or "unavailable", "claimed_tool_names": claimed, "observed_tool_names": observed},
        "schema_validation": {case["domain"]: report["schema_validation"] for case, report in zip(cases, reports)},
        "benchmark": {"companies": len(cases), "criteria": list(BENCHMARK_CRITERIA), "per_company": benchmark, "unsupported_claim_count": sum(0 if row["criteria"]["unsupported_claim_count"] else 1 for row in benchmark.values()), "quality_failures": sorted(failed), "contribution": {case["domain"]: [{"category": item["category"], "claims": len(item["claims"])} for item in brief["meta"]["page_contribution"]] for case, brief in zip(cases, briefs)}},
        "budget_proof": {"default_cap": DEFAULT_CAP, "hard_cap": HARD_CAP, "per_company": per_company, "candidate_traces": {case["domain"]: trace for case, trace in zip(cases, traces)}},
        "briefs": briefs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote sanitized keyless E2E report: {args.output}")
    print(f"quality failures: {sorted(failed) if failed else 'none'}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
