//! Special pages — cover, colofon, TOC, and backcover.
//!
//! Builds DrawList-based RawPages for non-content pages.
//! These are pre-rendered canvases inserted before/after the main content.

use openaec_layout::{Color, DrawList, Mm, Pt, RawPage, A4};

use crate::brand::BrandConfig;
use crate::schema::ReportData;

// ── Color helpers ────────────────────────────────────────────────────

/// Resolve the primary brand color, falling back to OpenAEC default.
fn brand_primary(brand: &BrandConfig) -> Color {
    brand
        .resolve_color("$primary")
        .and_then(Color::from_hex)
        .unwrap_or(Color::rgb(0x40, 0x12, 0x4A))
}

/// Resolve the secondary brand color, falling back to OpenAEC default.
fn brand_secondary(brand: &BrandConfig) -> Color {
    brand
        .resolve_color("$secondary")
        .and_then(Color::from_hex)
        .unwrap_or(Color::rgb(0x38, 0xBD, 0xA0))
}

/// Resolve the text brand color, falling back to OpenAEC default.
fn brand_text(brand: &BrandConfig) -> Color {
    brand
        .resolve_color("$text")
        .and_then(Color::from_hex)
        .unwrap_or(Color::rgb(0x45, 0x24, 0x3D))
}

// ── Cover page ───────────────────────────────────────────────────────

/// Build a cover page with brand colors.
///
/// Layout (top-left origin, Y downward):
/// - Brand name at top-left (x=55, y=50) in primary color
/// - Bottom 75% of page filled with primary color
/// - Project title as large white text near bottom-left (x=55, y=750)
/// - Subtitle (if present) in turquoise below the title
pub fn build_cover_page(data: &ReportData, brand: &BrandConfig) -> RawPage {
    let mut dl = DrawList::new();
    let primary = brand_primary(brand);
    let secondary = brand_secondary(brand);

    let page_w = A4.width;
    let page_h = A4.height;

    // Background rectangle: bottom 75% of the page
    // Top-left origin: starts at 25% from top, extends to bottom
    let bg_y = Pt(page_h.0 * 0.25);
    let bg_h = Pt(page_h.0 * 0.75);
    dl.set_fill_color(primary);
    dl.draw_rect(Pt(0.0), bg_y, page_w, bg_h, true, false);

    // Brand name at top-left (in the white area)
    dl.set_fill_color(primary);
    dl.set_font("LiberationSans-Bold", Pt(14.0));
    dl.draw_text(Pt::from(Mm(55.0)), Pt::from(Mm(50.0)), &brand.brand.name);

    // Tagline below brand name (if present)
    if let Some(ref tagline) = brand.brand.tagline {
        dl.set_fill_color(secondary);
        dl.set_font("LiberationSans-Regular", Pt(10.0));
        dl.draw_text(Pt::from(Mm(55.0)), Pt::from(Mm(58.0)), tagline);
    }

    // Project title: large white text in the colored area
    dl.set_fill_color(Color::WHITE);
    dl.set_font("LiberationSans-Bold", Pt(18.0));
    dl.draw_text(Pt::from(Mm(55.0)), Pt::from(Mm(750.0 / 2.8346)), &data.project);

    // Subtitle (if present) in turquoise below the title
    if let Some(ref cover) = data.cover {
        if let Some(ref subtitle) = cover.subtitle {
            dl.set_fill_color(secondary);
            dl.set_font("LiberationSans-Regular", Pt(12.0));
            dl.draw_text(
                Pt::from(Mm(55.0)),
                Pt::from(Mm(750.0 / 2.8346 + 8.0)),
                subtitle,
            );
        }
    }

    // Project metadata in white, bottom area
    let mut meta_y = Pt::from(Mm(750.0 / 2.8346 + 20.0));
    dl.set_fill_color(Color::WHITE);
    dl.set_font("LiberationSans-Regular", Pt(9.0));

    if let Some(ref pn) = data.project_number {
        dl.draw_text(Pt::from(Mm(55.0)), meta_y, &format!("Projectnummer: {}", pn));
        meta_y = Pt(meta_y.0 + Pt::from(Mm(5.0)).0);
    }
    if let Some(ref client) = data.client {
        dl.draw_text(Pt::from(Mm(55.0)), meta_y, &format!("Opdrachtgever: {}", client));
        meta_y = Pt(meta_y.0 + Pt::from(Mm(5.0)).0);
    }
    if let Some(ref date) = data.date {
        dl.draw_text(Pt::from(Mm(55.0)), meta_y, &format!("Datum: {}", date));
    }

    RawPage {
        page_size: A4,
        draw_list: dl,
    }
}

