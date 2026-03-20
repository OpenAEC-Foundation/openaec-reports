# Frontend TODO — OpenAEC Reports UI

> Prioriteit: 🔴 Hoog | 🟡 Middel | 🟢 Laag
> Laatst bijgewerkt: 2026-03-20

---

## 🟡 Dark theme fine-tuning
- [ ] Visueel testen van `openaec` (dark) thema op productie
- [ ] Content area editors/formulieren controle op contrast
- [ ] FeedbackDialog visueel verifiëren met themed CSS variabelen

## 🟢 Geavanceerde Features (Toekomst)

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
- **Opmerking:** Tests en dev server draaien via lokale kopie (`C:\temp\openaec-reports-ui`) i.v.m. netwerkpad-incompatibiliteit met Vite/Vitest

---

## Afgerond

| Fase | Wat | Wanneer |
|------|-----|---------|
| 1-7 | Core editor, sidebar, blocks, metadata, API, bijlagen, UX | Week 5-8 |
| P5 | Rich text: Tiptap WYSIWYG editor | Week 8 |
| P6 | Visual polish: branding, iconen, toasts | Week 8 |
| P7 | Tech debt: Vitest, ErrorBoundary, env vars | Week 8 |
| P8 | Brand config: CSS custom properties | Week 8 |
| F-FINAL | renderer_v2 alignment | Week 8 |
| Chrome | OpenAEC Design System: TitleBar, Ribbon, Backstage, StatusBar | Week 12 |
| Auth | OIDC/Authentik SSO, user/role management | Week 12 |
| Admin | Admin panel + knop in Backstage/TitleBar dropdown | Week 12 |
| Save/Open | Server vs lokaal keuze dialogs (SaveAsDialog, OpenDialog) | Week 12 |
| Feedback | FeedbackDialog (Open Feedback Studio API) | Week 12 |
| i18n | Nederlands + Engels, 5 namespaces | Week 12 |
| Shortcuts | Ctrl+N (nieuw), ShortcutHelp themed + i18n | Week 12 |
