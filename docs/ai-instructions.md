# OpenAEC Report Generator — AI Integration Guide

Instructions for AI assistants (Cursor, Copilot, Windsurf, Claude, etc.) to generate professional engineering reports using the OpenAEC report generator platform.

---

## 1. Overview

`openaec-reports` is a PDF report generator for professional engineering reports (structural calculations, daylight analysis, building code assessments, etc.). It exposes a REST API and an MCP server. You provide JSON describing the report structure; the platform renders a pixel-perfect A4/A3 PDF with full house-style branding.

**Base URL:** `http://localhost:8000` (default, configurable via environment)

**Key principle:** The data interface is always JSON. You describe what the report should contain; the engine handles layout, typography, stationery, and branding.

**Three rendering engines are available:**
- `/api/generate` — ReportLab engine (fast, no branding required)
- `/api/generate/v2` — ReportGeneratorV2 (pixel-perfect stationery branding)
- `/api/generate/template` — TemplateEngine (YAML-driven, multi-tenant, recommended for tenant-specific reports)

---

## 2. Authentication

All API endpoints except `GET /api/health`, `POST /api/auth/login`, `POST /api/auth/register`, and `GET /api/auth/registration-enabled` require authentication.

Four methods are supported, checked in this priority order:

### Method 1 — API Key (recommended for automated tools and scripts)

```http
X-API-Key: 3bm_k_your_api_key_here
```

API keys start with the prefix `3bm_k_` and contain 64 hex characters. They are created via the admin panel or admin API. Each key is linked to a user and inherits that user's permissions and tenant.

### Method 2 — HTTP-only Cookie (browser sessions)

Automatically set after a successful login via `POST /api/auth/login`. No manual header needed. The cookie is `httpOnly` and `secure` in production.

### Method 3 — Bearer Token (local JWT, after login)

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5...
```

The token is returned in the login response body as the `token` field.

### Method 4 — OIDC Bearer Token (Authentik SSO)

```http
Authorization: Bearer <oidc_access_or_id_token>
```

The server validates the token against the configured OIDC provider (Authentik). On first login, the user is auto-provisioned.

### Login Flow

```http
POST /api/auth/login
Content-Type: application/json