// ── Colofon page ─────────────────────────────────────────────────────

/// Build a colofon (document info) page.
///
/// Layout:
/// - "Colofon" title at top (x=70, y=60) in primary color, 18pt
/// - Two-column layout: labels at x=70, values at x=230
/// - Horizontal separator lines between groups
/// - Revision history table (if present)
/// - Disclaimer text at bottom (if present)
pub fn build_colofon_page(data: &ReportData, brand: &BrandConfig) -> RawPage {
    let mut dl = DrawList::new();
    let primary = brand_primary(brand);
    let text_color = brand_text(brand);

    let label_x = Pt::from(Mm(25.0));
    let value_x = Pt::from(Mm(80.0));
    let line_start_x = label_x;
    let line_end_x = Pt::from(Mm(185.0));
    let row_height = Pt::from(Mm(7.0));

    // Title
    dl.set_fill_color(primary);
    dl.set_font("LiberationSans-Bold", Pt(18.0));
    dl.draw_text(label_x, Pt::from(Mm(25.0)), "Colofon");

    let mut cursor_y = Pt::from(Mm(40.0));

    // Helper closure-like: draw a label-value row
    let draw_row = |dl: &mut DrawList, y: Pt, label: &str, value: &str| {
        dl.set_fill_color(text_color);
        dl.set_font("LiberationSans-Bold", Pt(9.0));
        dl.draw_text(label_x, y, label);
        dl.set_font("LiberationSans-Regular", Pt(9.0));
        dl.draw_text(value_x, y, value);
    };

    // Project info
    draw_row(&mut dl, cursor_y, "Project", &data.project);
    cursor_y = Pt(cursor_y.0 + row_height.0);

    if let Some(ref pn) = data.project_number {
        draw_row(&mut dl, cursor_y, "Projectnummer", pn);
        cursor_y = Pt(cursor_y.0 + row_height.0);
    }

    if let Some(ref client) = data.client {
        draw_row(&mut dl, cursor_y, "Opdrachtgever", client);
        cursor_y = Pt(cursor_y.0 + row_height.0);
    }

    // Separator line
    cursor_y = Pt(cursor_y.0 + Pt::from(Mm(2.0)).0);
    dl.set_stroke_color(Color::LIGHT_GREY);
    dl.set_line_width(Pt(0.5));
    dl.draw_line(line_start_x, cursor_y, line_end_x, cursor_y);
    cursor_y = Pt(cursor_y.0 + Pt::from(Mm(4.0)).0);

    // Colofon-specific fields
    if let Some(ref colofon) = data.colofon {
        if let Some(ref name) = colofon.opdrachtgever_naam {
            draw_row(&mut dl, cursor_y, "Opdrachtgever", name);
            cursor_y = Pt(cursor_y.0 + row_height.0);
        }

        if let Some(ref bedrijf) = colofon.adviseur_bedrijf {
            draw_row(&mut dl, cursor_y, "Adviseur", bedrijf);
            cursor_y = Pt(cursor_y.0 + row_height.0);
        }

        if let Some(ref naam) = colofon.adviseur_naam {
            draw_row(&mut dl, cursor_y, "Opgesteld door", naam);
            cursor_y = Pt(cursor_y.0 + row_height.0);
        }

        if let Some(ref datum) = colofon.datum {
            draw_row(&mut dl, cursor_y, "Datum", datum);
            cursor_y = Pt(cursor_y.0 + row_height.0);
        } else if let Some(ref date) = data.date {
            draw_row(&mut dl, cursor_y, "Datum", date);
            cursor_y = Pt(cursor_y.0 + row_height.0);
        }

        if let Some(ref status) = colofon.status_colofon {
            draw_row(&mut dl, cursor_y, "Status", status);
            cursor_y = Pt(cursor_y.0 + row_height.0);
        }

        if let Some(ref kenmerk) = colofon.kenmerk {
            draw_row(&mut dl, cursor_y, "Kenmerk", kenmerk);
            cursor_y = Pt(cursor_y.0 + row_height.0);
        }

        // Versie
        draw_row(&mut dl, cursor_y, "Versie", &data.version);
        cursor_y = Pt(cursor_y.0 + row_height.0);

        // Separator before revision history
        if !colofon.revision_history.is_empty() {
            cursor_y = Pt(cursor_y.0 + Pt::from(Mm(2.0)).0);
            dl.set_stroke_color(Color::LIGHT_GREY);
            dl.set_line_width(Pt(0.5));
            dl.draw_line(line_start_x, cursor_y, line_end_x, cursor_y);
            cursor_y = Pt(cursor_y.0 + Pt::from(Mm(4.0)).0);

            // Revision history header
            dl.set_fill_color(primary);
            dl.set_font("LiberationSans-Bold", Pt(10.0));
            dl.draw_text(label_x, cursor_y, "Revisiehistorie");
            cursor_y = Pt(cursor_y.0 + Pt::from(Mm(6.0)).0);

            // Table header
            let col_version_x = label_x;
            let col_date_x = Pt::from(Mm(50.0));
            let col_author_x = Pt::from(Mm(80.0));
            let col_desc_x = Pt::from(Mm(105.0));

            dl.set_fill_color(text_color);
            dl.set_font("LiberationSans-Bold", Pt(8.0));
            dl.draw_text(col_version_x, cursor_y, "Versie");
            dl.draw_text(col_date_x, cursor_y, "Datum");
            dl.draw_text(col_author_x, cursor_y, "Auteur");
            dl.draw_text(col_desc_x, cursor_y, "Omschrijving");
            cursor_y = Pt(cursor_y.0 + Pt::from(Mm(5.0)).0);

            // Rows
            dl.set_font("LiberationSans-Regular", Pt(8.0));
            for rev in &colofon.revision_history {
                dl.draw_text(col_version_x, cursor_y, &rev.version);
                dl.draw_text(col_date_x, cursor_y, &rev.date);
                dl.draw_text(
                    col_author_x,
                    cursor_y,
                    rev.author.as_deref().unwrap_or("-"),
                );
                dl.draw_text(col_desc_x, cursor_y, &rev.description);
                cursor_y = Pt(cursor_y.0 + Pt::from(Mm(5.0)).0);
            }
        }

        // Disclaimer at bottom
        if let Some(ref disclaimer) = colofon.disclaimer {
            // Position disclaimer near the bottom of the page
            let disclaimer_y = Pt::from(Mm(260.0));
            dl.set_stroke_color(Color::LIGHT_GREY);
            dl.set_line_width(Pt(0.5));
            dl.draw_line(label_x, disclaimer_y, line_end_x, disclaimer_y);

            dl.set_fill_color(Color::GREY);
            dl.set_font("LiberationSans-Regular", Pt(7.0));
            dl.draw_text(label_x, Pt(disclaimer_y.0 + Pt::from(Mm(4.0)).0), disclaimer);
        }
    } else {
        // Fallback: use data-level fields when no colofon struct
        if let Some(ref date) = data.date {
            draw_row(&mut dl, cursor_y, "Datum", date);
            cursor_y = Pt(cursor_y.0 + row_height.0);
        }

        draw_row(&mut dl, cursor_y, "Status", &format!("{:?}", data.status));
        cursor_y = Pt(cursor_y.0 + row_height.0);

        draw_row(&mut dl, cursor_y, "Versie", &data.version);
        let _ = cursor_y; // suppress unused warning
    }

    RawPage {
        page_size: A4,
        draw_list: dl,
    }
}

