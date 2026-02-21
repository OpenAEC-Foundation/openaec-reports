# Frontend TODO — Report Generator UI

> Prioriteit: 🔴 Hoog | 🟡 Middel | 🟢 Laag
> Prompts staan klaar voor Claude Code uitvoering.

---

## 🟢 P9 — Geavanceerde Features (Toekomst)

### Block Copy/Paste
- [ ] Kopieer block naar clipboard (Ctrl+C op geselecteerd block)
- [ ] Plak block in huidige of andere sectie (Ctrl+V)

### Section Templates
- [ ] "Voeg standaard sectie toe" met pre-filled blocks
- [ ] Constructief: Uitgangspunten, Belastingen, Berekeningen, Toetsing

### Multi-rapport
- [ ] Rapport lijst (localStorage of API)
- [ ] Rapport dupliceren / verwijderen

### Template Editor
- [ ] Visuele template configuratie
- [ ] Drag & drop sectie volgorde in template

### Revit Bridge
- [ ] WebSocket listener voor Revit push data
- [ ] Auto-fill berekening blocks vanuit Revit

---

## Test Resultaten

- **Tests:** 25 passing (2 test files)
- **Conversion round-trip:** 6 tests (minimal, full, ID stripping, unique IDs, bullet_list/heading_2, content_sections)
- **Store unit tests:** 19 tests (sections, blocks incl. bullet_list/heading_2, appendices, undo/redo, metadata, import/export)
- **TypeScript:** 0 errors (`npx tsc -b`)
- **Opmerking:** Tests en dev server draaien via lokale kopie (`C:\temp\bm-reports-ui`) i.v.m. netwerkpad-incompatibiliteit met Vite/Vitest

---

## Afgerond

| Fase | Wat | Wanneer |
|------|-----|---------|
| 1: Setup | Vite, Zustand, TypeScript, dnd-kit | Week 5 |
| 2: Sidebar | Section CRUD, drag & drop | Week 5 |
| 3: Block editors | 8 editors, alle block types | Week 6 |
| 4: Metadata | Tabs, cover, colofon, options, templates | Week 6 |
| 4fix: Bugfixes | Reordering, deletion, state sync | Week 7 |
| 5: API integratie | Preview, generate, download, validation | Week 7 |
| 6: Bijlagen | AppendixEditor, CRUD, reorder | Week 7 |
| 7: UX | JSON import/export, split view, undo/redo, auto-save, live preview, shortcuts | Week 8 |
| P5: Rich Text | Tiptap WYSIWYG editor in ParagraphEditor | Week 8 |
| P6: Visual Polish | 3BM branding, SVG iconen, inklapbare secties, floating toasts | Week 8 |
| P7: Tech Debt | Vitest tests, ErrorBoundary, env variables, build hardening | Week 8 |
| P8: Brand Config | Huisstijl als data: brand.ts, CSS vars, generieke Tailwind classes | Week 8 |
| F-FINAL: v2 Alignment | renderer_v2 alignment: bullet_list, heading_2, colofon, content_sections, API | Week 8 |
