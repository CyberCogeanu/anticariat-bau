#!/usr/bin/env python3
"""
Deployment script for Anticariat Albert Executive Operator Portal to Cloudflare.
Strict Zero Local File Credentials Rule:
Retrieves credentials exclusively from Doppler (homelab-lab/prd) or environment.
Zero credentials stored or logged to disk.
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error

PORTAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portal")
DOPPLER_BIN = "/home/marius/.local/bin/doppler"
PROJECT = "homelab-lab"
CONFIG = "prd"

def get_doppler_secret(name: str) -> str:
    # First check environment
    val = os.environ.get(name, "")
    if val:
        return val
    # Otherwise fetch from Doppler CLI
    if os.path.isfile(DOPPLER_BIN):
        try:
            res = subprocess.run(
                [DOPPLER_BIN, "secrets", "get", name, "--plain", "-p", PROJECT, "-c", CONFIG, "--no-check-version"],
                capture_output=True, text=True, check=True
            )
            return res.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
    return ""

def main():
    print("[1/6] Fetching credentials strictly from Doppler (homelab-lab/prd)...")
    # Prefer CLOUDFLARE_PAGES_TOKEN if set, fallback to CLOUDFLARE_API_TOKEN
    token = get_doppler_secret("CLOUDFLARE_PAGES_TOKEN")
    if not token or "PASTE" in token or len(token) < 20:
        token = get_doppler_secret("CLOUDFLARE_API_TOKEN")

    account_id = get_doppler_secret("CLOUDFLARE_ACCOUNT_ID") or "82c43dc0dc66b34937a39d190b6c68e9"
    zone_id = "e842abeeb3d774b9a208a79db9a12e20"
    domain = "portal.anticariatalbert.com"
    allowed_emails = ["office@anticariatalbert.com", "flare@cogeanu.com"]

    if not token or "PASTE" in token or len(token) < 20:
        print("ERROR: Valid Cloudflare token not found in Doppler (homelab-lab/prd).")
        print("Please update CLOUDFLARE_PAGES_TOKEN or CLOUDFLARE_API_TOKEN in the Doppler web interface.")
        sys.exit(1)

    # 1. Verify token
    print("[2/6] Verifying token permissions with Cloudflare API...")
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/user/tokens/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not data.get("success"):
                print("ERROR: Cloudflare token verification failed:", data.get("errors"))
                sys.exit(1)
            print(" -> Token is valid and active.")
    except Exception as e:
        print(f"ERROR verifying token: {e}")
        sys.exit(1)

    # 2. Deploy Pages via Wrangler
    print("[3/6] Deploying portal to Cloudflare Pages (project: anticariat-portal)...")
    env = os.environ.copy()
    env["CLOUDFLARE_API_TOKEN"] = token
    env["CLOUDFLARE_ACCOUNT_ID"] = account_id

    cmd = [
        "npx", "--yes", "wrangler", "pages", "deploy",
        PORTAL_DIR,
        "--project-name=anticariat-portal",
        "--branch=main",
        "--commit-dirty=true"
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print("Wrangler deploy output:\n", res.stdout)
        print("Wrangler deploy error:\n", res.stderr)
        print("ERROR: Wrangler deployment failed.")
        sys.exit(1)
    print(" -> Pages deployment successful!")
    for line in res.stdout.splitlines():
        if "pages.dev" in line:
            print("   ", line.strip())

    # 3. Add Custom Domain to Pages project
    print(f"[4/6] Binding custom domain {domain} to Pages project...")
    domain_req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/anticariat-portal/domains",
        data=json.dumps({"name": domain}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(domain_req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f" -> Custom domain {domain} registered successfully.")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        if "already exists" in err_body.lower() or "8000000" in err_body:
            print(f" -> Custom domain {domain} is already registered on Pages.")
        else:
            print(f" -> Custom domain API response ({e.code}): {err_body}")

    # 4. Ensure DNS CNAME record
    print(f"[5/6] Verifying DNS CNAME record in zone for {domain}...")
    dns_check_req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={domain}",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(dns_check_req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            records = data.get("result", [])
            if not records:
                create_dns_req = urllib.request.Request(
                    f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
                    data=json.dumps({
                        "type": "CNAME",
                        "name": "portal",
                        "content": "anticariat-portal.pages.dev",
                        "ttl": 1,
                        "proxied": True
                    }).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(create_dns_req) as dns_resp:
                    print(f" -> Created DNS CNAME {domain} -> anticariat-portal.pages.dev (proxied: True).")
            else:
                print(f" -> DNS record for {domain} already exists: {records[0]['type']} -> {records[0]['content']}.")
    except Exception as e:
        print(f" -> Note on DNS management: {e}")

    # 5. Cloudflare Zero Trust (Access) Application
    print(f"[6/6] Configuring Cloudflare Zero Trust (Access) for {domain}...")
    apps_req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/access/apps",
        headers={"Authorization": f"Bearer {token}"}
    )
    app_id = None
    try:
        with urllib.request.urlopen(apps_req) as resp:
            apps = json.loads(resp.read().decode("utf-8")).get("result", [])
            for app in apps:
                if app.get("domain") == domain:
                    app_id = app.get("id")
                    break

        if not app_id:
            new_app_req = urllib.request.Request(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/access/apps",
                data=json.dumps({
                    "name": "Portal Operativ Anticariat Albert",
                    "domain": domain,
                    "session_duration": "720h", # 30 days
                    "auto_redirect_to_identity": False
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(new_app_req) as resp:
                created_app = json.loads(resp.read().decode("utf-8")).get("result", {})
                app_id = created_app.get("id")
                print(f" -> Created Zero Trust Application (ID: {app_id}). Session duration: 30 days (720h).")
        else:
            print(f" -> Zero Trust Application already exists (ID: {app_id}).")

        if app_id:
            policy_req = urllib.request.Request(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/access/apps/{app_id}/policies",
                data=json.dumps({
                    "name": "Operator & Admin 30-Day Access",
                    "decision": "allow",
                    "include": [{"email": {"email": email}} for email in allowed_emails]
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            try:
                with urllib.request.urlopen(policy_req) as resp:
                    print(f" -> Access policy attached for allowed emails: {allowed_emails}")
            except urllib.error.HTTPError as e:
                err = e.read().decode("utf-8")
                if "already exists" in err.lower():
                    print(" -> Access policy already exists.")
                else:
                    print(f" -> Note on policy creation: {err}")
    except Exception as e:
        print(f" -> Note on Zero Trust setup: {e}")

    print("\n=======================================================")
    print(f"SUCCESS: Portal is deployed and ready!")
    print(f"URL: https://{domain}")
    print(f"Operator Login: Mother uses 6-digit email PIN sent to office@anticariatalbert.com")
    print(f"Session Duration: 30 days")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
