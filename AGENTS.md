# AGENTS.md - BAU Agent Contract

## Non-Negotiable Controls

1. **Human Authority on Consequential Actions**:
   - No advertising money may be spent and no broadcast marketing emails may be dispatched without explicit human approval from Marius or his mother.
2. **No Unicode Em Dash (U+2014)**:
   - Use standard ASCII hyphens (-), commas, colons, or parentheses.
3. **Customer PII Security**:
   - Customer personal data must be processed in compliance with GDPR.
   - No customer phone numbers or physical addresses may be committed to Git or passed to unvetted cloud models.
4. **Secrets Management (Zero Credential Files on Disk & Proactive Doppler Placeholders)**:
   - Never create or store credentials in `.env`, `.env.*`, or any filesystem files on disk.
   - All production Shopify tokens, courier credentials, Cloudflare tokens, and email API keys must be retrieved strictly from Doppler (configs: `homelab-lab/prd` or dedicated `anticariat-bau`).
   - Proactive Doppler Placeholders: Whenever new credentials or tokens are needed, the agent must provision empty placeholder keys in Doppler (`doppler secrets set KEY="" --project ... --config ...`) and only ask the human operator to populate the values.
