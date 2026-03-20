# Frontend Status — OpenAEC Reports UI

> Laatst bijgewerkt: 2026-03-20

## Deployment

| Component | URL | Status |
|-----------|-----|--------|
| **Productie** | https://report.open-aec.com/ | ✅ Live |
| **Backend API** | https://report.open-aec.com/api/* | ✅ Live |
| **Lokaal dev** | http://localhost:5173 → http://localhost:8000 | ✅ |

### Deploy procedure
1. Commit + push naar `main`
2. SSH naar Hetzner: `ssh jochem@46.224.215.142`
3. `cd /opt/openaec/bm-reports-api && git pull`
4. `cd /opt/openaec && docker compose build --no-cache bm-reports-api`
5. `docker compose up -d bm-reports-api`
6. Frontend kopiëren: `docker cp bm-reports-api:/app/static/. /tmp/fe/ && sudo cp -r /tmp/fe/* /opt/openaec/bm-reports-ui/dist/`

## Architectuur

```
src/
├── components/
│   ├── blocks/          # 10 block editors + RichTextEditor (Tiptap)
│   ├── editor/          # BlockEditor (met ErrorBoundary), BlockToolbox, AppendixEditor
│   ├── forms/           # MetadataTabs, CoverForm, ColofonForm, OptionsPanel, TemplateSelector
│   ├── chrome/          # OpenAEC Design System
│   │   ├── TitleBar.tsx + .css        # Quick access, user dropdown, SSO link
│   │   ├── StatusBar.tsx + .css       # Stats + connection indicator
│   │   ├── Modal.tsx + .css           # Generieke dialog
│   │   ├── ThemedSelect.tsx + .css    # Styled dropdown
│   │   ├── ribbon/                    # Office-style tabbed toolbar
│   │   │   ├── Ribbon.tsx + .css      # Container + animaties
│   │   │   ├── RibbonTab/Button/Group/Stack.tsx
│   │   │   ├── HomeTab.tsx            # Valideren
│   │   │   ├── InsertTab.tsx          # Block invoegen
│   │   │   ├── ViewTab.tsx            # Weergave + zijbalk
│   │   │   └── icons.ts              # SVG iconen
│   │   ├── backstage/                 # File menu overlay
│   │   │   ├── Backstage.tsx + .css   # Nieuw/Openen/Opslaan/OpslaanAls/etc.
│   │   │   ├── SaveAsDialog.tsx       # Server vs lokaal keuze
│   │   │   └── OpenDialog.tsx         # Server vs lokaal keuze
│   │   └── settings/
│   │       └── SettingsDialog.tsx + .css  # Thema/taal
│   ├── feedback/
│   │   └── FeedbackDialog.tsx + .css  # Issue/bug rapportage
│   ├── layout/
│   │   ├── AppShell.tsx               # Root orchestratie
│   │   ├── Sidebar.tsx                # Secties/bijlagen boom
│   │   ├── MainPanel.tsx              # Editor/preview/JSON modes
│   │   ├── ShortcutHelp.tsx           # Sneltoetsen dialog
│   │   └── ValidationBanner.tsx       # Validatie errors banner
│   ├── admin/
│   │   └── AdminPanel.tsx             # Gebruikers/template beheer
│   ├── projects/
│   │   └── ProjectBrowser.tsx         # Server rapporten browser
│   └── shared/
│       ├── ErrorBoundary.tsx
│       └── BlockIcons.tsx
├── config/
│   └── oidc.ts              # OIDC/Authentik SSO + getAuthentikUserUrl()
├── hooks/
│   └── useKeyboardShortcuts.ts  # Globale sneltoetsen
├── i18n/
│   ├── config.ts             # 5 namespaces: common, ribbon, backstage, settings, feedback
│   └── locales/{en,nl}/      # Vertalingen (NL + EN)
├── services/
│   └── api.ts                # Backend API client
├── stores/
│   ├── reportStore.ts        # Rapport state (secties, metadata, bijlagen, undo/redo)
│   ├── apiStore.ts           # API state (preview, generatie, templates, brands)
│   ├── authStore.ts          # Authenticatie (OIDC, user, role)
│   ├── projectStore.ts       # Server project/rapport CRUD
│   └── adminStore.ts         # Admin panel state
├── themes.css                # CSS custom properties (~80 tokens, 2 thema's)
├── types/
│   └── report.ts             # TypeScript types
└── utils/
    ├── conversion.ts         # Store → API JSON
    ├── defaults.ts           # Default block waarden
    ├── idGenerator.ts        # Unieke ID generator
    └── settingsStore.ts      # localStorage wrapper
```

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** — bundler
- **Zustand** — state management
- **Tailwind CSS** — utility styling
- **Tiptap** — rich text editor (paragraph blocks)
- **dnd-kit** — drag & drop
- **i18next** — internationalisatie (NL + EN)
- **Vitest** + **React Testing Library** — tests

