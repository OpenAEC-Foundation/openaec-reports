# TODO — bm-reports

> Prioriteit: 🔴 Blocker | 🟡 Middel | 🟢 Nice-to-have
> Laatst bijgewerkt: 2026-03-01
> Volgende actie: deploy met `docker build --no-cache`

---

## 🔴 DEPLOY — Frontend Rebuild + Deploy (BLOCKER)

Code fixes zijn gecommit (cfaa808). Frontend smart routing code was al correct, maar productie serveerde een gecachte bundle.

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
| 1 - Voorblad (portrait) | Stationery achtergrond, logo, kleurbanen, tekst op juiste positie |
| 2 - Locatie (portrait) | Stationery, labels links, waarden rechts, footer balk |
| 3 - BIC Controles (portrait) | Stationery, tabel met 3 kolommen, bedragen, footer |
| 4 - Detail weergave (LANDSCAPE) | Orientatie correct, 7 kolommen, stationery |
| 5 - Objecten (LANDSCAPE) | Orientatie correct, 8 kolommen, stationery |
| 6 - Achterblad (portrait) | Alleen stationery, geen tekst |

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
