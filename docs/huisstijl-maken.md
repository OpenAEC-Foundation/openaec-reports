# Een huisstijl maken

Een huisstijl is één map met alles wat een bedrijf naar buiten laat zien: logo's, kleuren, fonts, briefpapier,
rapportpagina's, facturen en mailhandtekeningen. Dezelfde map werkt in de **OpenAEC Report generator** (rapporten en
facturen als PDF) en in de **OpenAEC SuperCloud** (Beheer → Huisstijl: briefhoofd en facturen in ERPNext,
mailhandtekeningen voor alle medewerkers, de tools). Je maakt hem één keer en leest hem overal in.

## 1. Wat je nodig hebt

| Onderdeel | Wat | Formaat |
|---|---|---|
| Logo's | het gewone logo, een witte versie (voor donkere achtergronden), het beeldmerk en een favicon | SVG (liefst) en PNG |
| Kleuren | hoofdkleur, tweede kleur, tekstkleur, achtergrond; eventueel een accentkleur | hex `#RRGGBB` |
| Fonts | een font voor koppen en een voor tekst, met de **licentie** (naam en versie, bijv. SIL OFL 1.1) | TTF of OTF |
| Briefpapier | de vaste achtergrond per paginatype, zonder tekst die per document verschilt | PDF, A4 |
| Bedrijfsgegevens | naam, adres, kvk, btw, IBAN, telefoon, e-mail, website | tekst |
| Mailhandtekening | één of meer ontwerpen in HTML | HTML |
| Een voorbeeld | een bestaand rapport of een bestaande factuur om na te bouwen | PDF |

Tip: begin met wat er al is (het brandbook of een bestaande brief) en vul pas daarna aan.

## 2. De map

```
bureau/                         ← de naam van de map wordt de tenant
├── brand.yaml                  ← het hart van de huisstijl (zie 3)
├── logos/
│   ├── logo.svg                ← main
│   ├── logo-wit.svg            ← white
│   ├── beeldmerk.svg           ← symbol
│   └── favicon.png
├── fonts/
│   ├── Inter-Regular.ttf
│   └── SpaceGrotesk-Bold.ttf
├── stationery/                 ← briefpapier per paginatype (zie 4)
│   ├── brief.pdf
│   ├── factuur.pdf
│   ├── offerte.pdf
│   ├── cover.pdf
│   ├── content.pdf
│   └── backcover.pdf
├── templates/                  ← documentsoorten: rapport, factuur, ... (zie 05_YAML_GUIDE)
└── page_types/                 ← vaste paginalayouts (optioneel)
```

## 3. brand.yaml

```yaml
brand:
  name: "Bureau Jansen"
  slug: "bureau"
  tagline: "Bouwen met aandacht"

colors:
  primary: "#D97706"      # koppen, lijnen, knoppen, de kop van de factuur
  secondary: "#36363E"    # tweede kleur: subkoppen, de naam in het briefhoofd
  text: "#1F2937"         # tekst
  background: "#FFFFFF"   # achtergrond
  accent: "#EA580C"       # optioneel

font_files:               # pad in de map
  Inter-Regular: "fonts/Inter-Regular.ttf"
  SpaceGrotesk-Bold: "fonts/SpaceGrotesk-Bold.ttf"

fonts:                    # rol -> font
  heading: "SpaceGrotesk-Bold"
  body: "Inter-Regular"

logos:                    # variant -> bestand
  main: "logos/logo.svg"
  white: "logos/logo-wit.svg"
  symbol: "logos/beeldmerk.svg"
  favicon: "logos/favicon.png"

contact:                  # leeg laten mag: de SuperCloud vult het uit de bedrijfsgegevens
  name: "Bureau Jansen B.V."
  address: "Bouwstraat 1, 1234 AB Utrecht"
  website: "https://bureau.nl"

stationery:               # paginatype -> achtergrond
  brief:    { source: "stationery/brief.pdf" }
  factuur:  { source: "stationery/factuur.pdf" }
  offerte:  { source: "stationery/offerte.pdf" }
  cover:    { source: "stationery/cover.pdf" }
  content:
    source: "stationery/content.pdf"
    content_frame: { x_pt: 34, y_pt: 57, width_pt: 527, height_pt: 677 }   # waar de tekst mag staan
  backcover: { source: "stationery/backcover.pdf" }

email_signatures:         # mailhandtekeningen (HTML), zie 5
  - name: "Standaard"
    default: true
    template: |
      <table cellpadding="0" cellspacing="0" role="presentation" style="font-family:Inter,Arial,sans-serif;font-size:13px;color:#36363E">
        <tr>
          <td style="padding-right:12px"><img src="{logo_url}" alt="{handelsnaam}" width="48" height="48"></td>
          <td><strong>{naam}</strong><br>{functie}<br>
            <span style="color:#D97706">{handelsnaam}</span><br>
            <a href="tel:{telefoon}" style="color:#36363E">{telefoon}</a> ·
            <a href="mailto:{email}" style="color:#36363E">{email}</a><br>
            <a href="{website}" style="color:#D97706">{website}</a></td>
        </tr>
      </table>
  - name: "Kort"
    template: "<p><strong>{naam}</strong> · {handelsnaam} · {telefoon}</p>"
```