## Design System: OpenAEC Chrome

Office-geïnspireerd design system met themed CSS custom properties.

| Component | Hoogte | Functie |
|-----------|--------|---------|
| TitleBar | 32px | App icon, quick access (save/undo/redo/settings/help), user dropdown |
| Ribbon tabs | 28px | File, Home, Insert, View — met sliding border animatie |
| Ribbon content | 94px | Groepen met knoppen (large/medium/small) |
| StatusBar | 22px | Document stats, connection indicator |

### Thema's
- `light` — Deep Forge (#36363E bg, #D97706 accent, #FAFAF9 text)
- `openaec` — Darker variant (#27272A bg)

### Features
- User dropdown met SSO profiel link (Authentik)
- Admin knop (conditional op `role === "admin"`) in Backstage + TitleBar dropdown
- Backstage: Nieuw, Openen (server/lokaal), Opslaan, Opslaan als (server/lokaal), Projecten, Instellingen, Beheer, Feedback, Over
- FeedbackDialog: issue/bug rapportage naar Open Feedback Studio API
- SettingsDialog: thema + taal instellingen met live preview
- 15+ keyboard shortcuts met i18n ShortcutHelp dialog

## Fasen — Afgerond

| Fase | Wat | Status |
|------|-----|--------|
| **1-7** | Core editor, sidebar, blocks, metadata, API, bijlagen, UX | ✅ |
| **P5** | Rich text (Tiptap WYSIWYG) | ✅ |
| **P6** | Visual polish (branding, iconen, toasts) | ✅ |
| **P7** | Tech debt (Vitest, ErrorBoundary, env vars) | ✅ |
| **P8** | Brand config (CSS custom properties) | ✅ |
| **F-FINAL** | renderer_v2 alignment | ✅ |
| **Chrome** | OpenAEC Design System (TitleBar, Ribbon, Backstage, StatusBar) | ✅ |
| **Auth** | OIDC/Authentik SSO, user/role management | ✅ |
| **Admin** | Admin panel, knop in Backstage + TitleBar dropdown | ✅ |
| **Save/Open** | Server vs lokaal keuze dialogs | ✅ |
| **Feedback** | FeedbackDialog naar Open Feedback Studio | ✅ |
| **i18n** | Nederlands + Engels, 5 namespaces | ✅ |

## Tests

- **Tests:** 25 passing (2 test files)
- **Conversion round-trip:** 6 tests
- **Store unit tests:** 19 tests
- **TypeScript:** 0 errors (`npx tsc -b`)

## API Contract

```
GET  /api/health              → { status, version }
GET  /api/templates           → { templates: [...] }
GET  /api/brands              → { brands: [...] }
GET  /api/stationery          → { brands: [...] }
GET  /api/templates/{n}/scaffold → { template, project, sections, cover, ... }
POST /api/validate            → { valid, errors }
POST /api/generate/v2         → application/pdf (binary)
POST /api/upload              → { path: string }
```
