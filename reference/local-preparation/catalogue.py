"""Bounded explicit NASA import and offline, numerical game templates.

Only ``python3 catalogue.py --refresh`` performs network I/O. No model is used.
The raw upstream response is private; public evidence is a labelled projection.
"""
import argparse
import hashlib
import json
import os
import random
import re
import stat
import tempfile
import time
import urllib.request
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit

ENDPOINT = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
DOCS = "https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html"
CANDIDATES = ("Kepler-22 b", "Kepler-10 b", "HD 209458 b", "WASP-12 b", "TRAPPIST-1 e", "WASP-39 b")
FIELDS = {
    "pl_orbper": {"quantity": "orbital period", "unit": "days", "definition": "Time taken for one orbit, in days."},
    "pl_rade": {"quantity": "planetary radius", "unit": "Earth radii", "definition": "Planetary radius (not diameter), in Earth radii."},
    "pl_orbsmax": {"quantity": "orbital semi-major axis", "unit": "astronomical units", "definition": "Semi-major axis of the planetary orbit, in astronomical units (not instantaneous star distance)."},
}
COLUMNS = ("pl_name", "hostname", "default_flag", "pl_controv_flag", *[column for field in FIELDS for column in (field, field + "err1", field + "err2", field + "lim")], "pl_refname", "rowupdate")
QUERY = "select top 6 " + ",".join(COLUMNS) + " from ps where default_flag=1 and pl_controv_flag=0 and pl_name in (" + ",".join("'" + name + "'" for name in CANDIDATES) + ") order by pl_name"
REQUEST_URL = ENDPOINT + "?" + urlencode({"query": QUERY, "format": "json"})
CACHE = Path(__file__).resolve().parent / "data" / "nasa-ps-snapshot.json"
MAX_RESPONSE = 65536
MAX_CACHE = 131072
REFRESH = "Refresh locally with: python3 prototype/spot-the-fake/catalogue.py --refresh"


class CatalogueError(RuntimeError):
    pass


def fail(message):
    raise CatalogueError(message)


def strict_json(raw, decimal=False):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj: fail("Duplicate JSON key.")
            obj[key] = value
        return obj
    def constant(_): fail("Non-finite JSON number.")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant,
                          **({"parse_float": Decimal} if decimal else {}))
    except (ValueError, TypeError, RecursionError, InvalidOperation) as error:
        raise CatalogueError("Invalid JSON snapshot.") from error


def safe_text(value, maximum=160):
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or value != value.strip(): fail("Unsafe or missing source text.")
    if any(ord(c) < 32 or ord(c) > 126 for c in value) or any(c in value for c in "<>\\") or re.search(r"https?://|javascript:|data:", value, re.I): fail("Unsafe source text.")
    return value


def reference_url(url):
    if not isinstance(url, str) or len(url) > 400 or re.search(r"[\s<>\\%]", url): fail("Unsafe reference URL.")
    try:
        parts = urlsplit(url)
    except ValueError as error:
        raise CatalogueError("Unsafe reference URL.") from error
    approved_path = (parts.netloc == "ui.adsabs.harvard.edu" and re.fullmatch(r"/abs/[A-Za-z0-9.&+_-]+/abstract", parts.path)) or url == DOCS
    if parts.scheme != "https" or not approved_path or parts.fragment or parts.query: fail("Unapproved reference URL.")
    return url


