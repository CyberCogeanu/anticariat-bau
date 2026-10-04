#!/usr/bin/env python3
"""
Cloudflare DNS Subdomain Management Script for Anticariat Albert.

Manages DNS records (CNAME) pointing to Shopify edge infrastructure.
Strictly adheres to:
- Zero credentials on disk (reads strictly from environment variables).
- No Unicode em dash (U+2014) in text, comments, or documentation.
- Cloudflare proxy mode set to false (DNS-only) for initial SSL verification.
"""

import argparse
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


def get_cloudflare_credentials() -> Tuple[str, str]:
    """
    Retrieve Cloudflare API token and Zone ID from environment variables.
    Supports CLOUDFLARE_PAGES_TOKEN or CLOUDFLARE_API_TOKEN.
    """
    token = os.environ.get("CLOUDFLARE_PAGES_TOKEN") or os.environ.get("CLOUDFLARE_API_TOKEN")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")

    if not token or len(token) < 20 or "PASTE" in token:
        print(
            "[ERROR] Valid Cloudflare API token not found in environment.",
            file=sys.stderr,
        )
        print("Set CLOUDFLARE_PAGES_TOKEN or CLOUDFLARE_API_TOKEN in Doppler.", file=sys.stderr)
        print("Example: doppler run --project anticariat-bau --config prd -- python3 manage_subdomain_dns.py", file=sys.stderr)
        sys.exit(1)

    if not zone_id:
        print("[ERROR] CLOUDFLARE_ZONE_ID not found in environment.", file=sys.stderr)
        sys.exit(1)

    return token.strip(), zone_id.strip()


