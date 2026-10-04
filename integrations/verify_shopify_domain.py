#!/usr/bin/env python3
"""
Shopify Domain Status & Connectivity Verification Script.

Queries Shopify Admin GraphQL API to inspect attached custom domains,
monitors SSL activation, and tests live HTTPS connectivity.

Strictly adheres to:
- Zero credentials on disk (reads strictly from environment variables).
- No Unicode em dash (U+2014) in text, comments, or documentation.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


def get_shopify_credentials() -> Tuple[str, str, str]:
    """
    Retrieve Shopify shop domain, Admin API token, and API version.
    Supports direct token or OAuth client credentials exchange.
    """
    shop_domain = os.environ.get("SHOPIFY_STORE_DOMAIN") or os.environ.get("SHOPIFY_SHOP_DOMAIN")
    admin_token = os.environ.get("SHOPIFY_ADMIN_ACCESS_TOKEN") or os.environ.get("SHOPIFY_ADMIN_API_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")
    api_version = os.environ.get("SHOPIFY_API_VERSION", "2025-01")

    if not shop_domain:
        print("[ERROR] Missing store domain. Please set SHOPIFY_SHOP_DOMAIN or SHOPIFY_STORE_DOMAIN.", file=sys.stderr)
        print("Example: doppler run --project anticariat-bau --config prd -- python3 verify_shopify_domain.py", file=sys.stderr)
        sys.exit(1)

    shop_domain = shop_domain.replace("https://", "").replace("http://", "").strip("/")

    # Detect if client secret was mistakenly placed in admin token
    if admin_token and admin_token.startswith("shpss_"):
        if not client_secret:
            client_secret = admin_token
        admin_token = None

    if not admin_token:
        if client_id and client_secret:
            oauth_url = f"https://{shop_domain}/admin/oauth/access_token"
            payload = urllib.parse.urlencode({
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }).encode("utf-8")

            req = urllib.request.Request(
                oauth_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    admin_token = resp_data.get("access_token")
            except Exception as e:
                print(f"[AUTH ERROR] Failed to obtain access token via OAuth: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("[ERROR] Missing credentials. Provide SHOPIFY_ADMIN_API_TOKEN or SHOPIFY_CLIENT_ID + SHOPIFY_CLIENT_SECRET.", file=sys.stderr)
            sys.exit(1)

    return shop_domain, admin_token, api_version


def query_shopify_domains(shop_domain: str, admin_token: str, api_version: str) -> Dict[str, Any]:
    """Execute GraphQL query to retrieve shop domains and primary domain."""
    graphql_query = """
    {
      shop {
        name
        myshopifyDomain
        primaryDomain {
          host
          sslEnabled
          url
        }
        domains {
          host
          sslEnabled
          url
        }
      }
    }
    """
    url = f"https://{shop_domain}/admin/api/{api_version}/graphql.json"
    req = urllib.request.Request(
        url,
        data=json.dumps({"query": graphql_query}).encode("utf-8"),
        headers={
            "X-Shopify-Access-Token": admin_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "anticariat-bau-domain-verifier/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def probe_https_connectivity(target_host: str) -> Dict[str, Any]:
    """Perform HTTPS probe to test edge web server response."""
    url = f"https://{target_host}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AnticariatDomainVerifier/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")

    result = {
        "url": url,
        "reachable": False,
        "status_code": None,
        "ssl_verified": False,
        "server_header": None,
        "location": None,
        "error": None,
    }

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result["reachable"] = True
            result["status_code"] = resp.getcode()
            result["ssl_verified"] = True
            result["server_header"] = resp.headers.get("Server")
            result["location"] = resp.headers.get("Location")
    except urllib.error.HTTPError as e:
        result["reachable"] = True
        result["status_code"] = e.code
        result["ssl_verified"] = True
        result["server_header"] = e.headers.get("Server")
        result["location"] = e.headers.get("Location")
    except Exception as e:
        result["error"] = str(e)

    return result


def inspect_domain_status(
    shop_domain: str,
    admin_token: str,
    api_version: str,
    target_domain: str,
) -> Tuple[bool, bool, Dict[str, Any]]:
    """
    Inspect shop domains for target_domain.
    Returns (domain_bound, ssl_active, details).
    """
    res = query_shopify_domains(shop_domain, admin_token, api_version)
    shop_data = res.get("data", {}).get("shop", {})
    primary_domain = shop_data.get("primaryDomain", {})
    domains_list = shop_data.get("domains", [])

    is_primary = primary_domain.get("host") == target_domain
    matched_domain = None

    for d in domains_list:
        if d.get("host") == target_domain:
            matched_domain = d
            break

    domain_bound = matched_domain is not None
    ssl_active = bool(matched_domain and matched_domain.get("sslEnabled"))

    details = {
        "shop_name": shop_data.get("name"),
        "myshopify_domain": shop_data.get("myshopifyDomain"),
        "primary_domain": primary_domain,
        "all_domains": domains_list,
        "target_domain": target_domain,
        "is_bound": domain_bound,
        "is_primary": is_primary,
        "ssl_enabled": ssl_active,
    }
    return domain_bound, ssl_active, details


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify Shopify Custom Domain status and connectivity."
    )
    parser.add_argument(
        "--domain",
        default="dev.anticariatalbert.com",
        help="Target custom domain to verify (default: 'dev.anticariatalbert.com')",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch/poll continuously until domain is bound and SSL is active.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Polling interval in seconds when using --watch (default: 10s)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximum timeout in seconds for --watch (default: 300s)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON format.",
    )

    args = parser.parse_args()

    shop_domain, admin_token, api_version = get_shopify_credentials()
    target_domain = args.domain.strip()

    start_time = time.time()
    iteration = 0

    while True:
        iteration += 1
        domain_bound, ssl_active, details = inspect_domain_status(
            shop_domain, admin_token, api_version, target_domain
        )
        probe_result = probe_https_connectivity(target_domain)
        details["https_probe"] = probe_result

        if args.json:
            print(json.dumps(details, indent=2))
        else:
            print("==================================================================")
            print(" Shopify Domain Verification Status")
            print("==================================================================")
            print(f"Shop Name:        {details.get('shop_name')}")
            print(f"Shopify Domain:   {details.get('myshopify_domain')}")
            print(f"Target Domain:    {target_domain}")
            print(f"Bound in Shopify: {'YES' if domain_bound else 'NO (Pending merchant connection in Admin)'}")
            print(f"SSL Status:       {'ACTIVE' if ssl_active else 'PENDING / INACTIVE'}")
            print(f"Primary Domain:   {'YES' if details.get('is_primary') else 'NO'}")
            print("------------------------------------------------------------------")
            print(f"All Attached Domains in Shopify:")
            for d in details.get("all_domains", []):
                host = d.get("host")
                ssl = "SSL OK" if d.get("sslEnabled") else "No SSL"
                is_p = " [PRIMARY]" if host == details.get("primary_domain", {}).get("host") else ""
                print(f"  - {host} ({ssl}){is_p}")
            print("------------------------------------------------------------------")
            print("Direct HTTPS Edge Probe:")
            print(f"  Target URL:     {probe_result.get('url')}")
            print(f"  Reachable:      {probe_result.get('reachable')}")
            print(f"  HTTP Status:    {probe_result.get('status_code')}")
            print(f"  Server Header:  {probe_result.get('server_header')}")
            if probe_result.get("error"):
                print(f"  Probe Error:    {probe_result.get('error')}")
            print("==================================================================")

        if not args.watch:
            break

        if domain_bound and ssl_active:
            print("\n[SUCCESS] Domain is bound in Shopify and SSL is active!")
            break

        elapsed = time.time() - start_time
        if elapsed >= args.timeout:
            print(f"\n[TIMEOUT] Reached timeout of {args.timeout}s waiting for domain verification.")
            break

        print(f"\n[POLL {iteration}] Re-checking in {args.interval}s... (Elapsed: {int(elapsed)}s / {args.timeout}s)")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