class Reference(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []; self.url = None; self.opened = False; self.closed = False

    def handle_starttag(self, tag, attrs):
        # Archive pl_refname uses a single publication anchor; discard inert
        # target/refstr attributes but reject arbitrary markup/handlers.
        if tag != "a" or self.opened or set(k for k, _ in attrs) - {"href", "target", "refstr"} or len(dict(attrs)) != len(attrs): fail("Unsafe reference HTML.")
        values = dict(attrs)
        if values.get("target", "_blank") not in {"_blank", "ref"}: fail("Unsafe reference target.")
        if "refstr" in values: safe_text(values["refstr"], 240)
        self.url = reference_url(values.get("href")); self.opened = True

    def handle_endtag(self, tag):
        if tag != "a" or not self.opened or self.closed: fail("Unsafe reference HTML.")
        self.closed = True

    def handle_data(self, data):
        if (not self.opened or self.closed) and data.strip(): fail("Unexpected reference text outside anchor.")
        self.text.append(data)

    def handle_comment(self, data): fail("Unsafe reference HTML.")
    def handle_decl(self, decl): fail("Unsafe reference HTML.")
    def handle_pi(self, data): fail("Unsafe reference HTML.")
    def handle_startendtag(self, tag, attrs): fail("Unsafe reference HTML.")


def parse_reference(raw):
    if not isinstance(raw, str) or len(raw) > 1200: fail("Missing or oversized reference.")
    parser = Reference()
    try:
        parser.feed(raw); parser.close()
    except (ValueError, RecursionError) as error:
        raise CatalogueError("Invalid reference HTML.") from error
    if not parser.opened or not parser.closed: fail("Missing publication reference.")
    return safe_text("".join(parser.text).strip(), 240), parser.url


def valid_date(value):
    try:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value): fail("Invalid source date.")
        parsed = date.fromisoformat(value)
        if parsed < date(1990, 1, 1) or parsed > datetime.now(timezone.utc).date(): fail("Invalid source date.")
    except ValueError as error:
        raise CatalogueError("Invalid source date.") from error
    return value


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)): fail("Measurement must be a JSON number.")
    result = Decimal(value)
    if not result.is_finite() or (result != 0 and not Decimal("1e-15") <= abs(result) <= Decimal("1e15")): fail("Non-finite or out-of-range measurement.")
    if len(result.as_tuple().digits) > 24 or abs(result.as_tuple().exponent) > 30: fail("Unsupported numeric precision.")
    return result


def format_number(value):
    # Exact decimal scalar, no rounding or unit conversion. Explicitly cap
    # numeric range above to avoid enormous/scientific display ambiguities.
    with localcontext() as context:
        context.prec = 50
        rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def measurement(row, field):
    value = number(row[field]); upper = number(row[field + "err1"]); lower = number(row[field + "err2"])
    limit = row[field + "lim"]
    if type(limit) is not int or limit != 0 or value <= 0 or upper < 0 or lower > 0 or value + lower <= 0: fail("Ineligible uncertainty/limit.")
    altered = value * 2
    # Exact decimal rendering has zero rounding tolerance. Require a strict
    # >10-error gap; uncertainty is not represented as a hard truth boundary.
    if altered > Decimal("1e15") or abs(altered - value) <= 10 * max(upper, abs(lower)) or format_number(altered) == format_number(value): fail("Mutation too close to reported error.")
    return {"field": field, "value": value, "upper": upper, "lower": lower, "altered": altered}


def normalize(raw):
    rows = strict_json(raw, decimal=True)
    if not isinstance(rows, list) or not 3 <= len(rows) <= 6: fail("Expected three to six catalogue rows.")
    eligible = []; seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(COLUMNS): fail("Unexpected catalogue row schema.")
        name = safe_text(row["pl_name"]); host = safe_text(row["hostname"])
        if name not in CANDIDATES or name in seen or host != name.rsplit(" ", 1)[0]: fail("Unexpected or duplicate planet/default row.")
        seen.add(name)
        if type(row["default_flag"]) is not int or row["default_flag"] != 1 or type(row["pl_controv_flag"]) is not int or row["pl_controv_flag"] != 0: fail("Unexpected default/controversy flags.")
        ref, url = parse_reference(row["pl_refname"]); update = valid_date(row["rowupdate"])
        try:
            measures = [measurement(row, field) for field in FIELDS]
        except CatalogueError:
            # Null/missing errors, limits, or large uncertainty make this planet
            # ineligible, never a fabricated or zero-error replacement.
            continue
        eligible.append({"name": name, "host": host, "reference": ref, "reference_url": url, "rowupdate": update, "measurements": measures})
    if len(eligible) < 3: fail("Fewer than three eligible planets; old cache preserved.")
    return eligible


