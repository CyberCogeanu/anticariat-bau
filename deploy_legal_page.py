#!/usr/bin/env python3
"""
Deploy Legal 'Termeni si Conditii' Page to Shopify via Admin GraphQL API.

Deterministically creates or updates the legal terms page on Shopify.
Zero credential files on disk: strictly consumes environment variables
injected via Doppler or runtime environment.

Mandatory rules:
- No Unicode em dash (U+2014) in text, comments, or documentation.
- Idempotent: checks for existing handle 'termeni-si-conditii' and updates if present.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def get_shopify_credentials() -> Tuple[str, str]:
    """
    Retrieve and validate Shopify credentials from environment variables.
    Supports direct Admin API token or OAuth client credentials exchange.
    """
    shop_domain = os.environ.get("SHOPIFY_STORE_DOMAIN") or os.environ.get("SHOPIFY_SHOP_DOMAIN")
    admin_token = os.environ.get("SHOPIFY_ADMIN_ACCESS_TOKEN") or os.environ.get("SHOPIFY_ADMIN_API_TOKEN")
    client_id = os.environ.get("SHOPIFY_CLIENT_ID")
    client_secret = os.environ.get("SHOPIFY_CLIENT_SECRET")

    if not shop_domain:
        print(
            "[ERROR] Missing store domain. Please set SHOPIFY_STORE_DOMAIN or SHOPIFY_SHOP_DOMAIN.",
            file=sys.stderr,
        )
        print("Example: doppler run --project anticariat-bau --config prd -- python3 deploy_legal_page.py", file=sys.stderr)
        sys.exit(1)

    # Clean domain if full URL was provided
    shop_domain = shop_domain.replace("https://", "").replace("http://", "").strip("/")

    # Detect if client secret was mistakenly placed in admin token
    if admin_token and admin_token.startswith("shpss_"):
        if not client_secret:
            client_secret = admin_token
        admin_token = None

    # Perform OAuth client credentials exchange if direct token is absent
    if not admin_token:
        if client_id and client_secret:
            print("[AUTH] Exchanging client_id and client_secret for Admin API access token...")
            oauth_url = f"https://{shop_domain}/admin/oauth/access_token"
            payload = urllib.parse.urlencode({
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }).encode("utf-8")

            req = urllib.request.Request(
                oauth_url,
                data=payload,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    admin_token = resp_data.get("access_token")
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                print(f"[AUTH ERROR] OAuth exchange failed ({e.code}): {err_body}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"[AUTH ERROR] Failed to connect to Shopify OAuth: {e}", file=sys.stderr)
                sys.exit(1)

            if not admin_token:
                print("[AUTH ERROR] OAuth response did not contain access_token.", file=sys.stderr)
                sys.exit(1)
            print("[AUTH] Successfully acquired access token via Client Credentials.")
        else:
            print(
                "[ERROR] Missing credentials. Please provide SHOPIFY_ADMIN_ACCESS_TOKEN or SHOPIFY_CLIENT_ID + SHOPIFY_CLIENT_SECRET.",
                file=sys.stderr,
            )
            sys.exit(1)

    return shop_domain, admin_token


def execute_graphql(
    shop_domain: str,
    access_token: str,
    query: str,
    variables: Optional[Dict[str, Any]] = None,
    api_version: str = "2025-01",
) -> Dict[str, Any]:
    """Execute a GraphQL query/mutation against the Shopify Admin API."""
    url = f"https://{shop_domain}/admin/api/{api_version}/graphql.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw_body = resp.read().decode("utf-8")
            return json.loads(raw_body)
    except urllib.error.HTTPError as e:
        raw_err = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(raw_err)
            return err_json
        except Exception:
            return {"errors": [{"message": f"HTTP {e.code}: {raw_err}"}]}
    except Exception as e:
        return {"errors": [{"message": f"Network exception: {str(e)}"}]}


def check_app_access_scopes(shop_domain: str, token: str, api_version: str) -> Set[str]:
    """Query current app installation to inspect granted access scopes."""
    query = """
    {
      currentAppInstallation {
        accessScopes {
          handle
        }
      }
    }
    """
    res = execute_graphql(shop_domain, token, query, api_version=api_version)
    scopes = set()
    data = res.get("data", {}) or {}
    app_inst = data.get("currentAppInstallation") or {}
    for scope_item in app_inst.get("accessScopes", []):
        scopes.add(scope_item.get("handle"))
    return scopes


def extract_body_content(html_content: str, raw_mode: bool = False) -> str:
    """
    Extract relevant styled content for Shopify page body.
    In Liquid templates, injecting <!DOCTYPE html><body> tags can distort the layout.
    We extract <style>...</style> and <article>...</article> seamlessly.
    """
    if raw_mode:
        return html_content

    # Extract style block if present
    style_match = re.search(r"(<style[\s\S]*?</style>)", html_content, re.IGNORECASE)
    style_block = style_match.group(1).strip() if style_match else ""

    # Extract article or body content
    article_match = re.search(r"(<article[\s\S]*?</article>)", html_content, re.IGNORECASE)
    if article_match:
        body_block = article_match.group(1).strip()
    else:
        body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", html_content, re.IGNORECASE)
        body_block = body_match.group(1).strip() if body_match else html_content.strip()

    if style_block and not body_block.startswith("<style"):
        return f"{style_block}\n\n{body_block}"
    return body_block


def print_scope_guidance() -> None:
    """Print actionable instructions for enabling required Shopify scopes."""
    print("\n" + "=" * 76, file=sys.stderr)
    print("[PERMISSION NOTICE] Required Shopify access scopes: 'read_content' & 'write_content'", file=sys.stderr)
    print("Online Store Pages in Shopify require the content permission scopes.", file=sys.stderr)
    print("\nHow to enable in Shopify Admin:", file=sys.stderr)
    print("1. Log in to Shopify Admin -> Settings -> Apps and sales channels", file=sys.stderr)
    print("2. Click 'Develop apps' and open your custom app (e.g. Anticariat Migration / BAU)", file=sys.stderr)
    print("3. Click 'Configuration' tab -> 'Admin API integration' -> 'Edit'", file=sys.stderr)
    print("4. Scroll to 'Online Store' -> Check 'read_content' and 'write_content'", file=sys.stderr)
    print("5. Click 'Save' (and re-authorize or reinstall if prompted)", file=sys.stderr)
    print("=" * 76 + "\n", file=sys.stderr)


def find_existing_page(shop_domain: str, token: str, handle: str, api_version: str) -> Optional[Dict[str, Any]]:
    """Query Shopify to find if a page with the given handle already exists."""
    query = """
    query FindLegalPage($query: String!) {
      pages(first: 5, query: $query) {
        edges {
          node {
            id
            title
            handle
            isPublished
            createdAt
            updatedAt
          }
        }
      }
    }
    """
    res = execute_graphql(shop_domain, token, query, {"query": f"handle:{handle}"}, api_version)

    if "errors" in res and res["errors"]:
        err_msg = str(res["errors"])
        if "Access denied for pages field" in err_msg or "ACCESS_DENIED" in err_msg or "read_content" in err_msg:
            print_scope_guidance()
            sys.exit(1)
        raise RuntimeError(f"GraphQL error while finding page: {res['errors']}")

    data = res.get("data", {}) or {}
    pages = data.get("pages", {}).get("edges", [])
    for edge in pages:
        node = edge.get("node", {})
        if node.get("handle") == handle:
            return node
    return None


def create_or_update_page(
    shop_domain: str,
    token: str,
    title: str,
    handle: str,
    body_html: str,
    api_version: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Create or update a legal page in Shopify via GraphQL mutations."""
    existing_page = find_existing_page(shop_domain, token, handle, api_version)

    if existing_page:
        page_id = existing_page["id"]
        print(f"[FOUND] Existing page found with handle '{handle}': {page_id}")
        if dry_run:
            print(f"[DRY-RUN] Would update page {page_id} with title '{title}' ({len(body_html)} characters).")
            return {"dry_run": True, "action": "update", "id": page_id, "handle": handle}

        mutation = """
        mutation UpdateLegalPage($id: ID!, $page: PageUpdateInput!) {
          pageUpdate(id: $id, page: $page) {
            page {
              id
              title
              handle
              isPublished
              updatedAt
            }
            userErrors {
              field
              message
              code
            }
          }
        }
        """
        variables = {
            "id": page_id,
            "page": {
                "title": title,
                "body": body_html,
                "isPublished": True,
            },
        }
        res = execute_graphql(shop_domain, token, mutation, variables, api_version)
        if "errors" in res and res["errors"]:
            err_msg = str(res["errors"])
            if "ACCESS_DENIED" in err_msg or "write_content" in err_msg:
                print_scope_guidance()
                sys.exit(1)
            raise RuntimeError(f"GraphQL error during pageUpdate: {res['errors']}")

        update_data = res.get("data", {}).get("pageUpdate", {})
        user_errors = update_data.get("userErrors", [])
        if user_errors:
            raise RuntimeError(f"Shopify pageUpdate user errors: {user_errors}")
        return update_data.get("page", {})
    else:
        print(f"[NOT FOUND] No existing page with handle '{handle}'. Creating new page...")
        if dry_run:
            print(f"[DRY-RUN] Would create new page with handle '{handle}', title '{title}' ({len(body_html)} characters).")
            return {"dry_run": True, "action": "create", "handle": handle}

        mutation = """
        mutation CreateLegalPage($page: PageCreateInput!) {
          pageCreate(page: $page) {
            page {
              id
              title
              handle
              isPublished
              createdAt
            }
            userErrors {
              field
              message
              code
            }
          }
        }
        """
        variables = {
            "page": {
                "title": title,
                "handle": handle,
                "body": body_html,
                "isPublished": True,
            },
        }
        res = execute_graphql(shop_domain, token, mutation, variables, api_version)
        if "errors" in res and res["errors"]:
            err_msg = str(res["errors"])
            if "ACCESS_DENIED" in err_msg or "write_content" in err_msg:
                print_scope_guidance()
                sys.exit(1)
            raise RuntimeError(f"GraphQL error during pageCreate: {res['errors']}")

        create_data = res.get("data", {}).get("pageCreate", {})
        user_errors = create_data.get("userErrors", [])
        if user_errors:
            raise RuntimeError(f"Shopify pageCreate user errors: {user_errors}")
        return create_data.get("page", {})