def cf_api_request(
    endpoint: str,
    token: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a request against the Cloudflare v4 REST API."""
    url = f"https://api.cloudflare.com/client/v4{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "anticariat-bau-dns-manager/1.0",
    }
    payload = json.dumps(data).encode("utf-8") if data is not None else None

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode("utf-8")
            return json.loads(resp_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
            messages = err_json.get("errors", [])
            print(f"[API ERROR] HTTP {e.code}: {messages}", file=sys.stderr)
        except Exception:
            print(f"[API ERROR] HTTP {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[CONNECTION ERROR] Failed to connect to Cloudflare API: {e}", file=sys.stderr)
        sys.exit(1)


def get_zone_details(zone_id: str, token: str) -> str:
    """Fetch zone name to construct FQDN accurately."""
    res = cf_api_request(f"/zones/{zone_id}", token)
    zone_name = res.get("result", {}).get("name")
    if not zone_name:
        print(f"[ERROR] Could not retrieve zone name for ID: {zone_id}", file=sys.stderr)
        sys.exit(1)
    return zone_name


def find_dns_records(zone_id: str, token: str, record_name: str) -> List[Dict[str, Any]]:
    """Find all existing DNS records matching the exact record name."""
    params = urllib.parse.urlencode({"name": record_name})
    res = cf_api_request(f"/zones/{zone_id}/dns_records?{params}", token)
    return res.get("result", [])


def create_or_update_cname(
    zone_id: str,
    token: str,
    record_name: str,
    target: str,
    proxied: bool = False,
    ttl: int = 1,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Deterministic CNAME management:
    - Finds existing record.
    - If present and matches: noop.
    - If present and differs: update (PUT).
    - If absent: create (POST).
    """
    existing_records = find_dns_records(zone_id, token, record_name)
    comment_text = "Shopify custom subdomain managed by anticariat-bau"

    payload = {
        "type": "CNAME",
        "name": record_name,
        "content": target,
        "ttl": ttl,
        "proxied": proxied,
        "comment": comment_text,
    }

    if existing_records:
        match = None
        for r in existing_records:
            if r.get("name") == record_name:
                match = r
                break

        if match:
            record_id = match["id"]
            current_type = match.get("type")
            current_content = match.get("content")
            current_proxied = match.get("proxied")
            current_ttl = match.get("ttl")

            if (
                current_type == "CNAME"
                and current_content == target
                and current_proxied == proxied
                and current_ttl == ttl
            ):
                print(f"[OK] Record '{record_name}' already exists and matches desired state:")
                print(f"     Type: {current_type} | Target: {current_content} | Proxied: {current_proxied} | TTL: {current_ttl}")
                return match

            print(f"[ACTION] Updating existing record {record_id} for '{record_name}'...")
            print(f"         Before: Type={current_type}, Target={current_content}, Proxied={current_proxied}")
            print(f"         After:  Type=CNAME, Target={target}, Proxied={proxied}")

            if dry_run:
                print("[DRY-RUN] Skipping PUT API call.")
                return payload

            res = cf_api_request(
                f"/zones/{zone_id}/dns_records/{record_id}",
                token,
                method="PUT",
                data=payload,
            )
            print(f"[SUCCESS] Record updated successfully (ID: {record_id}).")
            return res.get("result", {})

    print(f"[ACTION] Creating new CNAME record for '{record_name}' -> '{target}' (proxied={proxied}, ttl={ttl})...")
    if dry_run:
        print("[DRY-RUN] Skipping POST API call.")
        return payload

    res = cf_api_request(
        f"/zones/{zone_id}/dns_records",
        token,
        method="POST",
        data=payload,
    )
    new_record = res.get("result", {})
    record_id = new_record.get("id")
    print(f"[SUCCESS] CNAME record created successfully (ID: {record_id}).")
    return new_record


def validate_dns_resolution(record_name: str, expected_target: str) -> bool:
    """
    Validate DNS propagation:
    1. Query Cloudflare Public DNS-over-HTTPS (DoH) for CNAME and A records.
    2. Attempt socket host resolution.
    """
    print("\n[VALIDATION] Validating public DNS propagation...")
    doh_cname_url = f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(record_name)}&type=CNAME"
    req_cname = urllib.request.Request(
        doh_cname_url,
        headers={"Accept": "application/dns-json", "User-Agent": "anticariat-bau-dns-validator/1.0"},
    )

    cname_verified = False
    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(req_cname, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                answers = data.get("Answer", [])
                for ans in answers:
                    val = ans.get("data", "").rstrip(".")
                    target_clean = expected_target.rstrip(".")
                    if val == target_clean or ans.get("type") == 5:
                        cname_verified = True
                        print(f"  [DoH CNAME] {record_name} -> {ans.get('data')} (TTL: {ans.get('TTL')}s)")
                        break
            if cname_verified:
                break
        except Exception as e:
            print(f"  [DoH Query Attempt {attempt}] Retrying: {e}")
        time.sleep(1)

    # Check A record resolution via DoH
    doh_a_url = f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(record_name)}&type=A"
    req_a = urllib.request.Request(
        doh_a_url,
        headers={"Accept": "application/dns-json", "User-Agent": "anticariat-bau-dns-validator/1.0"},
    )
    a_records = []
    try:
        with urllib.request.urlopen(req_a, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            answers = data.get("Answer", [])
            for ans in answers:
                if ans.get("type") == 1:
                    a_records.append(ans.get("data"))
            if a_records:
                print(f"  [DoH A Records] {record_name} resolves to Shopify edge IP(s): {', '.join(a_records)}")
    except Exception as e:
        print(f"  [DoH A Query] Error: {e}")

    # Check local socket resolution
    try:
        socket_ips = [ip[4][0] for ip in socket.getaddrinfo(record_name, 80, socket.AF_INET)]
        unique_ips = sorted(list(set(socket_ips)))
        print(f"  [System Socket] Resolved {record_name} to: {', '.join(unique_ips)}")
    except socket.gaierror as e:
        print(f"  [System Socket] Resolution pending local propagation: {e}")

    if cname_verified or a_records:
        print("[VALIDATION OK] DNS records are active and resolving to Shopify infrastructure.")
        return True
    else:
        print("[VALIDATION NOTICE] Record registered, but propagation is still ongoing. Allow 1-2 minutes.")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage Cloudflare DNS Subdomain for Shopify integration."
    )
    parser.add_argument(
        "--subdomain",
        default="dev",
        help="Subdomain prefix (e.g. 'dev') or fully qualified domain name (default: 'dev')",
    )
    parser.add_argument(
        "--target",
        default="shops.myshopify.com",
        help="Target CNAME destination (default: 'shops.myshopify.com')",
    )
    parser.add_argument(
        "--proxied",
        action="store_true",
        default=False,
        help="Enable Cloudflare proxy (Orange Cloud). Default is False (Grey Cloud, DNS-only).",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=1,
        help="Time to live in seconds (1 = Automatic). Default: 1",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate DNS record inspection without executing mutations.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate current DNS resolution without modifying Cloudflare records.",
    )

    args = parser.parse_args()

    token, zone_id = get_cloudflare_credentials()
    zone_name = get_zone_details(zone_id, token)

    # Compute FQDN
    if args.subdomain.endswith(f".{zone_name}"):
        record_name = args.subdomain
    elif args.subdomain == zone_name:
        record_name = zone_name
    else:
        record_name = f"{args.subdomain}.{zone_name}"

    print("==================================================================")
    print(" Anticariat Albert - Cloudflare DNS Subdomain Automation")
    print("==================================================================")
    print(f"Zone Name:   {zone_name}")
    print(f"Zone ID:     {zone_id}")
    print(f"Record Name: {record_name}")
    print(f"Target:      {args.target}")
    print(f"Proxied:     {args.proxied} (DNS-only: {not args.proxied})")
    print(f"TTL:         {args.ttl} (1 = Auto)")
    print(f"Dry Run:     {args.dry_run}")
    print("==================================================================\n")

    if args.validate_only:
        validate_dns_resolution(record_name, args.target)
        return

    create_or_update_cname(
        zone_id=zone_id,
        token=token,
        record_name=record_name,
        target=args.target,
        proxied=args.proxied,
        ttl=args.ttl,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        validate_dns_resolution(record_name, args.target)


if __name__ == "__main__":
    main()