// ── TOC page ─────────────────────────────────────────────────────────

/// Build a table of contents page.
///
/// Layout:
/// - Title at top (18pt, primary color)
/// - List all sections with number and title
/// - Section number at x=70, title at x=110
/// - 14pt leading between entries
pub fn build_toc_page(data: &ReportData, brand: &BrandConfig) -> RawPage {
    let mut dl = DrawList::new();
    let primary = brand_primary(brand);
    let text_color = brand_text(brand);

    let num_x = Pt::from(Mm(25.0));
    let title_x = Pt::from(Mm(40.0));
    let entry_leading = Pt(14.0);

    // Title — use toc.title if available, otherwise "Inhoudsopgave"
    let toc_title = data
        .toc
        .as_ref()
        .map(|t| t.title.as_str())
        .unwrap_or("Inhoudsopgave");

    dl.set_fill_color(primary);
    dl.set_font("LiberationSans-Bold", Pt(18.0));
    dl.draw_text(num_x, Pt::from(Mm(25.0)), toc_title);

    let mut cursor_y = Pt::from(Mm(40.0));
    let max_depth = data.toc.as_ref().map(|t| t.max_depth).unwrap_or(3);

    // Track chapter numbering
    let mut chapter_num = 0u32;

    for section in &data.sections {
        if section.level > max_depth {
            continue;
        }

        if section.level == 1 {
            chapter_num += 1;
        }

        // Section number
        let number_text = if section.level == 1 {
            format!("{}.", chapter_num)
        } else {
            // For sub-levels, use indentation instead of complex numbering
            String::new()
        };

        let indent = Pt((section.level as f32 - 1.0) * Pt::from(Mm(6.0)).0);

        dl.set_fill_color(primary);
        dl.set_font("LiberationSans-Bold", Pt(10.0));
        if !number_text.is_empty() {
            dl.draw_text(Pt(num_x.0 + indent.0), cursor_y, &number_text);
        }

        dl.set_fill_color(text_color);
        let font_size = if section.level == 1 { 10.0 } else { 9.0 };
        let font_name = if section.level == 1 {
            "LiberationSans-Bold"
        } else {
            "LiberationSans-Regular"
        };
        dl.set_font(font_name, Pt(font_size));
        dl.draw_text(Pt(title_x.0 + indent.0), cursor_y, &section.title);

        cursor_y = Pt(cursor_y.0 + entry_leading.0);
    }

    RawPage {
        page_size: A4,
        draw_list: dl,
    }
}

