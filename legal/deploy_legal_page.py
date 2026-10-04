#!/usr/bin/env python3
"""
Deploy Legal Pages and Native Policies to Shopify via Admin GraphQL API.

Deterministically creates or updates both:
1. Online Store Pages (/pages/*):
   - Termeni si Conditii: /pages/termeni-si-conditii (Page ID: gid://shopify/Page/762875904391)
   - Politica de Confidentialitate: /pages/politica-de-confidentialitate
2. Native Shop Policies (/policies/*):
   - TERMS_OF_SERVICE: /policies/terms-of-service
   - PRIVACY_POLICY: /policies/privacy-policy

Zero credential files on disk: strictly consumes environment variables
injected via Doppler or runtime environment.

Mandatory rules:
- No Unicode em dash (U+2014) in text, comments, or documentation.
- Idempotent: checks for existing handle/policy and updates deterministically.
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
    Extract relevant styled content for Shopify page and policy bodies.
    Strips raw <style>, <head>, <script>, <title>, <meta>, <html>, and <body> tags
    to prevent raw CSS leaks in Shopify's policy parser, ensuring pure semantic HTML
    with universal inline styles.
    """
    if raw_mode:
        return html_content

    cleaned = html_content

    # Remove <!DOCTYPE ...>
    cleaned = re.sub(r"<!DOCTYPE[^>]*>", "", cleaned, flags=re.IGNORECASE)

    # Remove <head>...</head> including its inner tags (<title>, <meta>, <style>)
    cleaned = re.sub(r"<head[\s\S]*?</head>", "", cleaned, flags=re.IGNORECASE)

    # Remove any dangling <style>...</style> blocks
    cleaned = re.sub(r"<style[\s\S]*?</style>", "", cleaned, flags=re.IGNORECASE)

    # Remove any dangling <script>...</script> blocks
    cleaned = re.sub(r"<script[\s\S]*?</script>", "", cleaned, flags=re.IGNORECASE)

    # Remove any dangling <title>...</title> tags
    cleaned = re.sub(r"<title[\s\S]*?</title>", "", cleaned, flags=re.IGNORECASE)

    # Remove any dangling <meta> tags
    cleaned = re.sub(r"<meta[^>]*>", "", cleaned, flags=re.IGNORECASE)

    # Extract <article>...</article> if present
    article_match = re.search(r"(<article[\s\S]*?</article>)", cleaned, re.IGNORECASE)
    if article_match:
        return article_match.group(1).strip()

    # Extract <body>...</body> if present
    body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", cleaned, re.IGNORECASE)
    if body_match:
        cleaned = body_match.group(1).strip()

    # Remove closing </html> or </body> if still present
    cleaned = re.sub(r"</?(?:html|body)[^>]*>", "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


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
    page_id: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Create or update a legal page in Shopify via GraphQL mutations."""
    existing_page = None
    if page_id:
        existing_page = {"id": page_id, "handle": handle}
    else:
        existing_page = find_existing_page(shop_domain, token, handle, api_version)

    if existing_page:
        target_id = existing_page["id"]
        print(f"[FOUND] Existing page found ({handle}): {target_id}")
        if dry_run:
            print(f"[DRY-RUN] Would update page {target_id} with title '{title}' ({len(body_html)} characters).")
            return {"dry_run": True, "action": "update", "id": target_id, "handle": handle}

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
            "id": target_id,
            "page": {
                "title": title,
                "body": body_html,
                "isPublished": True,
            },
        }
        res = execute_graphql(shop_domain, token, mutation, variables, api_version)
        if "errors" in res and res["errors"]:
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
            raise RuntimeError(f"GraphQL error during pageCreate: {res['errors']}")

        create_data = res.get("data", {}).get("pageCreate", {})
        user_errors = create_data.get("userErrors", [])
        if user_errors:
            raise RuntimeError(f"Shopify pageCreate user errors: {user_errors}")
        return create_data.get("page", {})


def disable_privacy_features(
    shop_domain: str,
    token: str,
    features: List[str],
    api_version: str,
) -> List[str]:
    """Disable automatic management for customer privacy features (e.g. PRIVACY_POLICY)."""
    mutation = """
    mutation DisablePrivacyFeatures($featuresToDisable: [PrivacyFeaturesEnum!]!) {
      privacyFeaturesDisable(featuresToDisable: $featuresToDisable) {
        featuresDisabled
        userErrors {
          field
          message
        }
      }
    }
    """
    res = execute_graphql(shop_domain, token, mutation, {"featuresToDisable": features}, api_version)
    data = res.get("data", {}).get("privacyFeaturesDisable", {})
    return data.get("featuresDisabled", [])


def update_shop_policy(
    shop_domain: str,
    token: str,
    policy_type: str,
    body_html: str,
    api_version: str,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Update native Shopify Shop Policy (e.g. TERMS_OF_SERVICE, PRIVACY_POLICY) via GraphQL mutation.
    Automatically handles disabling auto-managed privacy features when updating PRIVACY_POLICY.
    """
    print(f"[POLICY] Target native policy type: {policy_type}")
    if dry_run:
        print(f"[DRY-RUN] Would update shopPolicy '{policy_type}' ({len(body_html)} characters).")
        return {"dry_run": True, "action": "shopPolicyUpdate", "type": policy_type}

    mutation = """
    mutation UpdateShopPolicy($shopPolicy: ShopPolicyInput!) {
      shopPolicyUpdate(shopPolicy: $shopPolicy) {
        shopPolicy {
          id
          title
          url
          body
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    variables = {
        "shopPolicy": {
            "type": policy_type,
            "body": body_html,
        }
    }
    res = execute_graphql(shop_domain, token, mutation, variables, api_version)
    if "errors" in res and res["errors"]:
        raise RuntimeError(f"GraphQL error during shopPolicyUpdate: {res['errors']}")

    data = res.get("data", {}).get("shopPolicyUpdate", {})
    user_errors = data.get("userErrors", [])
    if user_errors:
        # Check if error is due to automatic management of Privacy Policy
        is_auto_managed = any(
            "Automatic management for Privacy Policy must be turned off" in err.get("message", "")
            for err in user_errors
        )
        if is_auto_managed:
            print("[POLICY] Automatic management for Privacy Policy detected. Disabling automatic management...")
            disabled = disable_privacy_features(shop_domain, token, ["PRIVACY_POLICY"], api_version)
            print(f"[POLICY] Disabled automatic management: {disabled}. Retrying shopPolicyUpdate...")
            res = execute_graphql(shop_domain, token, mutation, variables, api_version)
            data = res.get("data", {}).get("shopPolicyUpdate", {})
            user_errors = data.get("userErrors", [])

        if user_errors:
            raise RuntimeError(f"Shopify shopPolicyUpdate user errors: {user_errors}")

    return data.get("shopPolicy", {})


def verify_no_em_dash(text: str) -> None:
    """Strictly assert no Unicode em dash (U+2014) is present."""
    count = text.count("\u2014")
    if count > 0:
        raise ValueError(
            f"Constraint violation: Found {count} Unicode em dash (U+2014) characters in document. "
            "Rule prohibits em dash; use ASCII hyphen (-) instead."
        )


DOC_PRESETS = {
    "terms": {
        "html_file": "anticariat_termeni_si_conditii.html",
        "handle": "termeni-si-conditii",
        "title": "Termeni și condiții",
        "policy_type": "TERMS_OF_SERVICE",
        "page_id": "gid://shopify/Page/762875904391",
        "label": "Termeni și Condiții",
    },
    "privacy": {
        "html_file": "anticariat_politica_de_confidentialitate.html",
        "handle": "politica-de-confidentialitate",
        "title": "Politica de confidențialitate",
        "policy_type": "PRIVACY_POLICY",
        "page_id": None,
        "label": "Politica de Confidențialitate (GDPR)",
    },
}

POLICY_SLUGS = {
    "TERMS_OF_SERVICE": "terms-of-service",
    "PRIVACY_POLICY": "privacy-policy",
    "REFUND_POLICY": "refund-policy",
    "SHIPPING_POLICY": "shipping-policy",
    "LEGAL_NOTICE": "legal-notice",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy Legal pages and native policies to Shopify via Admin GraphQL API."
    )
    parser.add_argument(
        "--type",
        "--doc-type",
        dest="doc_type",
        choices=["terms", "privacy"],
        default=None,
        help="Legal document type preset: 'terms' (Termeni si Conditii) or 'privacy' (Politica de Confidentialitate). Auto-detected if omitted.",
    )
    parser.add_argument(
        "--html-path",
        "--file",
        dest="html_path",
        type=str,
        default=None,
        help="Path to the legal HTML source file.",
    )
    parser.add_argument(
        "--target",
        type=str,
        choices=["all", "page", "policy"],
        default="all",
        help="Deployment target: 'all' (page + policy), 'page' (only /pages/*), 'policy' (only /policies/*). Default: all",
    )
    parser.add_argument(
        "--handle",
        type=str,
        default=None,
        help="Shopify page handle (slug).",
    )
    parser.add_argument(
        "--page-id",
        type=str,
        default=None,
        help="Optional explicit Shopify Page ID.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Shopify page title.",
    )
    parser.add_argument(
        "--policy-type",
        type=str,
        default=None,
        help="Shopify ShopPolicyType (e.g. TERMS_OF_SERVICE, PRIVACY_POLICY).",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Upload raw file contents without sanitizing head/style blocks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate HTML and verify Shopify connectivity without mutating data.",
    )

    args = parser.parse_args()

    # Determine document type preset if not explicit
    preset_key = args.doc_type
    if not preset_key:
        file_hint = (args.html_path or "").lower()
        policy_hint = (args.policy_type or "").upper()
        handle_hint = (args.handle or "").lower()

        if (
            "confidentialitate" in file_hint
            or "privacy" in file_hint
            or policy_hint == "PRIVACY_POLICY"
            or "confidentialitate" in handle_hint
        ):
            preset_key = "privacy"
        elif (
            "termeni" in file_hint
            or "terms" in file_hint
            or policy_hint == "TERMS_OF_SERVICE"
            or "termeni" in handle_hint
        ):
            preset_key = "terms"
        else:
            preset_key = "terms"

    preset = DOC_PRESETS[preset_key]
    html_target = args.html_path or preset["html_file"]
    handle = args.handle or preset["handle"]
    title = args.title or preset["title"]
    policy_type = args.policy_type or preset["policy_type"]
    page_id = args.page_id or preset["page_id"]
    doc_label = preset["label"]

    # Find HTML file
    candidate_paths = [
        Path(html_target),
        Path(__file__).parent / html_target,
        Path("/home/marius/Projects/anticariat/bau") / html_target,
        Path("/home/marius/Projects/anticariat/bau/legal") / html_target,
    ]
    html_file = None
    for p in candidate_paths:
        if p.exists() and p.is_file():
            html_file = p
            break

    if not html_file:
        print(f"[ERROR] Could not find HTML file at '{html_target}' or fallback locations.", file=sys.stderr)
        sys.exit(1)

    print(f"[INPUT] Document preset: {preset_key.upper()} ({doc_label})")
    print(f"[INPUT] Reading source from: {html_file}")
    with open(html_file, "r", encoding="utf-8") as f:
        raw_html = f.read()

    # Strict compliance check
    verify_no_em_dash(raw_html)
    print("[COMPLIANCE] Zero Unicode em dash (U+2014) characters verified in source HTML.")

    # Extract clean body HTML without head/style/title blocks
    body_html = extract_body_content(raw_html, raw_mode=args.raw)
    verify_no_em_dash(body_html)
    print(f"[PARSER] Prepared payload body ({len(body_html)} characters / {len(body_html.encode('utf-8'))} bytes).")

    # Connect to Shopify
    api_version = os.environ.get("SHOPIFY_API_VERSION", "2025-01")
    shop_domain, token = get_shopify_credentials()
    public_domain = os.environ.get("PUBLIC_STORE_DOMAIN", "dev.anticariatalbert.com")
    print(f"[CONNECT] Connected to shop: {shop_domain} (API: {api_version})")

    # Deploy based on target
    if args.target in ("all", "page"):
        print(f"[DEPLOY] Updating Online Store Page '{handle}' (Title: '{title}')...")
        page_res = create_or_update_page(
            shop_domain=shop_domain,
            token=token,
            title=title,
            handle=handle,
            body_html=body_html,
            api_version=api_version,
            page_id=page_id,
            dry_run=args.dry_run,
        )
        final_page_id = page_res.get("id") or page_id
        page_admin_url = f"https://{shop_domain}/pages/{handle}"
        print(f"[SUCCESS] Page endpoint synced -> ID: {final_page_id} | Store URL: {page_admin_url}")
        if public_domain and public_domain != shop_domain:
            print(f"          Public storefront URL: https://{public_domain}/pages/{handle}")

    if args.target in ("all", "policy"):
        policy_slug = POLICY_SLUGS.get(policy_type, policy_type.lower().replace("_", "-"))
        print(f"[DEPLOY] Updating Shop Policy '{policy_type}' (Slug: '{policy_slug}')...")
        policy_res = update_shop_policy(
            shop_domain=shop_domain,
            token=token,
            policy_type=policy_type,
            body_html=body_html,
            api_version=api_version,
            dry_run=args.dry_run,
        )
        policy_admin_url = f"https://{shop_domain}/policies/{policy_slug}"
        print(f"[SUCCESS] Policy endpoint synced -> Type: {policy_type} | Store URL: {policy_admin_url}")
        if public_domain and public_domain != shop_domain:
            print(f"          Public storefront URL: https://{public_domain}/policies/{policy_slug}")

    print("=" * 70)
    print(f"[COMPLETED] {doc_label} synchronization successfully finished.")
    print("=" * 70)


if __name__ == "__main__":
    main()

