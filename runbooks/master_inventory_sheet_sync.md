# Runbook: Master Inventory Spreadsheet Synchronization & Intake (BAU)

## 1. Overview & Objective
This operational runbook defines the recurring maintenance procedure for synchronizing the shop owner's (Marius's mother) Master Inventory Spreadsheet with the canonical catalog and the live Shopify storefront.

### Primary Goals:
- Keep shelf picking locations (`location_id`) 100% updated for warehouse fulfillment.
- Ingest newly cataloged books into the canonical system.
- Update shipping weights and physical dimensions for courier calculation.
- Backfill collector metadata (translators, foreword authors, edition curators, series).

### Recommended Frequency:
- **Weekly:** Every Sunday evening or Monday morning before weekly shipping dispatches.
- **On-Demand:** Immediately following a major physical shelf reorganization or cataloging batch.

---

## 2. Pre-Requisites & Environment

All commands must be executed within the `anticariat-migration` workspace using the Python virtual environment and Doppler for zero-secret credentials:

```bash
cd /home/marius/Projects/anticariat/migration
source .venv/bin/activate
```

Verify Doppler authentication:
```bash
doppler --no-check-version run --project anticariat-migration --config prd -- echo "Doppler OK"
```

---

## 3. Step-by-Step Execution Workflow

### Step 1: Ingest & Cache Master Spreadsheet
Fetch the latest CSV export from Google Sheets, calculate SHA-256 fingerprint, clean headers, and populate SQLite:

```bash
python3 extractors/ingest_mom_sheet.py --download
```

**Expected Output:**
- Downloads fresh CSV to `data/sources/mom_sheet_master.csv`.
- Generates SHA-256 fingerprint in `data/sources/mom_sheet_master.meta.json`.
- Indexes 37,000+ records into `data/sources/mom_sheet.sqlite`.
- Outputs ingestion metrics and top shelf locations.

---

### Step 2: Review Reconciliation Report
Inspect the newly generated reconciliation report to identify any anomalies, typos in codes, or stock divergences:

```bash
cat data/sources/mom_sheet_reconciliation_report.md
```

**Checklist:**
- [ ] Match rate against catalog remains >= 99.9%.
- [ ] Review any unmatched codes listed under "Unmatched Catalog Books". If a code was mistyped on physical sticker, correct it directly in the spreadsheet or catalog.

---

### Step 3: Run Canonical Catalog Enrichment
Enrich local canonical JSON files and update `data/catalog/inventory.db`:

```bash
# 1. Run dry-run to verify zero schema validation errors
python3 enrichment/enrich_from_mom_sheet.py --dry-run

# 2. Run live enrichment
python3 enrichment/enrich_from_mom_sheet.py
```

**What this updates:**
- `data/catalog/{shard}/{id_legacy:05d}.json`: sets `location_id`, `dimensions_cm`, `weight_grams`, `collection_series`, `contributors`, `condition_notes`, and audit provenance.
- `data/catalog/inventory.db`: updates `location_id`, `dimensions_cm`, `weight_grams`, and `enriched_status`.

---

### Step 4: Synchronize Metafields to Live Shopify Storefront
Push enriched specifications to live products mapped on Shopify and ensure theme templates are up to date:

```bash
doppler --no-check-version run --project anticariat-migration --config prd -- \
  python3 loaders/sync_product_metafields.py
```

**What this does:**
1. Validates that custom product metafield definitions exist in Shopify Admin.
2. Updates `custom.shelf_location`, `custom.dimensions`, `custom.translator`, `custom.editor_curator`, `custom.preface_author`, `custom.collection_series` across all live mapped products.
3. Deploys updated `blocks/product-specifications-block.liquid` to the active theme (`Horizon`).
4. Performs read-after-write verification on sample products.

---

### Step 5: Storefront Spot-Check Verification
Open sample product pages on the live development storefront to confirm proper visual rendering:
- `https://dev.anticariatalbert.com/products/avatarii-faraonului-tla-27`
- `https://dev.anticariatalbert.com/products/mite-balauca-28`
- `https://dev.anticariatalbert.com/products/m-eminescu-71`

**Verification Criteria:**
- Under "Specificatii bibliografice", verify the following labels appear when populated:
  - "Editura"
  - "Colecție / Serie"
  - "An apariție"
  - "Traducător"
  - "Ediție îngrijită de"
  - "Prefață / Cuvânt înainte"
  - "Format copertă"
  - "Dimensiuni" (e.g. `20 x 13 x 2 cm`)
  - "Număr pagini"
  - "Stare exemplar"
  - "Categorii"

---

## 4. Troubleshooting & Exception Handling

### Issue 1: "Cod not found in mom sheet"
- **Cause:** A book reference was truncated or mistyped in the legacy PrestaShop database (e.g. `13646` instead of `136468`).
- **Remedy:** Search Mom's sheet by title:
  ```bash
  python3 -c "import sqlite3; conn=sqlite3.connect('data/sources/mom_sheet.sqlite'); print(conn.execute(\"SELECT cod_reference, title FROM mom_sheet_books WHERE title LIKE '%titlu%' LIMIT 5\").fetchall())"
  ```
  Update the canonical JSON `cod_reference` with the confirmed code.

### Issue 2: Duplicate Cod in Spreadsheet
- **Cause:** Mom cataloged two volumes under the same code, or updated a record with a new date.
- **Resolution:** The loader deterministically prioritizes entries with active stock (`stock_quantity > 0`), valid location, and higher row index. No manual action required unless the volumes need distinct sticker barcodes.

### Issue 3: Missing Shopify API Permissions
- **Error:** `GraphQL Errors: Access denied for metafieldDefinitionCreate`
- **Remedy:** Ensure the Shopify App has `write_products`, `read_products`, and `write_themes` scopes enabled in the partner dashboard.
