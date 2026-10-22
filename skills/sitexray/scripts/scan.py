#!/usr/bin/env python3
"""Run an authorized passive website scan through https://sitexray.net."""

import argparse
import ipaddress
import json
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

API_URL = "https://sitexray.net/api/scan"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def normalize_url(value):
    value = value.strip()
    if len(value) > 300 or not value:
        raise ValueError("Provide a public website URL of at most 300 characters.")
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise ValueError("Invalid website URL.") from error
    try:
        ipaddress.ip_address(parsed.hostname or "")
    except ValueError:
        pass
    else:
        raise ValueError("Use a public domain, not an IP address.")
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or "." not in parsed.hostname
        or parsed.hostname.endswith((".local", ".localhost"))
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or port not in (None, 80, 443)
        or any(ord(char) < 32 for char in value)
    ):
        raise ValueError("Use a public HTTP(S) domain without credentials, query parameters or fragments, on port 80 or 443.")
    return value


def scan(url, authorized=False, locale="en"):
    if not authorized:
        raise ValueError("Pass --authorized only when the user owns or has permission to test this website.")
    target = normalize_url(url)
    request = Request(
        API_URL,
        data=json.dumps({"url": target, "authorized": True}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SiteXraySkill/1.0 (+https://sitexray.net/skill)",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as error:
        if error.code == 429:
            wait = error.headers.get("Retry-After", "8")
            raise RuntimeError("Rate limited. Wait at least {} seconds before a user-requested retry.".format(wait)) from error
        try:
            message = json.loads(error.read(4096)).get("message", "scan_failed")
        except (ValueError, AttributeError):
            message = "scan_failed"
        raise RuntimeError("SiteXray HTTP {}: {}".format(error.code, message)) from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("SiteXray returned an unexpectedly large response.")
    try:
        envelope = json.loads(raw)
    except ValueError as error:
        raise RuntimeError("SiteXray did not return JSON.") from error
    if not isinstance(envelope, dict) or envelope.get("code") != 0:
        raise RuntimeError("SiteXray did not complete the scan.")
    report = envelope.get("data")
    if not isinstance(report, dict) or not isinstance(report.get("findings"), list):
        raise RuntimeError("SiteXray returned an invalid report.")
    report_url = None
    report_id = report.get("id")
    if isinstance(report_id, str):
        try:
            identifier = uuid.UUID(report_id)
            if identifier.version == 4:
                prefix = "/zh" if locale == "zh" else ""
                report_url = "https://sitexray.net{}/report/{}".format(prefix, identifier)
        except ValueError:
            pass
    return {**report, "reportUrl": report_url}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Public domain or HTTP(S) URL to check")
    parser.add_argument("--authorized", action="store_true", help="The user owns, manages or has permission to test the target")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    parser.add_argument("--locale", choices=("en", "zh"), default="en", help="Language of the shareable report link")
    args = parser.parse_args(argv)
    try:
        report = scan(args.url, authorized=args.authorized, locale=args.locale)
    except (ValueError, RuntimeError, URLError, TimeoutError, OSError) as error:
        print("SiteXray: {}".format(error), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("{} — {} / 100 ({})".format(report.get("target", args.url), report.get("score", "?"), report.get("grade", "?")))
        print("Scanned: {}".format(report.get("scannedAt", "unknown")))
        for finding in report["findings"]:
            print("- [{}] {}".format(finding.get("severity", "info"), finding.get("id", "unknown")))
        print("Report: {}".format(report["reportUrl"] or "Not saved; no share link is available."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
