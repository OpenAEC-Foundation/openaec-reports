import { useState } from "react";

type SectionKey = "overview" | "tenants" | "users" | "templates" | "brand" | "api";

interface HelpSection {
  key: SectionKey;
  title: string;
  content: React.ReactNode;
}

const SECTIONS: HelpSection[] = [
  {
    key: "overview",
    title: "Overzicht",
    content: (
      <>
        <p>
          Het beheerpaneel biedt toegang tot alle configuratie van het OpenAEC
          Reports platform. Hieronder vind je uitleg per onderdeel.
        </p>
        <h4 className="mt-4 font-semibold text-gray-900">Architectuur</h4>
        <p className="mt-1">
          Het platform bestaat uit drie lagen:
        </p>
        <ul className="mt-2 list-disc pl-5 space-y-1">
          <li>
            <strong>Library</strong> (openaec-reports) — Python package dat PDF
            rapporten genereert op basis van JSON input en YAML templates.
          </li>
          <li>
            <strong>API Server</strong> — FastAPI backend die JSON ontvangt en
            PDF&apos;s retourneert. Biedt ook tenant/gebruikersbeheer.
          </li>
          <li>
            <strong>Frontend</strong> — Deze web-UI. Visuele editor die JSON
            produceert conform het rapport-schema.
          </li>
        </ul>
        <h4 className="mt-4 font-semibold text-gray-900">Multi-tenant</h4>
        <p className="mt-1">
          Het systeem ondersteunt meerdere organisaties (tenants). Elke tenant
          heeft eigen templates, brand-configuratie, stationery, logo&apos;s en
          fonts. De engine is generiek, de look &amp; feel per tenant
          configureerbaar.
        </p>
      </>
    ),
  },
  {
    key: "tenants",
    title: "Tenants",
    content: (
      <>
        <p>
          Een <strong>tenant</strong> is een organisatie met eigen huisstijl en
          templates. Elke tenant heeft een unieke slug (bijv.{" "}
          <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
            mijn_organisatie
          </code>
          ).
        </p>
        <h4 className="mt-4 font-semibold text-gray-900">Tenant aanmaken</h4>
        <ol className="mt-2 list-decimal pl-5 space-y-1">
          <li>Ga naar het tabblad <strong>Tenants</strong>.</li>
          <li>
            Klik op <strong>Nieuwe tenant</strong> en vul een naam en slug in.
          </li>
          <li>
            De slug wordt gebruikt als mapnaam en moet uniek zijn (lowercase,
            underscores toegestaan).
          </li>
        </ol>
        <h4 className="mt-4 font-semibold text-gray-900">Tenant structuur</h4>
        <p className="mt-1">Na aanmaken bevat een tenant-map:</p>
        <ul className="mt-2 list-disc pl-5 space-y-1">
          <li>
            <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
              brand.yaml
            </code>{" "}
            — Huisstijl configuratie (kleuren, fonts, logo-paden)
          </li>
          <li>
            <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
              templates/
            </code>{" "}
            — YAML rapport-templates
          </li>
          <li>
            <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
              stationery/
            </code>{" "}
            — PDF/PNG achtergrondpagina&apos;s
          </li>
          <li>
            <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
              logos/
            </code>{" "}
            — Logo&apos;s (SVG, PNG)
          </li>
          <li>
            <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
              fonts/
            </code>{" "}
            — Lettertypen (TTF, OTF)
          </li>
        </ul>
      </>
    ),
  },
  {
    key: "users",
    title: "Gebruikers",
    content: (
      <>
        <p>
          Gebruikersbeheer regelt wie toegang heeft tot het platform en met welke
          rechten.
        </p>
        <h4 className="mt-4 font-semibold text-gray-900">Rollen</h4>
        <ul className="mt-2 list-disc pl-5 space-y-1">
          <li>
            <strong>admin</strong> — Volledige toegang tot alle beheerfuncties,
            tenants en gebruikers.
          </li>
          <li>
            <strong>user</strong> — Kan rapporten aanmaken en genereren, maar
            geen beheertaken uitvoeren.
          </li>
        </ul>
        <h4 className="mt-4 font-semibold text-gray-900">Acties</h4>
        <ul className="mt-2 list-disc pl-5 space-y-1">
          <li>
            <strong>Aanmaken</strong> — Vul gebruikersnaam, wachtwoord, rol en
            optioneel een tenant-koppeling in.
          </li>
          <li>
            <strong>Wachtwoord resetten</strong> — Stel een nieuw wachtwoord in
            voor een bestaande gebruiker.
          </li>
          <li>
            <strong>Verwijderen</strong> — Verwijdert het account permanent.
          </li>
        </ul>
      </>
    ),
  },
  {
    key: "templates",
    title: "Templates",
    content: (
      <>
        <p>
          Templates zijn YAML-bestanden die de structuur en opmaak van een
          rapporttype defini&euml;ren. Elke tenant kan eigen templates hebben.
        </p>
        <h4 className="mt-4 font-semibold text-gray-900">Template structuur</h4>
        <p className="mt-1">Een template YAML bevat:</p>
        <ul className="mt-2 list-disc pl-5 space-y-1">
          <li>
            <strong>Metadata</strong> — Naam, beschrijving, tenant, papierformaat.
          </li>
          <li>
            <strong>Page types</strong> — Definities van paginatypen (cover,
            content, colofon) met stationery-referenties.
          </li>
          <li>
            <strong>Content styles</strong> — Typografie, kleuren, spacing per
            bloktype.
          </li>
          <li>
            <strong>Secties</strong> — Voorgedefinieerde secties met
            placeholder-content.
          </li>
        </ul>
        <h4 className="mt-4 font-semibold text-gray-900">Template uploaden</h4>
        <ol className="mt-2 list-decimal pl-5 space-y-1">
          <li>Selecteer een tenant in het Tenants-tabblad.</li>
          <li>
            Ga naar <strong>Templates</strong> en klik op{" "}
            <strong>Upload template</strong>.
          </li>
          <li>
            Selecteer een{" "}
            <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
              .yaml
            </code>{" "}
            bestand.
          </li>
        </ol>
        <h4 className="mt-4 font-semibold text-gray-900">Content block types</h4>
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left">
                <th className="py-1.5 pr-4 font-medium text-gray-900">Type</th>
                <th className="py-1.5 font-medium text-gray-900">Beschrijving</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">paragraph</code>
                </td>
                <td>Tekst met opmaak (bold, italic, sub, sup)</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">calculation</code>
                </td>
                <td>Berekening met formule, eenheid en resultaat</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">check</code>
                </td>
                <td>Unity check met required/calculated waarden</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">table</code>
                </td>
                <td>Tabel met headers en rijen</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">image</code>
                </td>
                <td>Afbeelding (pad, URL of base64)</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">map</code>
                </td>
                <td>Kadasterkaart via PDOK WMS</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">bullet_list</code>
                </td>
                <td>Opsomming met bullet points</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">heading_2</code>
                </td>
                <td>Subkop binnen een sectie</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">spacer</code>
                </td>
                <td>Verticale witruimte (in mm)</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="text-purple-700">page_break</code>
                </td>
                <td>Pagina-einde forceren</td>
              </tr>
            </tbody>
          </table>
        </div>
      </>
    ),
  },
  {
    key: "brand",
    title: "Brand & Huisstijl",
    content: (
      <>
        <p>
          De Brand-configuratie bepaalt de visuele identiteit van een tenant:
          kleuren, lettertypen, logo&apos;s en achtergrondpagina&apos;s
          (stationery).
        </p>
        <h4 className="mt-4 font-semibold text-gray-900">brand.yaml</h4>
        <p className="mt-1">Het centrale configuratiebestand bevat:</p>
        <ul className="mt-2 list-disc pl-5 space-y-1">
          <li>
            <strong>Kleuren</strong> — Primary, secondary, text, accent kleuren
            (hex).
          </li>
          <li>
            <strong>Fonts</strong> — Font-families met paden naar TTF/OTF
            bestanden.
          </li>
          <li>
            <strong>Logo&apos;s</strong> — Paden naar logo-varianten (kleur, wit,
            compact).
          </li>
          <li>
            <strong>Stationery</strong> — Referenties naar PDF/PNG
            achtergrondpagina&apos;s per paginatype.
          </li>
        </ul>
        <h4 className="mt-4 font-semibold text-gray-900">Brand Extraction Wizard</h4>
        <p className="mt-1">
          Automatisch een brand-configuratie opbouwen vanuit een bestaande PDF:
        </p>
        <ol className="mt-2 list-decimal pl-5 space-y-1">
          <li>
            Upload een referentie-PDF (bijv. een bestaand rapport in de gewenste
            huisstijl).
          </li>
          <li>
            De extractor analyseert kleuren, lettertypen en layout.
          </li>
          <li>Review en pas de ge&euml;xtraheerde waarden aan.</li>
          <li>
            Genereer een prompt-package voor verdere configuratie.
          </li>
          <li>Merge de resultaten naar de tenant brand.yaml.</li>
        </ol>
        <h4 className="mt-4 font-semibold text-gray-900">Assets uploaden</h4>
        <ul className="mt-2 list-disc pl-5 space-y-1">
          <li>
            <strong>Stationery</strong> — PDF of PNG bestanden voor
            pagina-achtergronden.
          </li>
          <li>
            <strong>Logo&apos;s</strong> — SVG (voorkeur) of PNG, in
            verschillende varianten.
          </li>
          <li>
            <strong>Fonts</strong> — TTF of OTF bestanden. Zorg dat de
            bestandsnamen overeenkomen met de referenties in brand.yaml.
          </li>
        </ul>
      </>
    ),
  },
  {
    key: "api",
    title: "API & Integratie",
    content: (
      <>
        <p>
          Het platform biedt een REST API voor integratie met externe systemen
          (bijv. pyRevit, scripts, CI/CD).
        </p>
        <h4 className="mt-4 font-semibold text-gray-900">Endpoints</h4>
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left">
                <th className="py-1.5 pr-4 font-medium text-gray-900">
                  Methode
                </th>
                <th className="py-1.5 pr-4 font-medium text-gray-900">Pad</th>
                <th className="py-1.5 font-medium text-gray-900">
                  Beschrijving
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="rounded bg-green-50 px-1.5 py-0.5 text-green-700">
                    GET
                  </code>
                </td>
                <td className="py-1.5 pr-4 font-mono text-sm">/api/health</td>
                <td>Status en versie</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="rounded bg-green-50 px-1.5 py-0.5 text-green-700">
                    GET
                  </code>
                </td>
                <td className="py-1.5 pr-4 font-mono text-sm">
                  /api/templates
                </td>
                <td>Beschikbare templates</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="rounded bg-green-50 px-1.5 py-0.5 text-green-700">
                    GET
                  </code>
                </td>
                <td className="py-1.5 pr-4 font-mono text-sm">/api/brands</td>
                <td>Beschikbare brands</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="rounded bg-green-50 px-1.5 py-0.5 text-green-700">
                    GET
                  </code>
                </td>
                <td className="py-1.5 pr-4 font-mono text-sm">
                  /api/templates/&#123;name&#125;/scaffold
                </td>
                <td>Leeg rapport-JSON als startpunt</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="rounded bg-blue-50 px-1.5 py-0.5 text-blue-700">
                    POST
                  </code>
                </td>
                <td className="py-1.5 pr-4 font-mono text-sm">
                  /api/validate
                </td>
                <td>Rapport-JSON valideren</td>
              </tr>
              <tr>
                <td className="py-1.5 pr-4">
                  <code className="rounded bg-blue-50 px-1.5 py-0.5 text-blue-700">
                    POST
                  </code>
                </td>
                <td className="py-1.5 pr-4 font-mono text-sm">
                  /api/generate
                </td>
                <td>PDF genereren uit JSON</td>
              </tr>
            </tbody>
          </table>
        </div>
        <h4 className="mt-4 font-semibold text-gray-900">Authenticatie</h4>
        <p className="mt-1">
          De API gebruikt JWT-tokens. Log in via{" "}
          <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
            POST /api/auth/login
          </code>{" "}
          om een token te ontvangen. Stuur het token mee als{" "}
          <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
            Authorization: Bearer &lt;token&gt;
          </code>{" "}
          header bij alle beveiligde endpoints.
        </p>
        <h4 className="mt-4 font-semibold text-gray-900">
          JSON Schema
        </h4>
        <p className="mt-1">
          Het volledige datamodel staat in{" "}
          <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
            schemas/report.schema.json
          </code>
          . Dit is het contract tussen frontend, API en library. Gebruik{" "}
          <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">
            GET /api/templates/&#123;name&#125;/scaffold
          </code>{" "}
          om een geldig startpunt te krijgen.
        </p>
      </>
    ),
  },
];

export function HelpPanel() {
  const [activeSection, setActiveSection] = useState<SectionKey>("overview");

  // SECTIONS is nooit leeg, activeSection is altijd een geldige key
  const current = SECTIONS.find((s) => s.key === activeSection)!;

  return (
    <div className="flex gap-6">
      {/* Sidebar navigatie */}
      <nav className="w-48 shrink-0">
        <ul className="space-y-1">
          {SECTIONS.map((section) => (
            <li key={section.key}>
              <button
                onClick={() => setActiveSection(section.key)}
                className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                  activeSection === section.key
                    ? "bg-purple-50 font-medium text-purple-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                {section.title}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="text-lg font-semibold text-gray-900">
            {current.title}
          </h3>
          <div className="mt-3 text-sm leading-relaxed text-gray-600">
            {current.content}
          </div>
        </div>
      </div>
    </div>
  );
}