def envelope(raw, retrieved_at):
    return {"schema_version": 1, "template_version": 1, "source": "NASA Exoplanet Archive", "table": "ps", "request_url": REQUEST_URL, "query": QUERY, "documentation_url": DOCS, "retrieved_at": retrieved_at, "fields": FIELDS, "raw_response": raw, "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()}


def validate_snapshot(snapshot):
    expected = set(envelope("", ""))
    if not isinstance(snapshot, dict) or set(snapshot) != expected: fail("Unexpected snapshot schema.")
    for key, value in envelope("", "").items():
        if key not in {"raw_response", "sha256", "retrieved_at"} and (snapshot[key] != value or type(snapshot[key]) is not type(value)): fail("Unsupported snapshot metadata: " + key)
    timestamp = snapshot["retrieved_at"]
    try:
        if not isinstance(timestamp, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", timestamp): fail("Invalid retrieval timestamp.")
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed < datetime(2020, 1, 1, tzinfo=timezone.utc) or parsed > datetime.now(timezone.utc): fail("Invalid retrieval timestamp.")
    except ValueError as error:
        raise CatalogueError("Invalid retrieval timestamp.") from error
    raw = snapshot["raw_response"]
    if not isinstance(raw, str) or not 1 <= len(raw.encode("utf-8")) <= MAX_RESPONSE: fail("Invalid response size.")
    if snapshot["sha256"] != hashlib.sha256(raw.encode("utf-8")).hexdigest(): fail("Snapshot integrity check failed.")
    planets = normalize(raw)
    if any(row["rowupdate"] > timestamp[:10] for row in strict_json(raw, decimal=True)): fail("Source record is newer than its snapshot.")
    return planets


def safe_target(path):
    path = Path(path)
    # Reject symlink parents as well as the leaf. The active cache path is fixed;
    # an explicit internal path parameter exists only for isolated unit tests.
    for parent in (path, *path.parents):
        if parent.is_symlink(): fail("Refusing symlink cache target.")
    if path.exists() and not path.is_file(): fail("Unexpected cache target.")
    if path.exists() and path.stat().st_nlink != 1: fail("Refusing multiply linked cache target.")
    if path.parent.exists() and not path.parent.is_dir(): fail("Unexpected cache directory.")
    return path


def load_snapshot(path=CACHE):
    try:
        path = safe_target(path)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode): fail("Unexpected cache target.")
            data = source.read(MAX_CACHE + 1)
        if len(data) > MAX_CACHE: fail("Snapshot exceeds size ceiling.")
        snapshot = strict_json(data.decode("utf-8"))
        planets = validate_snapshot(snapshot)
        return snapshot, planets
    except (OSError, UnicodeError, CatalogueError) as error:
        raise CatalogueError("NASA snapshot unavailable or invalid. " + REFRESH) from error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fail("NASA importer refuses all redirects.")


def fetch_response():
    request = urllib.request.Request(REQUEST_URL, headers={"Accept": "application/json", "User-Agent": "GhostProof-local-snapshot/1"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=15) as response:
            if response.status != 200 or response.geturl() != REQUEST_URL: fail("Unexpected NASA response endpoint/status.")
            if response.headers.get_content_type() != "application/json": fail("NASA JSON content type required.")
            data = response.read(MAX_RESPONSE + 1)
        if len(data) > MAX_RESPONSE: fail("NASA response exceeds size ceiling.")
        return data.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise CatalogueError("NASA import failed; no retry or cache replacement.") from error


def refresh(path=CACHE):
    path = safe_target(path)
    raw = fetch_response()  # Exactly one bounded request; no automatic retries.
    snapshot = envelope(raw, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    planets = validate_snapshot(snapshot)
    encoded = json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8")
    if len(encoded) > MAX_CACHE: fail("Snapshot exceeds cache ceiling.")
    temporary = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        safe_target(path)
        fd, temporary = tempfile.mkstemp(prefix=".nasa-ps-", dir=path.parent)
        with os.fdopen(fd, "wb") as output:
            output.write(encoded); output.flush(); os.fsync(output.fileno())
        # Validate bytes actually written before same-directory atomic commit.
        load_snapshot(temporary)
        safe_target(path)
        os.replace(temporary, path); temporary = None
    except OSError as error:
        raise CatalogueError("Snapshot write failed; old cache preserved.") from error
    finally:
        if temporary is not None: Path(temporary).unlink(missing_ok=True)
    return snapshot, planets


def render(name, field, value):
    spec = FIELDS[field]
    return f"The catalogue lists {name}'s {spec['quantity']} as {format_number(value)} {spec['unit']}."


def validate_round(packet, planet):
    claims = packet["claims"]
    if len(claims) != 3 or {c["field"] for c in claims} != set(FIELDS) or any(type(c["is_false"]) is not bool for c in claims) or sum(c["is_false"] for c in claims) != 1: fail("Invalid one-fake invariant.")
    if len({c["text"] for c in claims}) != 3 or any(len(c["text"]) > 200 for c in claims): fail("Invalid distinct claim rendering.")
    if len(packet["sources"]) != 1 or packet["sources"][0]["id"] != "S1" or packet["sources"][0]["url"] != REQUEST_URL: fail("Invalid source mapping.")
    measures = {m["field"]: m for m in planet["measurements"]}
    for claim in claims:
        m = measures[claim["field"]]
        original = render(planet["name"], m["field"], m["value"])
        expected = render(planet["name"], m["field"], m["altered"] if claim["is_false"] else m["value"])
        if claim["text"] != expected or claim["correction"] != (original if claim["is_false"] else "") or claim["source_id"] != "S1": fail("Invalid rendered mutation/correction.")
        if (claim["text"] != original) != claim["is_false"]: fail("More than one changed rendering.")
        spec = FIELDS[m["field"]]
        expected_evidence = {"field": m["field"], "quantity": spec["quantity"], "value": format_number(m["value"]), "unit": spec["unit"], "error_upper": format_number(m["upper"]), "error_lower": format_number(m["lower"]), "limit": 0, "definition": spec["definition"], "documentation_url": DOCS, "reference": planet["reference"], "reference_url": planet["reference_url"], "row_updated": planet["rowupdate"]}
        if claim["evidence"] != expected_evidence: fail("Invalid field evidence.")


def generate_round(excluded, phase, cancelled):
    started = time.monotonic()
    if cancelled(): fail("Cached round cancelled.")
    phase("Reading cached NASA data")
    snapshot, planets = load_snapshot()
    choices = [planet for planet in planets if planet["name"] not in excluded]
    if not choices: fail("No unused planet in this hunt. Start a fresh hunt.")
    rng = random.SystemRandom(); planet = rng.choice(choices); fake_field = rng.choice(tuple(FIELDS))
    phase("Checking the numbers")
    source = {"id": "S1", "title": "Retained Planetary Systems query · " + planet["name"], "publisher": "NASA Exoplanet Archive", "url": REQUEST_URL, "retrieved_at": snapshot["retrieved_at"]}
    claims = []
    for m in planet["measurements"]:
        field = m["field"]; spec = FIELDS[field]; is_false = field == fake_field
        original = render(planet["name"], field, m["value"])
        claims.append({"field": field, "text": render(planet["name"], field, m["altered"] if is_false else m["value"]), "is_false": is_false,
                       "correction": original if is_false else "", "source_id": "S1",
                       "explanation": "The fake doubled this one catalogue value; the quantity and units were left unchanged." if is_false else "This matches the retained catalogue value.",
                       "evidence": {"field": field, "quantity": spec["quantity"], "value": format_number(m["value"]), "unit": spec["unit"], "error_upper": format_number(m["upper"]), "error_lower": format_number(m["lower"]), "limit": 0, "definition": spec["definition"], "documentation_url": DOCS, "reference": planet["reference"], "reference_url": planet["reference_url"], "row_updated": planet["rowupdate"]}})
    rng.shuffle(claims)
    packet = {"topic": planet["name"], "claims": claims, "sources": [source], "seconds": round(time.monotonic() - started, 3), "pool_size": len(planets)}
    validate_round(packet, planet)
    if cancelled(): fail("Cached round cancelled.")
    return packet


def main():
    parser = argparse.ArgumentParser(description="Explicit local NASA snapshot importer; no inference.")
    parser.add_argument("--refresh", action="store_true", required=True)
    parser.parse_args()
    try:
        snapshot, planets = refresh()
    except CatalogueError as error:
        parser.exit(1, str(error) + "\n")
    print(json.dumps({"request_url": snapshot["request_url"], "retrieved_at": snapshot["retrieved_at"], "sha256": snapshot["sha256"], "eligible_planets": [p["name"] for p in planets]}, indent=2))


if __name__ == "__main__": main()
