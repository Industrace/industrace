# Print System

Industrace generates PDF documents **server-side with ReportLab**. There is no browser/Vue print layout path.

## What you can print

| Feature | Where | API |
|---------|--------|-----|
| Asset sheet (scheda asset) | Asset detail → Print | `POST /print/generate` then `GET /print/download/{print_id}` |
| Printed Kit (tenant pack) | Setup → Printed Kit | `POST /print/kit` then `GET /print/kit/download/{filename}` |

Default templates (`asset-card`, `asset-summary`) are seeded from Setup → Print Templates → initialize defaults, or `POST /print/templates/init-defaults`. Template keys are unique **per tenant**, so each tenant can seed the same defaults.

## Language and options

- Asset print: pass `options.language` (`en` / `it`). Alias `lang` is accepted. Unknown values fall back to `en`.
- Template options (camelCase or snake_case) are honoured: `includePhoto`, `includeQR`, `includeConnections`, `includeRiskMatrix`, `includeCustomFields`.
- Printed Kit: use `include_assets`, `include_sites`, `include_contacts`, `include_suppliers` (snake_case). The UI may send camelCase (`includeAssets`, …); the API accepts both. Language via `language` or `lang`.

Asset and kit PDFs are stored under `uploads/prints/{tenant_id}/`. Kit download is tenant-scoped and rejects path traversal.

## Architecture note

PDF rendering is **ReportLab only** (`backend/app/services/pdf_generator.py`). The field `component` on print templates is a renderer key (e.g. `reportlab-asset-card`), not a Vue component name. Legacy Vue print layouts were removed. Global templates cannot be updated or deleted by a tenant.

## Configuration

No `FEATURE_PRINT_SYSTEM` flag exists. Print endpoints are available to users with **assets** section access (RBAC). Upload directory defaults to `uploads/prints` (override via `PDFGenerator` / deployment volume mounts).

## Migrations

The print-templates unique constraint migration (`print_tpl_tenant_key`) is applied automatically on backend startup (`alembic upgrade heads` in `main.py`). After pulling a new image, a restart/rebuild is enough; a manual `alembic upgrade` is optional (useful for verifying heads before traffic).