// ── Backcover page ───────────────────────────────────────────────────

/// Build a backcover page with brand colors.
///
/// Layout:
/// - Full secondary color background
/// - Small accent rectangle (primary color) at bottom-left
/// - Brand name centered, large
/// - Contact info centered below brand name
pub fn build_backcover_page(data: &ReportData, brand: &BrandConfig) -> RawPage {
    let _ = data; // data not used for backcover, but kept for API consistency
    let mut dl = DrawList::new();
    let primary = brand_primary(brand);
    let secondary = brand_secondary(brand);

    let page_w = A4.width;
    let page_h = A4.height;
    let center_x = Pt(page_w.0 / 2.0);

    // Full-page secondary color background
    dl.set_fill_color(secondary);
    dl.draw_rect(Pt(0.0), Pt(0.0), page_w, page_h, true, false);

    // Small accent rectangle at bottom-left
    let accent_w = Pt::from(Mm(30.0));
    let accent_h = Pt::from(Mm(8.0));
    let accent_y = Pt(page_h.0 - accent_h.0 - Pt::from(Mm(15.0)).0);
    dl.set_fill_color(primary);
    dl.draw_rect(Pt::from(Mm(15.0)), accent_y, accent_w, accent_h, true, false);

    // Brand name — centered, large
    dl.set_fill_color(Color::WHITE);
    dl.set_font("LiberationSans-Bold", Pt(24.0));
    dl.draw_text_center(center_x, Pt(page_h.0 * 0.40), &brand.brand.name);

    // Tagline below brand name
    if let Some(ref tagline) = brand.brand.tagline {
        dl.set_font("LiberationSans-Regular", Pt(11.0));
        dl.draw_text_center(center_x, Pt(page_h.0 * 0.40 + Pt::from(Mm(10.0)).0), tagline);
    }

    // Contact info from brand
    let mut contact_y = Pt(page_h.0 * 0.55);
    let contact_leading = Pt::from(Mm(6.0));
    dl.set_fill_color(Color::WHITE);
    dl.set_font("LiberationSans-Regular", Pt(9.0));

    if let Some(name) = brand.contact.get("name") {
        dl.draw_text_center(center_x, contact_y, name);
        contact_y = Pt(contact_y.0 + contact_leading.0);
    }
    if let Some(address) = brand.contact.get("address") {
        dl.draw_text_center(center_x, contact_y, address);
        contact_y = Pt(contact_y.0 + contact_leading.0);
    }
    if let Some(website) = brand.contact.get("website") {
        dl.draw_text_center(center_x, contact_y, website);
    }

    RawPage {
        page_size: A4,
        draw_list: dl,
    }
}