{"username": "your_username", "password": "your_password"}
```

Response:
```json
{
  "user": {
    "id": "abc123...",
    "username": "your_username",
    "email": "you@example.com",
    "display_name": "A. Jansen",
    "role": "user",
    "tenant": "3bm_cooperatie"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5..."
}
```

The response also sets an `httpOnly` cookie. Use either the `token` field (as a Bearer header) or the cookie for subsequent requests.

---

## 3. API Endpoints

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/login` | None | Login with username + password |
| `POST` | `/api/auth/logout` | None | Clear the auth cookie |
| `POST` | `/api/auth/register` | None | Self-service registration (if enabled) |
| `GET` | `/api/auth/registration-enabled` | None | Check if self-registration is open |
| `GET` | `/api/auth/me` | Required | Current user info |
| `GET` | `/api/auth/oidc/config` | None | OIDC configuration for frontend |
| `POST` | `/api/auth/oidc/token-exchange` | None | Exchange OIDC token for session |
| `POST` | `/api/auth/oidc/code-exchange` | None | Server-side Authorization Code flow |

### Core — Discovery

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/health` | None | Health check — `{"status": "ok", "version": "..."}` |
| `GET` | `/api/templates` | Required | List available report templates |
| `GET` | `/api/templates/{name}/scaffold` | Required | Get empty JSON scaffold for a template |
| `GET` | `/api/brands` | Required | List available brand configurations |
| `GET` | `/api/stationery` | Required | List stationery files per brand |

### Core — Generation

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/validate` | Required | Validate report JSON against schema |
| `POST` | `/api/generate` | Required | Generate PDF — ReportLab engine |
| `POST` | `/api/generate/v2` | Required | Generate PDF — v2 renderer (pixel-perfect branding) |
| `POST` | `/api/generate/template` | Required | Generate PDF — TemplateEngine (YAML-driven, multi-tenant) |
| `POST` | `/api/upload` | Required | Upload an image file for use in reports |

### Storage — Projects

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/projects` | Required | List projects for the current user |
| `POST` | `/api/projects` | Required | Create a new project |
| `GET` | `/api/projects/{id}` | Required | Get project detail + report list |
| `PUT` | `/api/projects/{id}` | Required | Update project name/description |
| `DELETE` | `/api/projects/{id}` | Required | Delete project and all its reports |

### Storage — Reports (saved JSON, not PDFs)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/reports` | Required | List saved reports (optionally filter by project) |
| `POST` | `/api/reports` | Required | Save report JSON (create or update) |
| `GET` | `/api/reports/{id}` | Required | Get saved report (metadata + content JSON) |
| `PUT` | `/api/reports/{id}` | Required | Update saved report |
| `DELETE` | `/api/reports/{id}` | Required | Delete saved report |
| `PUT` | `/api/reports/{id}/move` | Required | Move report to a different project |

**Which generate endpoint to use:**
- `/api/generate/template` — for multi-tenant production reports with YAML-driven templates
- `/api/generate/v2` — for pixel-perfect reports with stationery branding
- `/api/generate` — for quick tests or when no branding is needed

---

## 4. Report JSON Format

The root object has two required fields (`template` and `project`).

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template` | string | Yes | Template name (e.g. `"structural"`, `"daylight"`) |
| `project` | string | Yes | Project name |
| `project_number` | string | No | Project number (e.g. `"2026-031"`) |
| `client` | string | No | Client / principal name |
| `author` | string | No | Author (default: `"3BM Bouwkunde"`) |
| `date` | string | No | Report date, ISO 8601 (default: today) |
| `version` | string | No | Document version (default: `"1.0"`) |
| `status` | string | No | `"CONCEPT"`, `"DEFINITIEF"`, or `"REVISIE"` |
| `format` | string | No | `"A4"` or `"A3"` (default: `"A4"`) |
| `orientation` | string | No | `"portrait"` or `"landscape"` (default: `"portrait"`) |
| `brand` | string | No | Brand slug (e.g. `"3bm_cooperatie"`, `"symitech"`) |
| `tenant` | string | No | Tenant identifier (determines which modules are available) |
| `cover` | object | No | Cover page configuration |
| `colofon` | object | No | Colophon / document information page |
| `toc` | object | No | Table of contents configuration |
| `sections` | array | No | Report sections (main content) |
| `backcover` | object | No | Back cover page |
| `metadata` | object | No | Free-form metadata (Revit info, software versions, etc.) |

### Cover Object

```json
"cover": {
  "subtitle": "Structural calculation — main load-bearing structure",
  "image": "renders/facade_west.png",
  "extra_fields": {
    "Reference": "3BM-2026-031-R01",
    "Classification": "Confidential"
  }
}
```

The `image` field accepts a file path, URL, or base64 object (see Section 6, Image Sources).

### Colofon Object

```json
"colofon": {
  "enabled": true,
  "opdrachtgever_naam": "Municipality of The Hague",
  "opdrachtgever_contact": "J. de Vries",
  "opdrachtgever_adres": "Spui 70, 2511 BT Den Haag",
  "adviseur_bedrijf": "3BM Bouwkunde",
  "adviseur_naam": "A. Jansen",
  "adviseur_email": "a.jansen@3bm.nl",
  "adviseur_telefoon": "+31 70 123 4567",
  "adviseur_functie": "Structural Engineer",
  "adviseur_registratie": "IBS-12345",
  "normen": "NEN-EN 1990 t/m 1999 with Dutch National Annexes",
  "fase": "Preliminary design",
  "kenmerk": "3BM-2026-031-R01",
  "datum": "2026-03-11",
  "status_colofon": "CONCEPT",
  "disclaimer": "This report is prepared by 3BM Bouwkunde...",
  "revision_history": [
    {
      "version": "0.1",
      "date": "2026-01-15",
      "author": "A. Jansen",
      "description": "First draft"
    },
    {
      "version": "1.0",
      "date": "2026-03-11",
      "author": "A. Jansen",
      "description": "Final version"
    }
  ]
}
```

**Auto-fill from user profile:** If a field is absent from the colophon, the API fills it automatically from the authenticated user's profile: `adviseur_naam` ← `display_name`, `adviseur_email` ← `email`, `adviseur_telefoon` ← `phone`, `adviseur_functie` ← `job_title`, `adviseur_registratie` ← `registration_number`, `adviseur_bedrijf` ← `company`.

### TOC Object

```json
"toc": {
  "enabled": true,
  "title": "Table of Contents",
  "max_depth": 3
}
```

`max_depth` controls how many heading levels appear in the TOC (1–3).

### Sections Array

Sections form the main body of the report. Each section has a title, a heading level, and a list of content blocks.

```json
"sections": [
  {
    "title": "Design Basis",
    "level": 1,
    "page_break_before": false,
    "orientation": "portrait",
    "content": [
      { "type": "paragraph", "text": "This report describes..." }
    ]
  }
]
```

**Section fields:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Section title (appears in TOC) |
| `level` | integer | Heading level: 1 = chapter, 2 = section, 3 = sub-section |
| `content` | array | List of content blocks |
| `orientation` | string | Override page orientation for this section |
| `page_break_before` | boolean | Start this section on a new page (default: `false`) |

---

## 5. Content Block Types

Every item in a section's `content` array is a content block identified by a required `"type"` field. There are 15 types.

---

### paragraph

Plain text with optional inline markup.

```json
{
  "type": "paragraph",
  "text": "All calculations follow <b>NEN-EN 1993-1-1</b> with the <i>Dutch National Annex</i>.",
  "style": "Normal"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `text` | Yes | Text content. Supports `<b>`, `<i>`, `<sub>`, `<sup>` markup |
| `style` | No | Style name from stylesheet (default: `"Normal"`) |

---

### calculation

Formatted engineering calculation block showing formula, substitution, and result.

```json
{
  "type": "calculation",
  "title": "Bending moment at mid-span",
  "formula": "M_Ed = q × l² / 8",
  "substitution": "M_Ed = 8.5 × 6.0² / 8",
  "result": "38.3",
  "unit": "kNm",
  "reference": "NEN-EN 1993-1-1"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Name of the calculation |
| `formula` | No | Mathematical formula as a string |
| `substitution` | No | Formula with values substituted |
| `result` | No | Calculated result value (string) |
| `unit` | No | Unit of the result (e.g. `"kNm"`, `"mm"`, `"kN/m²"`) |
| `reference` | No | Norm or standard reference |

---

### check

Unity check block — compares a calculated value against a limit.

```json
{
  "type": "check",
  "description": "Bending unity check beam L1",
  "required_value": "UC ≤ 1.0",
  "calculated_value": "M_Ed / M_Rd = 38.3 / 100.9",
  "unity_check": 0.38,
  "limit": 1.0,
  "reference": "NEN-EN 1993-1-1 §6.2.5"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | Description of the check |
| `required_value` | No | Requirement as text (e.g. `"UC ≤ 1.0"`) |
| `calculated_value` | No | Calculated value as text |
| `unity_check` | No | Utilization ratio as a number (0.0–∞) |
| `limit` | No | Pass/fail threshold (default: `1.0`) |
| `result` | No | `"VOLDOET"` (pass) or `"VOLDOET NIET"` (fail). Auto-derived from `unity_check` vs `limit` if omitted |
| `reference` | No | Norm reference |

**Unity check rendering:**
- `unity_check < limit` → green (passes)
- `unity_check == limit` → orange (borderline)
- `unity_check > limit` → red (fails)

---

### table

Data table with column headers and rows.

```json
{
  "type": "table",
  "title": "Applied materials",
  "headers": ["Element", "Material", "Grade"],
  "rows": [
    ["Foundation",   "Reinforced concrete", "C20/25"],
    ["Floor slab",   "Reinforced concrete", "C28/35"],
    ["Main beams",   "Steel",               "S355"],
    ["Columns",      "Steel",               "S355"]
  ],
  "column_widths": [60, 80, 50],
  "style": "default"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `headers` | Yes | Column names as array of strings |
| `rows` | Yes | 2D array of cell values |
| `title` | No | Table title |
| `column_widths` | No | Column widths in mm. Auto-calculated if omitted |
| `style` | No | `"default"`, `"minimal"`, or `"striped"` |

---

### image

Embed an image with optional caption and alignment.

```json
{
  "type": "image",
  "src": "renders/facade_west.png",
  "caption": "West facade — architectural render",
  "width_mm": 140,
  "alignment": "center"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `src` | Yes | Image source — see Section 6 (Image Sources) |
| `caption` | No | Caption text displayed below the image |
| `width_mm` | No | Width in mm. Auto-fit to page width if omitted |
| `alignment` | No | `"left"`, `"center"`, or `"right"` (default: `"center"`) |

---

### map

Embed a cadastral/topographic map from the Dutch PDOK WMS service (free, no API key needed). Works only for locations in the Netherlands.

```json
{
  "type": "map",
  "center": { "lat": 52.0975, "lon": 4.2200 },
  "radius_m": 150,
  "layers": ["percelen", "bebouwing", "luchtfoto"],
  "width_mm": 160,
  "caption": "Cadastral location — Kijkduin"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `center` | No* | `{"lat": ..., "lon": ...}` — WGS84 coordinates |
| `bbox` | No* | Bounding box: `{"min_x", "min_y", "max_x", "max_y"}` |
| `radius_m` | No | Radius in meters around center (default: `100`) |
| `layers` | No | Any combination of `"percelen"`, `"bebouwing"`, `"bestemmingsplan"`, `"luchtfoto"` (default: `["percelen", "bebouwing"]`) |
| `width_mm` | No | Map width in mm (default: `170`) |
| `caption` | No | Caption text |

*Either `center` or `bbox` should be provided.

---

### bullet_list

Bulleted list of items.

```json
{
  "type": "bullet_list",
  "items": [
    "NEN-EN 1990:2019 — Basis of structural design",
    "NEN-EN 1991-1-1:2005 — Self-weight and imposed loads",
    "NEN-EN 1993-1-1:2006 — Design of steel structures"
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `items` | Yes | Array of strings, one per bullet |

---

### heading_2

Sub-heading (H2) within a section. Can also serve as a section delimiter in appendices.

```json
{
  "type": "heading_2",
  "number": "1.1",
  "title": "Material Properties"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Heading text |
| `number` | No | Optional number label (e.g. `"1.1"`) |

---

### spacer

Vertical whitespace between content blocks.

```json
{
  "type": "spacer",
  "height_mm": 10
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `height_mm` | No | Height in mm (default: `5`) |

---

### page_break

Force a new page at this position.

```json
{
  "type": "page_break"
}
```

No additional fields.

---

### raw_flowable

Direct ReportLab Flowable instantiation. **Library-only — do not use via the API.** This is an escape hatch for direct Python usage.

```json
{
  "type": "raw_flowable",
  "class_name": "HRFlowable",
  "kwargs": {"width": "100%", "thickness": 1}
}
```

---

### bic_table

BIC (Bouwtechnische Inventarisatiecheck) control table. **Symitech tenant module only.**

```json
{
  "type": "bic_table",
  "location_name": "Winkelstraat 12, Amsterdam",
  "sections": [
    {
      "title": "Brandveiligheid",
      "rows": [
        {
          "label": "Brandcompartimentering",
          "ref_value": "≤ 1000 m²",
          "actual_value": "750 m²",
          "is_currency": false
        }
      ]
    }
  ],
  "summary": {
    "total_score": "8/10",
    "remarks": "Minor deficiencies noted"
  }
}
```

---

### cost_summary

Cost summary table. **Symitech tenant module only.**

```json
{
  "type": "cost_summary",
  "columns": ["Description", "Quantity", "Unit price", "Total"],
  "rows": [
    ["Structural steel",    "12.5 ton",  "€ 2.400", "€ 30.000"],
    ["Concrete foundation", "45 m³",     "€ 180",   "€  8.100"]
  ],
  "total": {
    "label": "Total excl. VAT",
    "amount": "€ 38.100"
  }
}
```

---

### location_detail

Location data block with client and property information. **Symitech tenant module only.**

```json
{
  "type": "location_detail",
  "client": {
    "name": "ABC Vastgoed B.V.",
    "contact": "M. de Boer",
    "address": "Industrieweg 5",
    "postal_code": "3542 AD",
    "city": "Utrecht",
    "phone": "030-123 4567",
    "email": "info@abcvastgoed.nl"
  },
  "location": {
    "name": "Winkelstraat 12",
    "address": "Winkelstraat 12",
    "postal_code": "1012 AB",
    "city": "Amsterdam",
    "cadastral": "AMS G 1234"
  },
  "photo_path": "photos/location_front.jpg"
}
```

---

### object_description

Object description block with key-value fields. **Symitech tenant module only.**

```json
{
  "type": "object_description",
  "object_name": "Kantoorgebouw Winkelstraat 12",
  "fields": [
    { "label": "Bouwjaar",         "value": "1978" },
    { "label": "Gebruiksfunctie",  "value": "Kantoorfunctie" },
    { "label": "Vloeroppervlak",   "value": "1.250 m²" },
    { "label": "Aantal verdiepingen", "value": "4" }
  ],
  "notes": "The building underwent partial renovation in 2005.",
  "photo_path": "photos/object_front.jpg"
}
```

---

## 6. Image Sources

The `src` field on `image` blocks, the `image` field on `cover`, and `photo_path` fields on Symitech blocks all accept three formats:

**Format 1 — File path (string)**
```json
"src": "renders/facade_west.png"
```
Can be absolute or relative. Relative paths are resolved from the server's working directory.

**Format 2 — URL (string)**
```json
"src": "https://example.com/images/facade.png"
```

**Format 3 — Base64 encoded data (object)**
```json
"src": {
  "data": "iVBORw0KGgoAAAANSUhEUgAAA...",
  "media_type": "image/png",
  "filename": "facade_west.png"
}
```

Supported `media_type` values: `"image/png"`, `"image/jpeg"`, `"image/svg+xml"`.

Use the base64 format when calling the API from an environment where the server cannot reach local files.

---

## 7. Workflow (Step by Step)

### Step 1 — Check the server

```http
GET /api/health
```

Expected response: `{"status": "ok", "version": "x.y.z"}`

### Step 2 — Authenticate

Obtain an API key from the admin panel, or login:

```http
POST /api/auth/login
Content-Type: application/json

{"username": "your_username", "password": "your_password"}
```

Save the `token` from the response or rely on the cookie.

### Step 3 — List available templates

```http
GET /api/templates
X-API-Key: 3bm_k_your_api_key_here
```

Response:
```json
{
  "templates": [
    {"name": "structural",     "report_type": "structural"},
    {"name": "daylight",       "report_type": "daylight"},
    {"name": "building_code",  "report_type": "building_code"}
  ]
}
```

### Step 4 — Get a scaffold

```http
GET /api/templates/structural/scaffold
X-API-Key: 3bm_k_your_api_key_here
```

Returns a pre-filled JSON object with all required fields set to defaults. Use this as the starting point for a new report.

### Step 5 — Fill in the report JSON

Replace placeholder values in the scaffold with actual project data. Add sections and content blocks to the `sections` array. Remove unused optional fields.

### Step 6 — Validate

```http
POST /api/validate
X-API-Key: 3bm_k_your_api_key_here
Content-Type: application/json

{ ...your report JSON... }
```

Success response:
```json
{"valid": true, "errors": []}
```

Failure response:
```json
{
  "valid": false,
  "errors": [
    {
      "path": "sections/0/content/1/type",
      "message": "'calcualtion' is not valid under any of the given schemas"
    }
  ]
}
```

Fix all errors before proceeding.

### Step 7 — Generate the PDF

```http
POST /api/generate/v2
X-API-Key: 3bm_k_your_api_key_here
Content-Type: application/json

{ ...your report JSON... }
```

The response is a binary PDF (`application/pdf`). The `Content-Disposition` header contains a suggested filename.

### Step 8 — Upload images (optional)

When the server cannot access local image files via path, upload them first:

```http
POST /api/upload
X-API-Key: 3bm_k_your_api_key_here
Content-Type: multipart/form-data

file=@facade_west.png
```

Response:
```json
{
  "path": "/app/uploads/a3f2b1c4d5e6.png",
  "filename": "a3f2b1c4d5e6.png",
  "size": 204800
}
```

Use the returned `path` as the `src` value in image blocks.

---

## 8. MCP Server Tools

If your AI tool supports MCP (Model Context Protocol), the `bm_reports` MCP server (`mcp__bm_reports__*`) provides the following tools:

| Tool | Description |
|------|-------------|
| `mcp__bm_reports__list_templates` | List all available report templates |
| `mcp__bm_reports__get_template_scaffold` | Get an empty JSON scaffold for a named template |
| `mcp__bm_reports__get_report_schema` | Get the full JSON schema (use as authoritative reference) |
| `mcp__bm_reports__get_block_examples` | Get example JSON for every content block type |
| `mcp__bm_reports__get_example_report` | Get a complete example report JSON |
| `mcp__bm_reports__list_brands` | List available brand configurations |
| `mcp__bm_reports__validate_report` | Validate report JSON against the schema |
| `mcp__bm_reports__generate_report` | Generate a PDF (ReportLab engine) |
| `mcp__bm_reports__generate_report_v2` | Generate a PDF (v2 renderer — pixel-perfect branding) |

### Typical MCP sequence

1. Call `mcp__bm_reports__list_templates` to see which templates are available.
2. Call `mcp__bm_reports__get_template_scaffold` with the chosen template name.
3. Call `mcp__bm_reports__get_block_examples` for reference when building content blocks.
4. Construct the report JSON with actual project data.
5. Call `mcp__bm_reports__validate_report` with the JSON. Fix any reported errors.
6. Call `mcp__bm_reports__generate_report_v2` with the validated JSON to produce the PDF.

---

## 9. Complete Example Report JSON

A self-contained, production-ready report demonstrating most content block types.

```json
{
  "template": "structural",
  "format": "A4",
  "project": "Harbour Viewing Platform",
  "project_number": "2026-042",
  "client": "Port Authority Rotterdam",
  "author": "3BM Bouwkunde",
  "date": "2026-03-11",
  "version": "1.0",
  "status": "CONCEPT",
  "brand": "3bm_cooperatie",

  "cover": {
    "subtitle": "Structural calculation — main load-bearing structure",
    "extra_fields": {
      "Reference": "3BM-2026-042-R01"
    }
  },

  "colofon": {
    "enabled": true,
    "opdrachtgever_naam": "Port Authority Rotterdam",
    "opdrachtgever_contact": "J. van den Berg",
    "opdrachtgever_adres": "Wilhelminakade 909, 3072 AP Rotterdam",
    "adviseur_bedrijf": "3BM Bouwkunde",
    "adviseur_naam": "A. Jansen",
    "adviseur_email": "a.jansen@3bm.nl",
    "adviseur_telefoon": "+31 70 123 4567",
    "adviseur_functie": "Structural Engineer",
    "normen": "NEN-EN 1990 t/m 1999 with Dutch National Annexes",
    "fase": "Preliminary design",
    "kenmerk": "3BM-2026-042-R01",
    "datum": "2026-03-11",
    "status_colofon": "CONCEPT",
    "revision_history": [
      {
        "version": "0.1",
        "date": "2026-02-01",
        "author": "A. Jansen",
        "description": "First draft"
      },
      {
        "version": "1.0",
        "date": "2026-03-11",
        "author": "A. Jansen",
        "description": "Final for review"
      }
    ]
  },

  "toc": {
    "enabled": true,
    "max_depth": 2
  },

  "sections": [
    {
      "title": "Design Basis",
      "level": 1,
      "content": [
        {
          "type": "paragraph",
          "text": "This report covers the structural calculation for the main load-bearing structure of the harbour viewing platform at Rotterdam. All calculations comply with the Eurocode suite and the Dutch National Annexes."
        },
        {
          "type": "heading_2",
          "number": "1.1",
          "title": "Applicable Standards"
        },
        {
          "type": "bullet_list",
          "items": [
            "NEN-EN 1990:2019 — Basis of structural design",
            "NEN-EN 1991-1-1:2005 — Self-weight and imposed loads",
            "NEN-EN 1993-1-1:2006 — Design of steel structures",
            "NEN-EN 1997-1:2005 — Geotechnical design"
          ]
        },
        {
          "type": "heading_2",
          "number": "1.2",
          "title": "Materials"
        },
        {
          "type": "table",
          "title": "Applied materials",
          "headers": ["Element", "Material", "Grade"],
          "rows": [
            ["Main beams",        "Steel",               "S355"],
            ["Secondary beams",   "Steel",               "S235"],
            ["Concrete slab",     "Reinforced concrete", "C28/35"],
            ["Foundation piles",  "Reinforced concrete", "C35/45"]
          ],
          "column_widths": [70, 80, 50]
        }
      ]
    },

    {
      "title": "Loads",
      "level": 1,
      "content": [
        {
          "type": "paragraph",
          "text": "Loads are determined in accordance with <b>NEN-EN 1991-1-1</b>."
        },
        {
          "type": "heading_2",
          "number": "2.1",
          "title": "Permanent Loads"
        },
        {
          "type": "paragraph",
          "text": "Reinforced concrete: 25 kN/m³. Steel deck: 0.8 kN/m². Finishes: 0.5 kN/m²."
        },
        {
          "type": "heading_2",
          "number": "2.2",
          "title": "Variable Loads"
        },
        {
          "type": "table",
          "title": "Load summary",
          "headers": ["Load type", "Value", "Standard"],
          "rows": [
            ["Imposed load — public area (cat. C3)", "5.0 kN/m²", "NEN-EN 1991-1-1 Table 6.2"],
            ["Wind load (basic)",                    "0.42 kN/m²", "NEN-EN 1991-1-4"],
            ["Snow load",                            "0.56 kN/m²", "NEN-EN 1991-1-3"]
          ],
          "column_widths": [80, 40, 80]
        }
      ]
    },

    {
      "title": "Structural Calculations",
      "level": 1,
      "page_break_before": true,
      "content": [
        {
          "type": "paragraph",
          "text": "All members are checked in the ultimate limit state (ULS) and serviceability limit state (SLS) according to <b>NEN-EN 1993-1-1</b>."
        },
        {
          "type": "heading_2",
          "number": "3.1",
          "title": "Main Beam B1 — HEA 260"
        },
        {
          "type": "calculation",
          "title": "Design bending moment",
          "formula": "M_Ed = q_d × l² / 8",
          "substitution": "M_Ed = 12.4 × 7.5² / 8",
          "result": "87.2",
          "unit": "kNm",
          "reference": "NEN-EN 1993-1-1"
        },
        {
          "type": "calculation",
          "title": "Plastic moment resistance",
          "formula": "M_Rd = W_pl,y × f_y / γ_M0",
          "substitution": "M_Rd = 919.8×10³ × 355 / 1.0",
          "result": "326.5",
          "unit": "kNm",
          "reference": "NEN-EN 1993-1-1 §6.2.5"
        },
        {
          "type": "check",
          "description": "ULS bending check — beam B1",
          "required_value": "UC ≤ 1.0",
          "calculated_value": "M_Ed / M_Rd = 87.2 / 326.5",
          "unity_check": 0.27,
          "limit": 1.0,
          "reference": "NEN-EN 1993-1-1 §6.2.5"
        },
        {
          "type": "check",
          "description": "SLS deflection check — beam B1",
          "required_value": "δ ≤ l/250 = 30.0 mm",
          "calculated_value": "δ_max = 14.8 mm",
          "unity_check": 0.49,
          "limit": 1.0,
          "reference": "NEN-EN 1993-1-1 §7.2"
        },
        {
          "type": "spacer",
          "height_mm": 8
        },
        {
          "type": "heading_2",
          "number": "3.2",
          "title": "Summary — Unity Checks"
        },
        {
          "type": "table",
          "title": "Unity check summary — all members",
          "headers": ["Member", "Check", "UC", "Result"],
          "rows": [
            ["B1 — HEA 260", "Bending (ULS)",    "0.27", "PASS"],
            ["B1 — HEA 260", "Deflection (SLS)", "0.49", "PASS"],
            ["B2 — HEA 200", "Bending (ULS)",    "0.61", "PASS"],
            ["B2 — HEA 200", "Shear (ULS)",      "0.38", "PASS"]
          ],
          "column_widths": [55, 55, 25, 35],
          "style": "striped"
        }
      ]
    },

    {
      "title": "Project Location",
      "level": 1,
      "content": [
        {
          "type": "paragraph",
          "text": "The project is located at the Rotterdam harbour, Wilhelminakade."
        },
        {
          "type": "map",
          "center": { "lat": 51.9050, "lon": 4.4685 },
          "radius_m": 200,
          "layers": ["percelen", "bebouwing"],
          "width_mm": 160,
          "caption": "Cadastral location — Rotterdam harbour"
        }
      ]
    }
  ],

  "backcover": {
    "enabled": true
  },

  "metadata": {
    "software": "OpenAEC Report Generator",
    "calculation_software": "Manual calculation"
  }
}
```

---

## 10. Tips for AI Assistants

**Always validate before generating.** The `POST /api/validate` endpoint catches schema errors early. Fix every reported error before calling generate.

**Use scaffolds as a starting point.** Call `GET /api/templates/{name}/scaffold` to get a pre-structured JSON with defaults already filled. This is faster and less error-prone than building from scratch.

**Content blocks are freely composable.** Add, remove, and reorder blocks in `content` arrays without restriction. There is no limit on blocks per section.

**Authentication priority order:** X-API-Key > cookie > Bearer JWT > OIDC token. For scripting and automation, always use an API key via `X-API-Key`.

**Unity check values:**
- `0.0` → 0% utilization
- `0.8` → 80% utilization (acceptable)
- `1.0` → exactly at the limit (pass, borderline)
- `1.05` → 5% over limit (fail)
- Omit `result` — it is auto-derived from `unity_check` vs `limit`.

**Images:**
- Use file paths for files accessible to the server, URLs for remote images, or base64 objects for embedded data.
- Upload local images via `POST /api/upload` when the server cannot reach them directly.
- `width_mm` is optional — images auto-fit to the page width if omitted.
- All dimensions are in mm.

**Sections and heading levels:**
- Level 1 = Chapter (always in TOC)
- Level 2 = Section (in TOC if `max_depth >= 2`)
- Level 3 = Sub-section (in TOC if `max_depth = 3`)
- Use `"page_break_before": true` to start a new chapter on a fresh page.

**Dates:** Always use ISO 8601 format: `"YYYY-MM-DD"` (e.g. `"2026-03-11"`).

**Which renderer to use:**
- `/api/generate/template` — production reports with tenant-specific YAML templates and branding
- `/api/generate/v2` — pixel-perfect stationery branding without YAML template
- `/api/generate` — quick tests or when no branding is needed

**Colophon auto-fill:** Fields missing from the `colofon` object are filled from the authenticated user's profile (`adviseur_naam`, `adviseur_email`, `adviseur_telefoon`, `adviseur_functie`, `adviseur_registratie`, `adviseur_bedrijf`). Only provide them explicitly to override the profile values.

**Multi-tenant setup:** The `brand` field selects the visual identity (stationery, logo, colors, fonts). The `tenant` field controls which modules are available. For tenant-specific block types (`bic_table`, `cost_summary`, `location_detail`, `object_description`), set `"tenant": "symitech"` and use the `symitech_{template}` template name prefix.

**Map blocks are Netherlands-only.** The `map` block uses the free Dutch PDOK WMS service. Coordinates must be within the Netherlands in WGS84 lat/lon.

**The `raw_flowable` block is library-only.** Do not use it via the REST API. It is an escape hatch for direct Python library usage only.

**Save report JSON before generating.** Use `POST /api/reports` to persist the report content JSON under a project. This allows you to retrieve and regenerate reports later without reconstructing the JSON from scratch.
