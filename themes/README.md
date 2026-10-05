# Themes - Storefront Styling & Asset Orchestration

This directory manages native visual refinements, CSS enhancements, and theme configurations for the Shopify Horizon theme.

## Architecture & Principles
1. **Native Horizon 4.2.0 Modification**: No theme replacements; styles and tokens are updated natively via the Shopify Admin GraphQL Theme API.
2. **Zero Credentials on Disk**: All API requests consume credentials injected strictly via Doppler (`anticariat-bau` / `prd`).
3. **Idempotency**: All scripts can be re-run safely at any time. If theme assets already match target state, zero redundant mutations are dispatched.
4. **No Unicode Em Dash**: Strictly enforce ASCII hyphens (-), commas, colons, or parentheses.

## Scripts
- `apply_visual_refinement.py`: Orchestrates the Antiquarian Bibliophile Heritage visual transition:
  - Updates `config/settings_data.json` color palette tokens and typography settings.
  - Aligns template JSON files to use `var(--font-heading--family)` for titles, with centered alignment and 12px inset padding on product cards.
  - Idempotently enhances `assets/base.css` with card corner clipping (`overflow: hidden`), center alignment, 12px inset padding, and button styling.
  - Performs live HTTPS validation through the password gate.
  - Runs WCAG AAA contrast ratio checks.

## Usage
```bash
# Dry run inspection
doppler run --project anticariat-bau --config prd -- python3 themes/apply_visual_refinement.py --dry-run

# Live deployment
doppler run --project anticariat-bau --config prd -- python3 themes/apply_visual_refinement.py
```