// ── Tests ────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::brand::{BrandIdentity, ZoneConfig};
    use crate::schema::*;
    use std::collections::HashMap;

    fn test_brand() -> BrandConfig {
        let mut colors = HashMap::new();
        colors.insert("primary".to_string(), "#40124A".to_string());
        colors.insert("secondary".to_string(), "#38BDA0".to_string());
        colors.insert("text".to_string(), "#45243D".to_string());

        let mut contact = HashMap::new();
        contact.insert("name".to_string(), "OpenAEC".to_string());
        contact.insert("address".to_string(), "Street 1 | City".to_string());
        contact.insert("website".to_string(), "www.openaec.nl".to_string());

        BrandConfig {
            brand: BrandIdentity {
                name: "OpenAEC".to_string(),
                slug: "openaec".to_string(),
                tenant: None,
                tagline: Some("Engineering excellence".to_string()),
            },
            colors,
            fonts: HashMap::new(),
            logos: HashMap::new(),
            contact,
            header: ZoneConfig::default(),
            footer: ZoneConfig::default(),
            styles: HashMap::new(),
            pages: HashMap::new(),
            stationery: HashMap::new(),
            modules: HashMap::new(),
            module_config: HashMap::new(),
            tenant_modules: serde_yaml::Value::Null,
            font_files: HashMap::new(),
            brand_dir: None,
        }
    }

    fn minimal_data() -> ReportData {
        ReportData {
            template: "structural".to_string(),
            project: "Test Project".to_string(),
            tenant: None,
            format: PaperFormat::A4,
            orientation: Orientation::Portrait,
            project_number: Some("2026-001".to_string()),
            client: Some("Test Client".to_string()),
            author: "JK".to_string(),
            date: Some("2026-03-15".to_string()),
            version: "1.0".to_string(),
            status: ReportStatus::Concept,
            cover: Some(Cover {
                subtitle: Some("Constructieve berekening".to_string()),
                image: None,
                extra_fields: HashMap::new(),
            }),
            colofon: Some(Colofon {
                enabled: true,
                opdrachtgever_naam: Some("Gemeente Den Haag".to_string()),
                opdrachtgever_contact: None,
                opdrachtgever_adres: None,
                adviseur_bedrijf: Some("OpenAEC".to_string()),
                adviseur_naam: Some("J. Kragten".to_string()),
                normen: None,
                documentgegevens: None,
                datum: Some("2026-03-15".to_string()),
                fase: None,
                status_colofon: Some("Concept".to_string()),
                kenmerk: Some("2026-001-R01".to_string()),
                adviseur_email: None,
                adviseur_telefoon: None,
                adviseur_functie: None,
                adviseur_registratie: None,
                extra_fields: HashMap::new(),
                revision_history: vec![RevisionEntry {
                    version: "1.0".to_string(),
                    date: "2026-03-15".to_string(),
                    author: Some("JK".to_string()),
                    description: "Eerste uitgave".to_string(),
                }],
                disclaimer: Some("Dit rapport is vertrouwelijk.".to_string()),
            }),
            toc: Some(TocConfig {
                enabled: true,
                title: "Inhoudsopgave".to_string(),
                max_depth: 3,
            }),
            sections: vec![
                Section {
                    title: "Uitgangspunten".to_string(),
                    level: 1,
                    content: vec![],
                    orientation: None,
                    page_break_before: false,
                },
                Section {
                    title: "Belastingen".to_string(),
                    level: 1,
                    content: vec![],
                    orientation: None,
                    page_break_before: false,
                },
                Section {
                    title: "Permanente belasting".to_string(),
                    level: 2,
                    content: vec![],
                    orientation: None,
                    page_break_before: false,
                },
            ],
            backcover: Some(BackcoverConfig { enabled: true }),
            metadata: HashMap::new(),
        }
    }

    #[test]
    fn test_brand_color_helpers() {
        let brand = test_brand();
        assert_eq!(brand_primary(&brand), Color::rgb(0x40, 0x12, 0x4A));
        assert_eq!(brand_secondary(&brand), Color::rgb(0x38, 0xBD, 0xA0));
        assert_eq!(brand_text(&brand), Color::rgb(0x45, 0x24, 0x3D));
    }

    #[test]
    fn test_brand_color_fallback() {
        let brand = BrandConfig {
            brand: BrandIdentity::default(),
            colors: HashMap::new(),
            fonts: HashMap::new(),
            logos: HashMap::new(),
            contact: HashMap::new(),
            header: ZoneConfig::default(),
            footer: ZoneConfig::default(),
            styles: HashMap::new(),
            pages: HashMap::new(),
            stationery: HashMap::new(),
            modules: HashMap::new(),
            module_config: HashMap::new(),
            tenant_modules: serde_yaml::Value::Null,
            font_files: HashMap::new(),
            brand_dir: None,
        };
        // Should fall back to OpenAEC defaults
        assert_eq!(brand_primary(&brand), Color::rgb(0x40, 0x12, 0x4A));
        assert_eq!(brand_secondary(&brand), Color::rgb(0x38, 0xBD, 0xA0));
        assert_eq!(brand_text(&brand), Color::rgb(0x45, 0x24, 0x3D));
    }

    #[test]
    fn test_build_cover_page() {
        let data = minimal_data();
        let brand = test_brand();
        let page = build_cover_page(&data, &brand);

        assert_eq!(page.page_size, A4);
        // Should have draw ops: rect + font + text (brand name) + font + text (title) + ...
        assert!(
            page.draw_list.ops.len() >= 5,
            "Cover page should have at least 5 draw ops, got {}",
            page.draw_list.ops.len()
        );
    }

    #[test]
    fn test_build_cover_page_minimal() {
        let mut data = minimal_data();
        data.cover = None;
        data.project_number = None;
        data.client = None;
        data.date = None;

        let brand = test_brand();
        let page = build_cover_page(&data, &brand);

        assert_eq!(page.page_size, A4);
        assert!(!page.draw_list.ops.is_empty());
    }

    #[test]
    fn test_build_colofon_page() {
        let data = minimal_data();
        let brand = test_brand();
        let page = build_colofon_page(&data, &brand);

        assert_eq!(page.page_size, A4);
        // Should have many draw ops: title + rows + separators + revision history + disclaimer
        assert!(
            page.draw_list.ops.len() >= 10,
            "Colofon page should have at least 10 draw ops, got {}",
            page.draw_list.ops.len()
        );
    }

    #[test]
    fn test_build_colofon_page_without_colofon() {
        let mut data = minimal_data();
        data.colofon = None;

        let brand = test_brand();
        let page = build_colofon_page(&data, &brand);

        assert_eq!(page.page_size, A4);
        assert!(!page.draw_list.ops.is_empty());
    }

    #[test]
    fn test_build_toc_page() {
        let data = minimal_data();
        let brand = test_brand();
        let page = build_toc_page(&data, &brand);

        assert_eq!(page.page_size, A4);
        // Title + 3 sections (each has font + text ops)
        assert!(
            page.draw_list.ops.len() >= 6,
            "TOC page should have at least 6 draw ops, got {}",
            page.draw_list.ops.len()
        );
    }

    #[test]
    fn test_build_toc_page_empty_sections() {
        let mut data = minimal_data();
        data.sections.clear();

        let brand = test_brand();
        let page = build_toc_page(&data, &brand);

        assert_eq!(page.page_size, A4);
        // At minimum: title font + text
        assert!(page.draw_list.ops.len() >= 2);
    }

    #[test]
    fn test_build_toc_respects_max_depth() {
        let mut data = minimal_data();
        data.toc = Some(TocConfig {
            enabled: true,
            title: "Contents".to_string(),
            max_depth: 1,
        });
        // Add a level-2 section that should be filtered out
        data.sections.push(Section {
            title: "Should be filtered".to_string(),
            level: 2,
            content: vec![],
            orientation: None,
            page_break_before: false,
        });

        let brand = test_brand();
        let page_depth_1 = build_toc_page(&data, &brand);

        // With max_depth=3
        data.toc = Some(TocConfig {
            enabled: true,
            title: "Contents".to_string(),
            max_depth: 3,
        });
        let page_depth_3 = build_toc_page(&data, &brand);

        // depth_3 should have more ops (the level-2 entries are included)
        assert!(page_depth_3.draw_list.ops.len() > page_depth_1.draw_list.ops.len());
    }

    #[test]
    fn test_build_backcover_page() {
        let data = minimal_data();
        let brand = test_brand();
        let page = build_backcover_page(&data, &brand);

        assert_eq!(page.page_size, A4);
        // Background rect + accent rect + brand name + tagline + contact lines
        assert!(
            page.draw_list.ops.len() >= 6,
            "Backcover should have at least 6 draw ops, got {}",
            page.draw_list.ops.len()
        );
    }

    #[test]
    fn test_build_backcover_no_contact() {
        let data = minimal_data();
        let mut brand = test_brand();
        brand.contact.clear();
        brand.brand.tagline = None;

        let page = build_backcover_page(&data, &brand);

        assert_eq!(page.page_size, A4);
        // Should still render background + accent + brand name
        assert!(page.draw_list.ops.len() >= 4);
    }
}
