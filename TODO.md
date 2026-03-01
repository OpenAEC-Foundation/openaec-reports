# TODO — bm-reports

> Prioriteit: 🔴 Blocker | 🟡 Middel | 🟢 Nice-to-have
> Laatst bijgewerkt: 2026-03-01 (pixel fixes + admin cleanup)
> Volgende actie: deploy met `docker build --no-cache`

---

## 🔴 DEPLOY — Frontend Rebuild + Deploy (BLOCKER)

Alle code fixes zijn gecommit (cfaa808, f3b8228, ab93b13). Frontend smart routing + replace button + BrandWizard cleanup klaar. Productie serveerde een gecachte bundle.

**Stappen:**
```bash
# 1. Docker build ZONDER cache
docker build --no-cache -t bm-reports:latest .

# 2. Test lokaal
docker run --rm -p 8000:8000 bm-reports:latest

# 3. Deploy naar VPS (git pull + rebuild)

# 4. Verificatie op productie
# → https://report.open-aec.com/api/health
# → Bundle check: fetch JS, search "generate/template"
# → Test Customer BIC PDF generatie via frontend
```

---

## 🟡 VALIDATE — Visuele Validatie na Deploy

Pas uitvoeren NADAT FIX-1, FIX-2, FIX-3 allemaal live staan.

**Test via productie frontend:**
1. Login op report.open-aec.com
2. Selecteer template "Customer BIC Factuur"
3. Laad test data of vul in
4. Genereer PDF
5. Vergelijk met referentie `Z:\50_projecten\7_OpenAEC_bouwkunde\temp\336.01-BIC Factuur_BIC.pdf`

**Checklist per pagina:**

| Pagina | Wat controleren |
|--------|----------------|
| 1 - Voorblad (portrait) | Stationery achtergrond, logo, kleurbanen, tekst op juiste positie (Arial) |
| 2 - Locatie (portrait) | Stationery, labels links, waarden rechts, footer balk, paginanummer |
| 3 - BIC Controles (portrait) | Stationery, tabel met 3 kolommen (fontsize 10pt), bedragen, footer |
| 4 - Detail weergave (LANDSCAPE) | Orientatie correct, 7 kolommen, stationery |
| 5 - Objecten (LANDSCAPE) | Orientatie correct, 8 kolommen, stationery |
| 6 - Achterblad (portrait) | Stationery + tekst "Deze pagina is [met opzet] leeg gelaten", footer, paginanummer |

**Referentie verschil (verwacht):**
- Generated: 5 XObjects/pagina, Reference: 10 XObjects/pagina
- Dit kan normaal zijn (reference bevat Word template artifacts)
- Belangrijk is visueel resultaat, niet exact image count

---

## 🟡 T3 — OpenAEC TemplateEngine Migratie (na validatie)

- [ ] T3.1 — OpenAEC page_type YAML's aanmaken
- [ ] T3.2 — OpenAEC template YAML's
- [ ] T3.3 — Flow mode engine integreren met block_registry

---

## 🟡 T4 — OpenAEC Rebranding

Alle OpenAEC-specifieke referenties uit de codebase halen (package naam, API endpoints, Docker labels, README, etc.). OpenAEC blijft alleen bestaan als tenant data (`tenants/default/`).

- [ ] T4.1 — Package rename: `bm_reports` → `openaec_reports`
- [ ] T4.2 — API prefix: `/api/` → blijft, maar branding aanpassen
- [ ] T4.3 — Docker image: `bm-reports` → `openaec-reports`
- [ ] T4.4 — Frontend: OpenAEC logo/naam → OpenAEC branding
- [ ] T4.5 — README, LICENSE, docs bijwerken
- [ ] T4.6 — Domain: `report.open-aec.com` → `reports.openaec.org` (of soortgelijk)

---

## 🟡 T5 — YAML Editor in Admin Panel

Self-service YAML beheer per tenant — geen git push nodig voor positioneering/styling.

**Fase 1 — Upload & beheer (quick win):**
- [ ] T5.1 — API: `/api/tenants/{tenant}/page_types/` CRUD endpoints
- [ ] T5.2 — Frontend: YAML file browser per tenant
- [ ] T5.3 — Upload/download YAML's + brand.yaml
- [ ] T5.4 — Preview: upload → render test-PDF → bekijk resultaat

**Fase 2 — Visuele editor:**
- [ ] T5.5 — YAML als formulier: text_zones bewerkbare rijen (x, y, font, size, color)
- [ ] T5.6 — Live preview bij wijziging
- [ ] T5.7 — Kleurenpicker uit brand.yaml

**Fase 3 — Brand onboarding wizard:**
- [ ] T5.8 — Upload brand guidelines PDF → auto-extractie kleuren/fonts
- [ ] T5.9 — Upload referentie PDF → coördinaten-extractie naar YAML
- [ ] T5.10 — Stationery PDF generator vanuit guidelines

---

## 🟢 Housekeeping

- [ ] `_temp_analyze.py` verwijderen uit project root
- [ ] CLAUDE.md updaten met TemplateEngine architectuur
- [ ] README.md updaten
- [ ] `lessons_learned.md` aanmaken

---

## 🟢 Infrastructure (later)

- [ ] Caddyfile vereenvoudigen
- [ ] fail2ban installeren
- [ ] Portainer installeren

---

## ✅ VOLTOOID

### Pixel Precision Fixes — 6 issues (1 maart, f3b8228)
- [x] Arial fonts: per-tenant font registratie via `font_files` in brand.yaml
- [x] Page numbering: "Pagina X van Y" met cover exclusion
- [x] Y-offset: font ascent correctie, delta <0.7pt
- [x] Image zones: `ImageZone` dataclass + `_draw_image_zones()` + locatie.yaml
- [x] Achterblad: text zones (leeg-gelaten tekst, footer, paginanummer)
- [x] BIC controles: table body fontsize → 10pt

### Admin Panel Cleanup (1 maart, ab93b13)
- [x] "Vervangen" knop per asset bestand in BrandManagement
- [x] Standalone BrandWizard (blauw, 3-stap) verwijderd (8 bestanden)
- [x] AdminTab type opgeschoond

### FIX-1 + FIX-2 — Tenant Resolution Fix (1 maart, cfaa808)
- [x] `_resolve_tenant_and_template()` — tenant uit template naam prefix
- [x] `_resolve_tenants_dir()` — robuust met `BM_TENANTS_ROOT` env var
- [x] Endpoint herschreven, 888 tests passed, E2E OK

### T-API — API Endpoint (28 feb)
- [x] `/api/generate/template` endpoint
- [x] `data_transform.py` module
- [x] Frontend smart routing (lokaal)
- [x] Integratietests

### T1 — Template Engine Fase 1 (28 feb)
- [x] 102+ unit tests, 3 E2E tests, 6-pagina PDF

### T2 — Stationery + Coördinaten (28 feb)
- [x] Referentie-gebaseerde coördinaten voor alle 6 page types

### CLEANUP — Mega Cleanup (28 feb)
- [x] Deprecated V1 Customer modules verwijderd
- [x] Prompts gearchiveerd
- [x] pytest cache opgeruimd
