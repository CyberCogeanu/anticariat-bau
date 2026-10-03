# Executive Operator Interface (Portal Operativ)

Minimal, zero-friction, touch-friendly web application for Marius's mother at the physical shop (Strada Alexandru Lăpușneanu 11, Iași).

## Core Capabilities

1. **Comenzi & Livrare (Daily Packing & Courier Dispatch):**
   - Direct visibility of pending orders with book title, author, physical sticker reference code (`cod`), and shelf coordinate (`location_id`, e.g. `C1-R04-S2`).
   - Tactile picking checkboxes with 1-click AWB generation for Fan Courier / Sameday.
   - Printable AWB shipping label preview modal.

2. **Adăugare Rapidă (<30 Secunde) (Fast Book Ingestion):**
   - Sticky shelf locking: Mother sets the active bookcase coordinate (e.g. `C1-R04-S2`) once, and all subsequently scanned books automatically inherit that shelf coordinate.
   - Instant bibliographic autocomplete from Romanian catalog database (Title, Author, Publisher, Year, Binding, Page Count, Suggested Price).
   - Condition grade and physical defect selector chips.
   - Live photo upload / smartphone camera capture preview.
   - Instant printable barcode shelf sticker generator with unique product ID and reference code.
   - Live reward loop: Each ingested book immediately adds +5 points to the Anticariat Power Index.

3. **Puls Vânzări (Daily/Monthly Financial Pulse):**
   - Clean summary of daily and monthly revenue in RON.
   - Average Order Value (AOV) and active catalog metrics.

4. **Radar Competiție & Aprobări (Growth & Governance):**
   - **Anticariat Power Index**: Dynamic 0 to 1,000,000 point progress tracker comparing Anticariat Albert against 16 Romanian competitor domains (Printre Cărți, Târgul Cărții, Anticariat Ursu, etc.).
   - **Feature Approval Cards**: 1-click decision cards ([Vreau pe Shopify: DA] / [NU]) for high-converting features identified across competitor stores.

## Technical Architecture & Deployment

- **Stack:** Pure Vanilla HTML5 + Custom CSS Design System + Vanilla JS (ES Modules). Zero dependencies, zero build steps required.
- **Offline & Local State:** Fully resilient with localStorage persistence. Decisions, newly added books, and order states survive browser reloads.
- **Hosting Target (Phase 5):** Cloudflare Pages with Cloudflare Zero Trust (Access) via one-time 6-digit email PIN. Zero VPN, zero Tailscale client on operator devices.
- **Local Testing:**
  ```bash
  python3 -m http.server 8080 --directory portal/
  ```