def verify_no_em_dash(text: str) -> None:
    """Strictly assert no Unicode em dash (U+2014) is present."""
    count = text.count("\u2014")
    if count > 0:
        raise ValueError(
            f"Constraint violation: Found {count} Unicode em dash (U+2014) characters in document. "
            "Rule prohibits em dash; use ASCII hyphen (-) instead."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy Legal 'Termeni si Conditii' page to Shopify via Admin GraphQL API."
    )
    parser.add_argument(
        "--html-path",
        type=str,
        default="anticariat_termeni_si_conditii.html",
        help="Path to the legal HTML source file.",
    )
    parser.add_argument(
        "--handle",
        type=str,
        default="termeni-si-conditii",
        help="Shopify page handle (slug). Default: termeni-si-conditii",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Termeni și condiții",
        help="Shopify page title. Default: Termeni și condiții",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Upload raw file contents without extracting style and article tags.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate HTML and verify Shopify connectivity without mutating data.",
    )

    args = parser.parse_args()

    # Find HTML file
    candidate_paths = [
        Path(args.html_path),
        Path(__file__).parent / args.html_path,
        Path("/home/marius/Projects/anticariat/bau") / args.html_path,
        Path("/home/marius/Projects/anticariat/bau/legal") / args.html_path,
    ]
    html_file = None
    for p in candidate_paths:
        if p.exists() and p.is_file():
            html_file = p
            break

    if not html_file:
        print(f"[ERROR] Could not find HTML file at '{args.html_path}' or fallback locations.", file=sys.stderr)
        sys.exit(1)

    print(f"[INPUT] Reading legal terms from: {html_file}")
    with open(html_file, "r", encoding="utf-8") as f:
        raw_html = f.read()

    # Strict compliance check
    verify_no_em_dash(raw_html)
    print("[COMPLIANCE] Zero Unicode em dash (U+2014) characters verified.")

    # Extract clean body HTML
    body_html = extract_body_content(raw_html, raw_mode=args.raw)
    print(f"[PARSER] Prepared payload body ({len(body_html)} characters / {len(body_html.encode('utf-8'))} bytes).")

    # Connect to Shopify
    api_version = os.environ.get("SHOPIFY_API_VERSION", "2025-01")
    shop_domain, token = get_shopify_credentials()
    print(f"[CONNECT] Connected to store: {shop_domain} (API: {api_version})")

    # Inspect current app access scopes
    scopes = check_app_access_scopes(shop_domain, token, api_version)
    has_read_content = "read_content" in scopes
    has_write_content = "write_content" in scopes

    print(f"[SCOPES] Current granted scopes ({len(scopes)}): {', '.join(sorted(scopes)) if scopes else 'None'}")
    if not (has_read_content and has_write_content):
        print(
            f"[NOTICE] App is currently missing 'read_content' (status: {has_read_content}) "
            f"and/or 'write_content' (status: {has_write_content})."
        )
        if args.dry_run:
            print("[DRY-RUN] Scope check complete. Payload parsed and validated.")
            print_scope_guidance()
            print("[SUCCESS] Dry-run completed successfully.")
            return
        else:
            print_scope_guidance()
            sys.exit(1)

    # Deploy
    result = create_or_update_page(
        shop_domain=shop_domain,
        token=token,
        title=args.title,
        handle=args.handle,
        body_html=body_html,
        api_version=api_version,
        dry_run=args.dry_run,
    )

    page_id = result.get("id")
    handle = result.get("handle") or args.handle
    public_url = f"https://{shop_domain}/pages/{handle}"

    print("=" * 64)
    print("[SUCCESS] Legal page published to Shopify!")
    print(f"Page ID:    {page_id}")
    print(f"Handle:     {handle}")
    print(f"Public URL: {public_url}")
    print("=" * 64)


if __name__ == "__main__":
    main()
