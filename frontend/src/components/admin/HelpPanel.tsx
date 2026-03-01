// Auto-generated — architecture documentation embedded as srcdoc
// Source: docs/architecture/architecture.html

const ARCHITECTURE_HTML = `<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenAEC Reports — Architecture</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root{--bg:#0c0e14;--bg-card:#13161f;--bg-hover:#1a1e2a;--border:#252a3a;--text:#c8cdd8;--text-dim:#6b7280;--text-bright:#e8ecf4;--blue:#006fab;--blue-dim:#004d7a;--brown:#94571e;--brown-dim:#6b3d14;--green:#2ecc71;--green-dim:#1a8a4a;--red:#e74c3c;--orange:#f39c12;--purple:#8b5cf6;--cyan:#22d3ee;--yellow:#fbbf24}
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;min-height:100vh}
  .header{background:linear-gradient(135deg,#0a0c12 0%,#141824 100%);border-bottom:1px solid var(--border);padding:28px 40px 20px}
  .header h1{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:var(--text-bright);letter-spacing:-0.5px}
  .header h1 span{color:var(--blue)}.header h1 .sep{color:var(--text-dim);margin:0 8px}
  .header p{font-size:13px;color:var(--text-dim);margin-top:4px}
  .tabs{display:flex;gap:2px;padding:0 40px;background:var(--bg);border-bottom:1px solid var(--border);overflow-x:auto}
  .tab{padding:12px 18px;font-size:12.5px;font-weight:600;color:var(--text-dim);cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;transition:all .15s;font-family:'JetBrains Mono',monospace}
  .tab:hover{color:var(--text);background:var(--bg-hover)}
  .tab.active{color:var(--blue);border-bottom-color:var(--blue)}
  .content{padding:32px 40px 60px;max-width:1400px}
  .panel{display:none}.panel.active{display:block}
  h2{font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700;color:var(--text-bright);margin:32px 0 16px;padding-bottom:8px;border-bottom:1px solid var(--border)}
  h2:first-child{margin-top:0}
  h2 .tag{font-size:10px;padding:2px 8px;border-radius:3px;margin-left:10px;vertical-align:middle;font-weight:600}
  .tag-blue{background:var(--blue-dim);color:#8ec8e8}.tag-green{background:var(--green-dim);color:#7eeaaa}.tag-purple{background:#4c2d8a;color:#c4a8ff}
  h3{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:600;color:var(--blue);margin:24px 0 10px}
  p{margin:8px 0;font-size:14px}
  .grid{display:grid;gap:16px}.grid-2{grid-template-columns:1fr 1fr}.grid-3{grid-template-columns:1fr 1fr 1fr}
  .card{background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:20px;transition:border-color .15s}
  .card:hover{border-color:var(--blue-dim)}
  .card-title{font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:var(--text-bright);margin-bottom:8px}
  pre,code{font-family:'JetBrains Mono',monospace;font-size:12.5px}
  pre{background:#0a0c12;border:1px solid var(--border);border-radius:6px;padding:16px 20px;overflow-x:auto;line-height:1.7;margin:12px 0}
  code{color:var(--cyan)}
  .c-blue{color:var(--blue)}.c-brown{color:var(--brown)}.c-green{color:var(--green)}.c-red{color:var(--red)}
  .c-orange{color:var(--orange)}.c-purple{color:var(--purple)}.c-dim{color:var(--text-dim)}
  .c-yellow{color:var(--yellow)}.c-bright{color:var(--text-bright)}
  table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0}
  th{text-align:left;font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;color:var(--blue);padding:10px 14px;border-bottom:2px solid var(--border);text-transform:uppercase;letter-spacing:.5px}
  td{padding:8px 14px;border-bottom:1px solid #1a1e28;vertical-align:top}
  tr:hover td{background:var(--bg-hover)}
  .flow{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:16px 0}
  .flow-node{padding:8px 16px;border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;border:1px solid}
  .flow-arrow{color:var(--text-dim);font-size:18px}
  .fn-input{background:#1a2332;border-color:var(--blue-dim);color:var(--blue)}
  .fn-process{background:#1f1a2e;border-color:#5b3d99;color:var(--purple)}
  .fn-output{background:#162218;border-color:var(--green-dim);color:var(--green)}
  .fn-config{background:#2a1f14;border-color:var(--brown-dim);color:var(--brown)}
  .step-list{counter-reset:step}
  .step{position:relative;padding:16px 20px 16px 56px;margin:8px 0;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;counter-increment:step}
  .step::before{content:counter(step);position:absolute;left:16px;top:16px;width:28px;height:28px;background:var(--blue-dim);color:var(--blue);border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700}
  .step-title{font-weight:700;color:var(--text-bright);font-size:13.5px;margin-bottom:4px}
  .step-body{font-size:13px;color:var(--text)}
  .step-body code{background:#0a0c12;padding:1px 6px;border-radius:3px;font-size:12px}
  .alert{padding:14px 18px;border-radius:6px;margin:16px 0;font-size:13px;border-left:3px solid}
  .alert-blue{background:#0d1a26;border-color:var(--blue)}.alert-orange{background:#1f1708;border-color:var(--orange)}
  .alert-red{background:#1f0d0d;border-color:var(--red)}.alert-green{background:#0d1f12;border-color:var(--green)}
  .badge{display:inline-block;font-size:10px;padding:2px 8px;border-radius:10px;font-weight:700;font-family:'JetBrains Mono',monospace;margin-right:4px}
  .badge-portrait{background:#1a2332;color:var(--blue)}.badge-landscape{background:#2a1f14;color:var(--orange)}
  .badge-special{background:#1f1a2e;color:var(--purple)}.badge-fixed{background:#162218;color:var(--green)}
  .tenant-card{background:linear-gradient(135deg,var(--bg-card) 0%,#181c28 100%);border:1px solid var(--border);border-radius:10px;padding:24px;position:relative;overflow:hidden}
  .tenant-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
  .tenant-card.symitech::before{background:linear-gradient(90deg,var(--blue),var(--brown))}
  .tenant-card.tbm::before{background:linear-gradient(90deg,#45233C,#55B49B)}
  @media(max-width:900px){.grid-2,.grid-3{grid-template-columns:1fr}.content{padding:20px}.tabs{padding:0 20px}.header{padding:20px}}
</style>
</head>
<body>

<div class="header">
  <h1><span>OpenAEC</span><span class="sep">/</span>Reports<span class="sep">—</span>Architecture</h1>
  <p>Multi-tenant PDF report engine · Template-driven · Pixel-precise · v3.0</p>
</div>

<div class="tabs" id="tabs">
  <div class="tab active" data-tab="overview">Overview</div>
  <div class="tab" data-tab="multitenant">Multi-Tenant</div>
  <div class="tab" data-tab="pipeline">Pipeline</div>
  <div class="tab" data-tab="pages">Pagina Types</div>
  <div class="tab" data-tab="mapping">JSON → PDF</div>
  <div class="tab" data-tab="newtenant">+ Nieuwe Tenant</div>
  <div class="tab" data-tab="rollen">Rolverdeling</div>
</div>

<div class="content">

<div class="panel active" id="overview">
<h2>Systeem Overzicht</h2>
<div class="flow">
  <div class="flow-node fn-input">JSON Data</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-process">data_transform.py</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-config">YAML Templates</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-process">TemplateEngine</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-output">PDF</div>
</div>
<div class="grid grid-3">
  <div class="card"><div class="card-title">📦 Backend</div><p>Python + FastAPI + PyMuPDF/ReportLab</p><p class="c-dim" style="font-size:12px">API endpoint: <code>/api/generate/template</code></p></div>
  <div class="card"><div class="card-title">🎨 Frontend</div><p>React + TypeScript + Zustand</p><p class="c-dim" style="font-size:12px">Admin panel voor template selectie + preview</p></div>
  <div class="card"><div class="card-title">🚀 Deploy</div><p>Docker op Hetzner VPS</p><p class="c-dim" style="font-size:12px">report.3bm.co.nl → reports.openaec.org</p></div>
</div>
<h2>Core Principes</h2>
<div class="grid grid-2">
  <div class="card"><div class="card-title">🔑 Geen hardcoded branding</div><p>Fontnamen, kleuren, posities — alles uit YAML configuratie. Nooit in Python code.</p></div>
  <div class="card"><div class="card-title">🏢 Tenant = bedrijf, Brand = huisstijl</div><p>Eén tenant kan meerdere brands hebben. Brand bepaalt visuele identiteit.</p></div>
  <div class="card"><div class="card-title">📐 Pixel-precise coördinaten</div><p>Alle posities geëxtraheerd uit referentie PDF's met PyMuPDF (pt → mm conversie).</p></div>
  <div class="card"><div class="card-title">📄 Stationery = achtergrond</div><p>Statische grafiek als PDF achtergrond. Engine rendert alleen variabele data.</p></div>
</div>
<h2>Rendering Engines</h2>
<table>
  <tr><th>Engine</th><th>Technologie</th><th>Gebruik</th><th>Status</th></tr>
  <tr><td><code class="c-dim">V1 — ReportLab</code></td><td>ReportLab Flowables</td><td>3BM constructieve rapporten</td><td><span class="badge" style="background:#2a1f14;color:#d4a574">legacy</span></td></tr>
  <tr><td><code class="c-dim">V2 — PyMuPDF</code></td><td>PyMuPDF renderer_v2</td><td>3BM pixel-perfect rapporten</td><td><span class="badge" style="background:#2a1f14;color:#d4a574">legacy</span></td></tr>
  <tr><td><code class="c-blue">V3 — TemplateEngine</code></td><td>ReportLab Canvas + YAML</td><td>Alle tenants, alle documenten</td><td><span class="badge" style="background:#162218;color:#7eeaaa">actief</span></td></tr>
</table>
</div>

<div class="panel" id="multitenant">
<h2>Multi-Tenant Architectuur</h2>
<div class="flow">
  <div class="flow-node fn-input">Tenant: symitech</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-config">brand.yaml + fonts/ + stationery/</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-config">templates/ + page_types/</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-output">Pixel-perfect PDF</div>
</div>
<h3>Directory Structuur</h3>
<pre>
<span class="c-blue">tenants/</span>
├── <span class="c-yellow">symitech/</span>                    <span class="c-dim"># Tenant 1</span>
│   ├── <span class="c-orange">brand.yaml</span>               <span class="c-dim"># Kleuren, fonts, styles</span>
│   ├── <span class="c-blue">fonts/</span>
│   ├── <span class="c-blue">stationery/</span>              <span class="c-dim"># Achtergrond PDF's</span>
│   ├── <span class="c-blue">templates/</span>               <span class="c-dim"># Documentstructuur</span>
│   └── <span class="c-blue">page_types/</span>              <span class="c-dim"># Pixel-exacte layouts</span>
├── <span class="c-yellow">3bm_cooperatie/</span>              <span class="c-dim"># Tenant 2</span>
└── <span class="c-purple">nieuwe_klant/</span>                <span class="c-dim"># Tenant N</span>
</pre>
<h3>Bestaande Tenants</h3>
<div class="grid grid-2">
  <div class="tenant-card symitech">
    <div class="card-title" style="color:var(--blue)">Symitech B.V.</div>
    <table>
      <tr><td class="c-dim" style="width:120px">Templates</td><td>BIC Factuur (6 pagina's)</td></tr>
      <tr><td class="c-dim">Fonts</td><td>Arial, Arial Bold</td></tr>
      <tr><td class="c-dim">Kleuren</td><td><span style="color:#006fab">■ #006fab</span> · <span style="color:#94571e">■ #94571e</span></td></tr>
    </table>
  </div>
  <div class="tenant-card tbm">
    <div class="card-title" style="color:#55B49B">3BM Coöperatie</div>
    <table>
      <tr><td class="c-dim" style="width:120px">Templates</td><td>Constructief rapport, Bouwkundig</td></tr>
      <tr><td class="c-dim">Fonts</td><td>Montserrat, Open Sans</td></tr>
      <tr><td class="c-dim">Kleuren</td><td><span style="color:#45233C">■ #45233C</span> · <span style="color:#55B49B">■ #55B49B</span></td></tr>
    </table>
  </div>
</div>
<h2>Tenant Isolatie</h2>
<div class="grid grid-3">
  <div class="card"><div class="card-title">🔒 Data Isolatie</div><p>Tenant resolved uit template naam prefix. API leest alleen eigen tenant directory.</p></div>
  <div class="card"><div class="card-title">🖋 Font Isolatie</div><p>Fonts per-tenant geregistreerd via <code>font_files</code> in brand.yaml.</p></div>
  <div class="card"><div class="card-title">📑 Stationery Isolatie</div><p>Engine zoekt alleen in <code>tenants/{tenant}/stationery/</code>.</p></div>
</div>
<h2>Tenant Resolution Flow</h2>
<pre>
<span class="c-dim">// API ontvangt:</span>
{ <span class="c-orange">"template"</span>: <span class="c-green">"symitech_bic_factuur"</span> }

<span class="c-dim">// _resolve_tenant_and_template():</span>
<span class="c-blue">1.</span> Split op eerste underscore → tenant=<span class="c-yellow">"symitech"</span>, template=<span class="c-green">"bic_factuur"</span>
<span class="c-blue">2.</span> Check: <span class="c-orange">tenants/symitech/</span> exists? ✓
<span class="c-blue">3.</span> Laad brand.yaml → registreer fonts → init TemplateEngine
<span class="c-blue">4.</span> data_transform(json) → engine.build() → PDF
</pre>
</div>

<div class="panel" id="pipeline">
<h2>Rendering Pipeline <span class="tag tag-green">V3</span></h2>
<div class="flow">
  <div class="flow-node fn-input">JSON (genest)</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-process">data_transform</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-input">Flat dict</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-process">TemplateEngine</div><div class="flow-arrow">→</div>
  <div class="flow-node fn-output">PDF</div>
</div>
<h3>Stap 1: Data Transform</h3>
<pre>
<span class="c-dim"># Input: geneste JSON</span>
{ <span class="c-orange">"sections"</span>: [{ <span class="c-orange">"content"</span>: [{ <span class="c-orange">"type"</span>: <span class="c-green">"bic_table"</span>, ... }] }] }

<span class="c-dim"># Output: flat dict</span>
{ <span class="c-orange">"bic"</span>: { <span class="c-orange">"kosten_conform"</span>: <span class="c-green">"€ 1.860,00"</span> },
  <span class="c-orange">"detail_items"</span>: [ { <span class="c-orange">"BIC Controle nummer"</span>: <span class="c-green">"BIC-2025-..."</span> } ] }
</pre>
<h3>Stap 2: YAML Bind Resolution</h3>
<pre>
<span class="c-dim"># YAML text_zone:</span>
- <span class="c-orange">bind</span>: <span class="c-green">bic.kosten_conform</span>    <span class="c-dim"># → "€ 1.860,00"</span>
  <span class="c-orange">x_mm</span>: <span class="c-cyan">148.1</span>
  <span class="c-orange">y_mm</span>: <span class="c-cyan">50.5</span>                    <span class="c-dim"># top-down mm</span>
  <span class="c-orange">font</span>: <span class="c-green">body</span>                    <span class="c-dim"># → brand.yaml</span>
  <span class="c-orange">color</span>: <span class="c-green">"text"</span>                 <span class="c-dim"># → brand.yaml</span>
</pre>
<h3>Stap 3: Pagina Opbouw (4 lagen)</h3>
<div class="grid grid-2">
  <div class="card"><div class="card-title">Layer 1: Stationery</div><p>Achtergrond PDF als onderlaag.</p></div>
  <div class="card"><div class="card-title">Layer 2: Line Zones</div><p>Decoratieve lijnen, kleur + dikte uit YAML.</p></div>
  <div class="card"><div class="card-title">Layer 3: Text Zones</div><p>Labels (static) + waarden (data-bound).</p></div>
  <div class="card"><div class="card-title">Layer 4: Tables</div><p>Kolom-tabellen met auto-paginering + truncation.</p></div>
</div>
</div>

<div class="panel" id="pages">
<h2>Symitech BIC Factuur — 6 Pagina's</h2>
<div class="grid grid-3">
  <div class="card"><div class="card-title"><span class="badge badge-special">special</span><span class="badge badge-portrait">portrait</span> Voorblad</div><p>Cover met logo, factuurkop, datum.</p></div>
  <div class="card"><div class="card-title"><span class="badge badge-fixed">fixed</span><span class="badge badge-portrait">portrait</span> Locatie</div><p>Opdrachtgever + locatie details.</p></div>
  <div class="card"><div class="card-title"><span class="badge badge-fixed">fixed</span><span class="badge badge-portrait">portrait</span> BIC Controles</div><p>Kosten-overzicht + samenvatting.</p></div>
  <div class="card"><div class="card-title"><span class="badge badge-fixed">fixed</span><span class="badge badge-landscape">landscape</span> Detail Weergave</div><p>7-koloms tabel, auto-paginering.</p></div>
  <div class="card"><div class="card-title"><span class="badge badge-fixed">fixed</span><span class="badge badge-landscape">landscape</span> Objecten</div><p>8-koloms tabel, tekst truncation.</p></div>
  <div class="card"><div class="card-title"><span class="badge badge-special">special</span><span class="badge badge-portrait">portrait</span> Achterblad</div><p>"Deze pagina is leeg gelaten"</p></div>
</div>
<h2>Template YAML Structuur</h2>
<pre>
<span class="c-orange">name</span>: <span class="c-green">symitech_bic_factuur</span>
<span class="c-orange">tenant</span>: <span class="c-green">symitech</span>
<span class="c-orange">pages</span>:
  - <span class="c-orange">type</span>: <span class="c-purple">special</span>  <span class="c-orange">page_type</span>: <span class="c-green">voorblad_bic</span>    <span class="c-orange">orientation</span>: <span class="c-green">portrait</span>
  - <span class="c-orange">type</span>: <span class="c-green">fixed</span>    <span class="c-orange">page_type</span>: <span class="c-green">locatie</span>         <span class="c-orange">orientation</span>: <span class="c-green">portrait</span>
  - <span class="c-orange">type</span>: <span class="c-green">fixed</span>    <span class="c-orange">page_type</span>: <span class="c-green">bic_controles</span>   <span class="c-orange">orientation</span>: <span class="c-green">portrait</span>
  - <span class="c-orange">type</span>: <span class="c-green">fixed</span>    <span class="c-orange">page_type</span>: <span class="c-green">detail_weergave</span> <span class="c-orange">orientation</span>: <span class="c-green">landscape</span>  <span class="c-orange">repeat</span>: <span class="c-green">auto</span>
  - <span class="c-orange">type</span>: <span class="c-green">fixed</span>    <span class="c-orange">page_type</span>: <span class="c-green">objecten</span>        <span class="c-orange">orientation</span>: <span class="c-green">landscape</span>  <span class="c-orange">repeat</span>: <span class="c-green">auto</span>
  - <span class="c-orange">type</span>: <span class="c-purple">special</span>  <span class="c-orange">page_type</span>: <span class="c-green">achterblad</span>      <span class="c-orange">orientation</span>: <span class="c-green">portrait</span>
</pre>
</div>

<div class="panel" id="mapping">
<h2>JSON → Transform → YAML Bind → PDF</h2>
<h3>BIC Controles</h3>
<table>
  <tr><th>Transform key</th><th>YAML bind</th><th>y (mm)</th></tr>
  <tr><td>bic.aantal_conform</td><td>bic.aantal_conform</td><td>46.5</td></tr>
  <tr><td>bic.kosten_conform</td><td>bic.kosten_conform</td><td>50.5</td></tr>
  <tr><td>bic.hydro_aantal_conform</td><td>bic.hydro_aantal_conform</td><td>58.6</td></tr>
  <tr><td>bic.reiskosten_conform</td><td>bic.reiskosten_conform</td><td>70.8</td></tr>
  <tr><td>bic.subtotaal_conform</td><td>bic.subtotaal_conform</td><td>83.8</td></tr>
  <tr><td>samenvatting.totaal_conform</td><td>samenvatting.totaal_conform</td><td>180.2</td></tr>
</table>
<div class="alert alert-blue"><strong>Kolom layout:</strong> Labels x=19.5mm · Conform x=148.1mm · Werkelijk x=190.6mm</div>
<h3>Detail Weergave (tabel)</h3>
<table>
  <tr><th>YAML field</th><th>Breedte</th><th>Align</th></tr>
  <tr><td>BIC Controle nummer</td><td>42mm</td><td>left</td></tr>
  <tr><td>Type</td><td>38mm</td><td>left</td></tr>
  <tr><td>Datum</td><td>17mm</td><td>left</td></tr>
  <tr><td>BIC controle</td><td>22mm</td><td>center</td></tr>
  <tr><td>Int. inspectie</td><td>24mm</td><td>center</td></tr>
  <tr><td>Reiniging</td><td>18mm</td><td>center</td></tr>
  <tr><td>Additioneel</td><td>100mm</td><td>left</td></tr>
</table>
<div class="alert alert-orange"><strong>Kritiek:</strong> YAML field names moeten EXACT matchen met JSON headers (inclusief spaties en hoofdletters).</div>
<h3>Styling Hiërarchie</h3>
<table>
  <tr><th>Element</th><th>Font</th><th>Color</th></tr>
  <tr><td>Labels (links)</td><td>heading (bold)</td><td style="color:#94571e">secondary #94571e</td></tr>
  <tr><td>Waarden (rechts)</td><td>body (regular)</td><td>text #000000</td></tr>
  <tr><td>Totaal waarden</td><td>heading (bold)</td><td style="color:#006fab">primary #006fab</td></tr>
  <tr><td>Tabel headers</td><td>heading (bold)</td><td style="color:#94571e">secondary</td></tr>
  <tr><td>Tabel data</td><td>body (regular)</td><td>text #000000</td></tr>
  <tr><td>Footer</td><td>heading (bold)</td><td>white #ffffff</td></tr>
</table>
</div>

<div class="panel" id="newtenant">
<h2>Nieuwe Tenant Toevoegen <span class="tag tag-purple">pixel-precise guide</span></h2>
<div class="alert alert-blue"><strong>Doorlooptijd:</strong> 2-4 uur voor een standaard document (4-8 pagina's).</div>
<h3>Benodigdheden</h3>
<div class="grid grid-3">
  <div class="card"><div class="card-title">📋 Brand Guidelines</div><p>Logo's, kleuren (hex), fonts (.ttf)</p></div>
  <div class="card"><div class="card-title">📄 Referentie PDF</div><p>Bestaand rapport als voorbeeld</p></div>
  <div class="card"><div class="card-title">📊 Voorbeeld Data</div><p>Ingevuld voorbeeld voor test JSON</p></div>
</div>
<h2>Stap-voor-stap</h2>
<div class="step-list">
  <div class="step"><div class="step-title">Directory structuur aanmaken</div><div class="step-body"><pre style="margin:8px 0">tenants/{tenant}/
├── brand.yaml · fonts/ · stationery/ · templates/ · page_types/</pre><p>Naam = lowercase, underscores. Bijv: <code>acme_corp</code></p></div></div>
  <div class="step"><div class="step-title">Referentie PDF analyseren met PyMuPDF</div><div class="step-body"><p>Extract tekst met posities, fonts, kleuren. Noteer <code>x0</code>, <code>y0</code> (pt, top-down).</p></div></div>
  <div class="step"><div class="step-title">Coördinaten converteren: pt → mm</div><div class="step-body"><pre style="margin:8px 0">mm = pt × 0.352778
<span class="c-dim">// +1.0mm offset op y_mm (baseline correctie)</span></pre></div></div>
  <div class="step"><div class="step-title">Stationery PDF's maken</div><div class="step-body"><p>Alleen statische elementen (logo, kleurbalken). Exact A4 formaat. Geen variabele data.</p></div></div>
  <div class="step"><div class="step-title">brand.yaml schrijven</div><div class="step-body"><p>colors, font_files, fonts mapping. Zie bestaande tenants als voorbeeld.</p></div></div>
  <div class="step"><div class="step-title">Page type YAML's schrijven</div><div class="step-body"><p>Eén YAML per pagina-layout. text_zones, line_zones, table configuratie.</p></div></div>
  <div class="step"><div class="step-title">Tabel configuratie</div><div class="step-body"><p>data_bind, columns, field names EXACT match met JSON keys.</p></div></div>
  <div class="step"><div class="step-title">Template YAML schrijven</div><div class="step-body"><p>Naam = <code>{tenant}_{type}</code>. Pagina volgorde + orientatie.</p></div></div>
  <div class="step"><div class="step-title">data_transform uitbreiden (indien nodig)</div><div class="step-body"><p>Alleen als JSON structuur afwijkt van bestaand formaat.</p></div></div>
  <div class="step"><div class="step-title">Test JSON + lokaal genereren</div><div class="step-body"><p>Vergelijk visueel met referentie PDF.</p></div></div>
  <div class="step"><div class="step-title">Fine-tuning + Deploy</div><div class="step-body"><pre style="margin:8px 0">git pull &amp;&amp; docker compose build --no-cache &amp;&amp; docker compose up -d</pre></div></div>
</div>
<h2>Troubleshooting</h2>
<table>
  <tr><th>Probleem</th><th>Oorzaak</th><th>Oplossing</th></tr>
  <tr><td>Lege pagina's</td><td>Fonts niet embedded</td><td>Check font_files in brand.yaml</td></tr>
  <tr><td>Tekst te hoog/laag</td><td>Baseline offset</td><td>+/- 1.0mm op y_mm</td></tr>
  <tr><td>Geen stationery</td><td>Bestandsnaam mismatch</td><td>Check stationery veld</td></tr>
  <tr><td>Template not found</td><td>Naam mist prefix</td><td>{tenant}_{type} in naam</td></tr>
  <tr><td>Tabel data leeg</td><td>Field name mismatch</td><td>YAML field = exact JSON key</td></tr>
  <tr><td>Tekst overlapt</td><td>Kolom te smal</td><td>Vergroot width_mm</td></tr>
  <tr><td>Verkeerde kleuren</td><td>Color ref onbekend</td><td>Gebruik primary/secondary/text</td></tr>
</table>
</div>

<div class="panel" id="rollen">
<h2>Rolverdeling: Jochem × Claude</h2>
<div class="grid grid-2">
  <div class="card" style="border-color:var(--blue-dim)">
    <div class="card-title" style="color:var(--blue)">👤 Jochem (Mens)</div>
    <table>
      <tr><td>JSON data per project</td></tr><tr><td>Referentie PDF's aanleveren</td></tr>
      <tr><td>Stationery PDF's maken</td></tr><tr><td>Brand guidelines doorgeven</td></tr>
      <tr><td>Visuele QA</td></tr><tr><td>Server deployment</td></tr>
    </table>
  </div>
  <div class="card" style="border-color:var(--purple)">
    <div class="card-title" style="color:var(--purple)">🤖 Claude (AI)</div>
    <table>
      <tr><td>Page type + Template YAML's</td></tr><tr><td>brand.yaml configureren</td></tr>
      <tr><td>data_transform.py updates</td></tr><tr><td>template_engine.py features</td></tr>
      <tr><td>Bug fixes + optimalisaties</td></tr><tr><td>Git commit + push</td></tr>
    </table>
  </div>
</div>
<h2>Roadmap</h2>
<table>
  <tr><th>ID</th><th>Taak</th><th>Status</th></tr>
  <tr><td>T3</td><td>3BM TemplateEngine migratie</td><td>🟡 Open</td></tr>
  <tr><td>T4</td><td>OpenAEC Rebranding</td><td>🟡 Open</td></tr>
  <tr><td>T5</td><td>YAML Editor in Admin Panel</td><td>🟡 Open</td></tr>
</table>
</div>

</div>

<script>
document.querySelectorAll('.tab').forEach(function(tab){
  tab.addEventListener('click',function(){
    document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});
    document.querySelectorAll('.panel').forEach(function(p){p.classList.remove('active')});
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  });
});
</script>
</body>
</html>`;

export function HelpPanel() {
  return (
    <div
      className="rounded-lg border border-gray-200 overflow-hidden"
      style={{ height: "calc(100vh - 200px)" }}
    >
      <iframe
        srcDoc={ARCHITECTURE_HTML}
        title="Architecture & Tenant Guide"
        className="w-full h-full border-0"
        sandbox="allow-scripts"
      />
    </div>
  );
}
