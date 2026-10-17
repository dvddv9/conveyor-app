<!-- DRAFT: This document is a technical template. Must be reviewed by a qualified lawyer before publication. -->

# Legal Documents

- [Terms of Service](./TERMS.md)
- [Privacy Policy](./PRIVACY.md)

⚠️ **These are technical templates.** Must be reviewed by a lawyer before publication.

## What is here

| File | Purpose |
| --- | --- |
| [`TERMS.md`](./TERMS.md) | Terms of Service — 11 sections, required by Stripe before payments can be approved. |
| [`PRIVACY.md`](./PRIVACY.md) | Privacy Policy — 8 sections, GDPR-oriented, documents sub-processors and retention. |

## How to use these templates

1. **Replace the placeholders.** Search for `[` in both files:

   | Placeholder | Replace with |
   | --- | --- |
   | `[Effective Date]` | Date the documents go live |
   | `[Company Legal Name]` | Registered legal entity name |
   | `[Your Country]` | Jurisdiction governing the Terms |
   | `[Company Postal Address]` | Registered address |
   | `[Representative Name and Address]` | EU/UK representative, if required |
   | `support@vishap.dev` | Real support address |
   | `privacy@vishap.dev` | Real privacy/DPO address |

2. **Verify the factual claims.** Sections that describe the implementation — Fernet
   encryption, HMAC webhook verification, JWT sessions, PII redaction, audit-trail
   hashes, observability stack — must match what actually ships. Re-read them after
   any change to the pipeline or infrastructure.

3. **Get legal review.** These are engineering drafts, not legal advice. A qualified
   lawyer in your jurisdiction must review them before publication.

4. **Publish.** Copy both files into `docs-site/docs/legal/` as `terms.md` and
   `privacy.md` (the Docusaurus mirrors of these documents), register them in
   `docs-site/sidebars.ts` under the `Legal` category, and link them from the
   landing page footer.

5. **Register with Stripe.** In the Stripe Dashboard go to
   **Settings → Public Details** and add the public URLs of both documents.
   Stripe will not approve live payments without them.

## Known gaps (TODO before launch)

- `GET /api/me/data` and `DELETE /api/me/data` — self-service export/deletion
  endpoints are referenced by the Privacy Policy but **not implemented yet**.
- Governing law and jurisdiction are placeholders — must be chosen deliberately.
- No EU/UK representative has been appointed.
- The 90-day material retention window is a policy statement; confirm the storage
  layer actually enforces it.

## Mirrors

`docs/legal/` is the editable source. `docs-site/docs/legal/` holds the copies that
Docusaurus renders at `/docs/legal/terms` and `/docs/legal/privacy`. They differ
only in relative link targets (`./PRIVACY.md` vs `./privacy`), so **edit both** —
or delete the mirror and generate it if the duplication becomes a burden.
