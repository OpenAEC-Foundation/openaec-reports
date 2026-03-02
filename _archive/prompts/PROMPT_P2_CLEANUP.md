# P2: Opschonen — Beide Repositories

## Context

Beide repos (`Report_generator` en `Report_generator_frontend`) bevatten vervuiling van de ontwikkelfase: ~50 pytest cache mappen, 12+ afgeronde PROMPT bestanden, losse testscripts, en verouderde documentatie. Dit moet opgeruimd worden voordat het project naar productie gaat.

## Stap 1: Backend — pytest cache mappen verwijderen

De `Report_generator` root bevat ~50 `pytest-cache-files-*` mappen. Verwijder ze allemaal:

```powershell
cd "X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator"
Get-ChildItem -Directory -Filter "pytest-cache-files-*" | Remove-Item -Recurse -Force
```

Verifieer dat ze weg zijn:
```powershell
(Get-ChildItem -Directory -Filter "pytest-cache-files-*").Count
# Verwacht: 0
```

## Stap 2: Backend — Afgeronde PROMPT bestanden archiveren

Maak een `_archive/prompts/` map en verplaats alle afgeronde prompts:

```
PROMPT_B1_MAP_BLOCK.md          → _archive/prompts/
PROMPT_B2_API.md                → _archive/prompts/
PROMPT_B3_SCAFFOLD_LANDSCAPE.md → _archive/prompts/
PROMPT_BUGFIXES.md              → _archive/prompts/
PROMPT_BUGFIXES_B1_B2.md        → _archive/prompts/
PROMPT_FASE_A_BRAND_ANALYZER.md → _archive/prompts/
PROMPT_FASE_B_FIX_HUISSTIJL.md → _archive/prompts/
PROMPT_FASE_B_HUISSTIJL_CORRECTIES.md → _archive/prompts/
PROMPT_BRAND_BUILDER.md         → _archive/prompts/
PROMPT_HUISSTIJL_STUDIO.md      → _archive/prompts/
PROMPT_STATIONERY_EN_FIXES.md   → _archive/prompts/
PROMPT_TEST_SUITE.md            → _archive/prompts/
```

**Behoud** in de root (nog niet afgerond of referentie):
- `PROMPT_P1_STATIONERY_EXTRACTIE.md` (actief)
- Eventuele andere nieuwe PROMPT bestanden

**Verplaats ook:**
```
PLAN_HUISSTIJL_STUDIO.md        → _archive/plans/
PLAN_STATIONERY_ARCHITECTUUR.md → _archive/plans/
SPEC_PAGINA_ARCHITECTUUR.md     → _archive/specs/
COVER_SPEC.md                   → _archive/specs/
BACKEND_OPDRACHT.md             → _archive/specs/
```

## Stap 3: Backend — Losse test scripts verwijderen

Verwijder deze bestanden uit de root (hun functionaliteit is al in de test suite):

```
check_cu2qu.py
convert_fonts.py
fix_maxp.py
test_fonts.py
test_font_output.py
test_huisstijl_output.pdf
```

## Stap 4: Backend — CLAUDE.md actualiseren

Lees de huidige `CLAUDE.md` en update het zodat het de werkelijke status reflecteert:

1. Verwijder verouderde fasebeschrijvingen (fase 5-10 die deels achterhaald zijn)
2. Verwijs naar `STATUS.md` voor de actuele module status
3. Verwijs naar `TODO.md` voor openstaande taken
4. Houd de architectuur sectie en conventies intact
5. Voeg een "Quick start" sectie toe:

```markdown
## Quick Start

```bash
# Installeer
pip install -e ".[dev,brand-tools]"

# Tests draaien
python -m pytest tests/ -v

# API starten
openaec-report serve --port 8000 --reload

# Rapport genereren
openaec-report generate --template structural --data schemas/example_structural.json --output output/test.pdf
```
```

## Stap 5: Frontend — Afgeronde PROMPT bestanden archiveren

```
Report_generator_frontend/
├── PROMPT_BLOCK_EDITORS.md      → _archive/prompts/
├── PROMPT_BUGFIXES.md           → _archive/prompts/
├── PROMPT_BUGFIXES_FASE4.md     → _archive/prompts/
├── PROMPT_FASE4_METADATA.md     → _archive/prompts/
├── PROMPT_FASE5_API_INTEGRATIE.md → _archive/prompts/
├── PROMPT_FASE6_BIJLAGEN.md     → _archive/prompts/
├── PROMPT_FASE7_UX.md           → _archive/prompts/
```

Verwijder ook:
```
"claude --dangerously-skip-permissions.txt"  → verwijderen (geen nuttig bestand)
```

## Stap 6: Frontend — CLAUDE.md actualiseren

Zelfde aanpak als backend:
1. Verwijder verouderde fasebeschrijvingen
2. Verwijs naar `STATUS.md` en `TODO.md`
3. Voeg Quick Start toe:

```markdown
## Quick Start

```bash
npm install
npm run dev          # Dev server op http://localhost:5173
npm run build        # Productie build naar dist/
```

**Vereist:** Backend API op http://localhost:8000 (zie Report_generator)
```

## Stap 7: Verifieer dat alles nog werkt

### Backend:
```bash
cd "X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator"
python -m pytest tests/ -v --tb=short
```
**Verwacht:** Alle tests passen (het archiveren van prompts en scripts raakt de test suite niet).

### Frontend:
```bash
cd "X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator_frontend"
npm run build
```
**Verwacht:** Geen build errors.

## Regels

1. **Verplaats, verwijder niet** — prompt bestanden gaan naar `_archive/`, niet de prullenbak
2. **Geen productie code wijzigen** — alleen documentatie en losse bestanden
3. **Test suite moet groen blijven** — draai tests na cleanup
4. **Commit-ready** — na deze prompt is de repo schoon genoeg voor een verse blik

## Verwachte output

Na afloop:
- 0 `pytest-cache-files-*` mappen in backend root
- `_archive/prompts/` met alle afgeronde prompts (beide repos)
- `_archive/plans/` en `_archive/specs/` met plannen/specs (backend)
- Bijgewerkte `CLAUDE.md` in beide repos
- Geen losse test scripts in backend root
- Alle tests nog steeds groen