Alleen `brand` en `colors` zijn verplicht; de rest vul je aan wanneer je het hebt. Meer over `header`, `footer`,
`styles` en `pages` (rapporten tot op de millimeter): [05_YAML_GUIDE](architecture/05_YAML_GUIDE.md).

### Kleuren die werken

- Tekst op de achtergrond heeft minstens een contrast van **4,5 : 1**; de hoofdkleur op de achtergrond minstens
  **3 : 1**. De SuperCloud rekent het na en waarschuwt (Beheer → Huisstijl → Kleuren).
- Witte tekst op de hoofdkleur (de kop van een tabel op de factuur) moet ook leesbaar zijn; is de hoofdkleur heel
  licht, kies dan een donkerdere tint.

## 4. Briefpapier

Eén PDF per paginatype, exact A4 (210 × 297 mm; liggend 297 × 210 mm):

| Paginatype | Waarvoor |
|---|---|
| `brief` | brieven |
| `factuur` | facturen |
| `offerte` | offertes |
| `cover`, `content`, `backcover` | omslag, inhoudspagina en achterkant van een rapport |
| `colofon`, `toc`, `appendix_divider` | colofon, inhoudsopgave en bijlagescheiding |

Regels:

- Alleen wat op **elke** pagina van dat type staat: de balk met het logo, lijnen, vaste labels, een achtergrond.
- **Geen** tekst die per document verschilt (adres, datum, bedragen): die zet de generator erop.
- Exporteer als PDF zonder formulieren, scripts of bijlagen (de SuperCloud weigert die).

## 5. Mailhandtekeningen

Een handtekening is HTML met plaatshouders. De SuperCloud vult ze per medewerker in:

| Plaatshouder | Wordt |
|---|---|
| `{naam}` | de naam van de medewerker |
| `{functie}` | de functie (uit ERPNext, Medewerker) |
| `{telefoon}` | het telefoonnummer van het bedrijf |
| `{mobiel}` | het mobiele nummer van de medewerker |
| `{email}` | het e-mailadres van de medewerker |
| `{handelsnaam}`, `{website}`, `{adres}` | de bedrijfsgegevens |
| `{logo_url}` | het adres van het logo (openbaar, zodat het in elke mail laadt) |

Regels voor HTML in mail:

- Gebruik een `<table>` en **inline styles** (`style="…"`): mailprogramma's negeren `<style>`-blokken en moderne CSS.
- Geef afbeeldingen een vaste `width` en `height`, en houd het logo klein (± 48 px).
- Links alleen `https:`, `mailto:` en `tel:`. Scripts en andere links haalt de SuperCloud eruit.
- Maak een korte variant voor antwoorden in een lange mailwisseling.

## 6. Inlezen en gebruiken

### In de Report generator

Zet de map onder de tenants-map (`OPENAEC_TENANTS_ROOT`) en kies de tenant in de editor of in het JSON-veld `brand`.
Voor een nieuwe documentsoort (bijvoorbeeld een eigen factuur): [06_NIEUWE_TENANT_CHECKLIST](architecture/06_NIEUWE_TENANT_CHECKLIST.md).

### In de SuperCloud

1. Pak de map in als **zip** (de map zelf, met `brand.yaml` erin).
2. Beheer → **Huisstijl** → Report generator → **Zip inlezen**. Vul de licentie van de fonts in, anders komen de
   fontbestanden niet mee.
3. Controleer in **Merk** de logo's en de kleurwaarschuwingen, en in **Handtekeningen** het voorbeeld voor een paar
   medewerkers.
4. **In de mail van alle medewerkers zetten**: iedereen krijgt de standaardhandtekening met zijn eigen naam,
   functie en telefoon. Wie zelf een handtekening maakte, houdt die.
5. **Briefpapier en facturen**: met ERPNext maakt de SuperCloud het briefhoofd *Huisstijl &lt;bedrijf&gt;* en de
   opmaak *Factuur (huisstijl)* en *Offerte (huisstijl)*, in je kleuren en fonts, met je gegevens in de voet. Ze
   werken zich bij na elke wijziging van de huisstijl.

Een wijziging in de SuperCloud (een nieuwe kleur, een ander logo) neem je terug mee naar de Report generator met
**Downloaden als map**: dezelfde map, met `brand.yaml` en alle bestanden.

## 7. Checklist

- [ ] `brand.yaml` met naam en de vier kleuren (primary, secondary, text, background)
- [ ] Logo's: main, white, symbol en favicon, liefst als SVG
- [ ] Fonts voor heading en body, met licentie
- [ ] Briefpapier voor brief, factuur en offerte (en voor rapporten: cover, content, backcover)
- [ ] Een standaardmailhandtekening, en eventueel een korte
- [ ] Contrast gecontroleerd (geen waarschuwingen in Beheer → Huisstijl)
- [ ] Ingelezen in de SuperCloud; een factuur en een mail bekeken
