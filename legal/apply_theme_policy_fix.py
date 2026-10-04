#!/usr/bin/env python3
"""
Idempotently append theme_policy_title_fix.css to assets/base.css of the MAIN Shopify theme.

Why: the Horizon /policies/* H1 overflows 390px viewports for long titles
("Politica de confidentialitate"). Policy bodies cannot style the theme title.

Usage (credentials only via Doppler):
  doppler run --project anticariat-bau --config prd -- python3 bau/legal/apply_theme_policy_fix.py [--dry-run]

Idempotent: if the marker block is already present it is replaced, never duplicated.
Re-run after any Horizon theme update that overwrites base.css.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from deploy_legal_page import execute_graphql, get_shopify_credentials  # noqa: E402

ASSET = "assets/base.css"
START = "/* anticariat-legal: policy title mobile fix"
END = "/* end anticariat-legal: policy title mobile fix */"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fix = (Path(__file__).parent / "theme_policy_title_fix.css").read_text(encoding="utf-8").strip()
    if "\u2014" in fix:
        sys.exit("[ERROR] Em dash found in CSS fix.")

    shop, token = get_shopify_credentials()
    res = execute_graphql(shop, token, "{ themes(first: 1, roles: [MAIN]) { nodes { id name } } }")
    theme = res["data"]["themes"]["nodes"][0]
    print(f"[THEME] {theme['name']} ({theme['id']})")

    q = """query($id: ID!, $f: [String!]) { theme(id: $id) { files(filenames: $f) { nodes {
      checksumMd5 body { ... on OnlineStoreThemeFileBodyText { content } } } } } }"""
    res = execute_graphql(shop, token, q, {"id": theme["id"], "f": [ASSET]})
    content = res["data"]["theme"]["files"]["nodes"][0]["body"]["content"]

    pattern = re.compile(re.escape(START) + r"[\s\S]*?" + re.escape(END))
    if pattern.search(content):
        new = pattern.sub(lambda _: fix, content)
        action = "replace"
    else:
        new = content.rstrip() + "\n\n" + fix + "\n"
        action = "append"

    if new == content:
        print("[SKIP] Fix already present and identical.")
        return
    if args.dry_run:
        print(f"[DRY-RUN] Would {action} fix block in {ASSET} ({len(content)} -> {len(new)} chars).")
        return

    m = """mutation($id: ID!, $files: [OnlineStoreThemeFilesUpsertFileInput!]!) {
      themeFilesUpsert(themeId: $id, files: $files) {
        upsertedThemeFiles { filename } userErrors { field message } } }"""
    res = execute_graphql(shop, token, m, {"id": theme["id"], "files": [
        {"filename": ASSET, "body": {"type": "TEXT", "value": new}}]})
    payload = (res.get("data") or {}).get("themeFilesUpsert") or {}
    if res.get("errors") or payload.get("userErrors"):
        sys.exit(f"[ERROR] {res.get('errors') or payload.get('userErrors')}")
    print(f"[SUCCESS] {action} -> {payload.get('upsertedThemeFiles')}")


if __name__ == "__main__":
    main()
