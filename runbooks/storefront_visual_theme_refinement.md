# Runbook: Storefront Visual Theme Refinement

## Context
The default Shopify Horizon 4.2.0 theme defaults to a stark, clinical white palette (`#FFFFFF` background, `#000000` text) with a single sans-serif font across both body and headings. For an antiquarian bookshop specializing in rare books, vintage editions, and bibliophile collections, this clinical aesthetic strains the eyes during prolonged evening browsing and lacks authentic editorial heritage.

This runbook documents the automated procedure to transition the storefront to the **Antiquarian Bibliophile Heritage** visual system.

## Design Token Contract
The visual system is governed by a centralized color token contract in `config/settings_data.json`:
- `background`: `#F8F5EE` (Warm cotton book paper canvas)
- `foreground`: `#201C18` (Deep espresso ink)
- `color1`: `#61574E` (Muted walnut for bibliographic metadata)
- `color2`: `#E4DCD0` (Warm linen for dividers, input borders, and card outlines)
- `nested_card`: `#FAF7F1` (Subtle archival paper card background)
- `badge_sold_out`: `#ECE5D8` (Warm grey-beige sold out indicator)

## Typography Contract
- **Headings & Book Titles**: `Libre Baskerville Bold` (`libre_baskerville_n7`)
  - Semantic weights: H1 (56px, display-tight), H2 (48px, display-tight), H3 (32px, display-normal), H4 (24px, display-tight).
- **Body & Bibliographic Details**: `Inter Normal` (`inter_n4`)
  - Line height: 1.6 (`body-loose`) for reading comfort on physical condition reports and excerpt passages.
- **Subheading**: `Inter Medium` (`inter_n5`).

## Automated Execution
The theme refinement is fully automated and idempotent via `themes/apply_visual_refinement.py`:

```bash
# Verify credentials and preview changes
doppler run --project anticariat-bau --config prd -- python3 themes/apply_visual_refinement.py --dry-run

# Apply visual refinement to active Shopify theme
doppler run --project anticariat-bau --config prd -- python3 themes/apply_visual_refinement.py
```

## Rollback Protocol
If you wish to revert to the default Horizon 4.2.0 clinical white appearance:
```bash
# Preview rollback changes safely
doppler run --project anticariat-bau --config prd -- python3 themes/apply_visual_refinement.py --dry-run --rollback

# Execute live rollback
doppler run --project anticariat-bau --config prd -- python3 themes/apply_visual_refinement.py --rollback
```
The rollback procedure is 100% deterministic:
- Restores `config/settings_data.json` to `#ffffff` background, `#000000` text, and `inter_n7` headings.
- Strips the marked custom CSS block from `assets/base.css`.
- Reverts template titles in `templates/*.json` to `var(--font-body--family)`.
- Leaves custom Liquid blocks (`product-author-block.liquid`, `product-specifications-block.liquid`) completely untouched and operational.

## Affected Theme Assets
1. `config/settings_data.json`: Centralized color palette, button radiuses, typography bindings.
2. `assets/base.css`: Appended with marked block `/* anticariat-theme: antiquarian bibliophile heritage styling */`.
3. Template JSON files (`templates/index.json`, `templates/collection.json`, `templates/product.json`, etc.): Headings and product titles mapped to `var(--font-heading--family)`.

## Verification Protocol
1. **API Asset Check**: Ensure GraphQL `themeFilesUpsert` mutation succeeds with zero userErrors.
2. **Contrast Analysis**:
   - Primary Text on Paper (`#201C18` on `#F8F5EE`): 15.55:1 (passes WCAG AAA >= 7.0:1).
   - Primary Button Text (`#F8F5EE` on `#201C18`): 15.55:1 (passes WCAG AAA >= 7.0:1).
   - Sold Out Badge (`#201C18` on `#ECE5D8`): 13.51:1 (passes WCAG AAA >= 7.0:1).
   - Secondary Metadata (`#61574E` on `#F8F5EE`): 6.47:1 (passes WCAG AA; passes WCAG AAA for large/bold text).
3. **Storefront HTTPS Verification**:
   - Unlock password gate using Doppler secret `SHOPIFY_STOREFRONT_PASSWORD`.
   - Verify `--color-background: #F8F5EE` and `Libre Baskerville` presence in DOM.
   - Confirm author block and book specification tables display without visual regressions.
