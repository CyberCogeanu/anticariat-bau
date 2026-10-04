# SOP: Connecting Custom Subdomains to Shopify via Cloudflare DNS

## Purpose
This Standard Operating Procedure defines the deterministic process for configuring, routing, and binding custom subdomains (e.g. `dev.anticariatalbert.com`) to Anticariat Albert's Shopify storefront (`0egygb-uv.myshopify.com`).

---

## Architecture & Security Requirements

1. **Zero Credentials on Disk**:
   All Cloudflare tokens and Shopify credentials must be injected dynamically via Doppler:
   `doppler run --project anticariat-bau --config prd -- ...`
2. **Cloudflare Proxying Policy**:
   New subdomains pointing to Shopify must initially be set to `proxied: false` (DNS-only / Grey Cloud) in Cloudflare. This ensures Shopify's SSL handshake and automated certificate provisioning (Let's Encrypt / Google Trust Services) can complete without proxy interference.
3. **No Unicode Em Dash**:
   Always use standard ASCII hyphens (-), colons, or parentheses.

---

## Execution Workflow

### Step 1: Automated Cloudflare DNS Provisioning
Run the automated DNS management script:

```bash
doppler run --project anticariat-bau --config prd -- \
  python3 integrations/manage_subdomain_dns.py --subdomain dev
```

Parameters:
- `--subdomain`: The subdomain prefix (default: `dev`).
- `--target`: The Shopify edge destination (default: `shops.myshopify.com`).
- `--proxied`: Flag to enable Cloudflare proxying (default: disabled, DNS-only).
- `--ttl`: Time to live (default: `1`, automatic).

The script will:
- Check for existing DNS records for `dev.anticariatalbert.com`.
- Create or update the record idempotently to `CNAME -> shops.myshopify.com`.
- Verify DNS propagation via Cloudflare DNS-over-HTTPS (DoH) and system resolvers.

---

### Step 2: Shopify Admin Domain Connection (Merchant Action)
Because Shopify requires merchant confirmation to bind custom domains to a shop:

1. Open Shopify Admin: `https://admin.shopify.com/store/0egygb-uv/settings/domains`
   (Or navigate to **Settings** -> **Domains**).
2. Click the **Connect existing domain** button in the top right.
3. In the domain input field, type:
   `dev.anticariatalbert.com`
4. Click **Next**, then click **Verify connection**.
5. Shopify will test the CNAME record against `shops.myshopify.com` and accept the domain binding.
6. (Optional) Once verified, if this subdomain is intended to be the default customer-facing address, click **Change primary domain** and select `dev.anticariatalbert.com`.

---

### Step 3: Domain Status & SSL Verification
Monitor the domain attachment and SSL certificate activation using the verification tool:

```bash
# Single status check
doppler run --project anticariat-bau --config prd -- \
  python3 integrations/verify_shopify_domain.py --domain dev.anticariatalbert.com

# Or continuous polling until active
doppler run --project anticariat-bau --config prd -- \
  python3 integrations/verify_shopify_domain.py --domain dev.anticariatalbert.com --watch
```

And test live HTTPS edge response:

```bash
curl -I https://dev.anticariatalbert.com/
```
