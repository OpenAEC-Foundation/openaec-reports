//! Font registry — TTF loading, metrics, text measurement.

use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;

use crate::error::LayoutError;
use crate::types::Pt;

/// Opaque font identifier.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct FontId(pub(crate) usize);

/// Cached per-font data and metrics.
struct FontEntry {
    /// Raw TTF/OTF bytes (kept for PDF embedding).
    data: Vec<u8>,
    /// Units per em from the font header.
    units_per_em: f32,
    /// Typographic ascender in font units.
    ascender: f32,
    /// Typographic descender in font units (negative).
    descender: f32,
    /// Glyph advance widths cache (char → advance in font units).
    advances: HashMap<char, f32>,
    /// Glyph coverage cache (char → font has a glyph for it).
    covered: HashMap<char, bool>,
}

impl FontEntry {
    fn load(data: Vec<u8>) -> Result<Self, LayoutError> {
        let face = ttf_parser::Face::parse(&data, 0)
            .map_err(|e| LayoutError::FontParseError(e.to_string()))?;

        let units_per_em = face.units_per_em() as f32;
        let ascender = face.ascender() as f32;
        let descender = face.descender() as f32;

        // Pre-cache ASCII advances
        let mut advances = HashMap::with_capacity(128);
        for ch in ' '..='~' {
            if let Some(glyph_id) = face.glyph_index(ch) {
                let advance = face.glyph_hor_advance(glyph_id).unwrap_or(0) as f32;
                advances.insert(ch, advance);
            }
        }

        Ok(Self {
            data,
            units_per_em,
            ascender,
            descender,
            advances,
            covered: HashMap::new(),
        })
    }

    fn char_advance(&mut self, ch: char) -> f32 {
        if let Some(&adv) = self.advances.get(&ch) {
            return adv;
        }
        // Cache miss — parse face and look up
        let advance = ttf_parser::Face::parse(&self.data, 0)
            .ok()
            .and_then(|face| face.glyph_index(ch).and_then(|gid| face.glyph_hor_advance(gid)))
            .unwrap_or(0) as f32;
        self.advances.insert(ch, advance);
        advance
    }

    fn has_char(&mut self, ch: char) -> bool {
        if let Some(&has) = self.covered.get(&ch) {
            return has;
        }
        let has = ttf_parser::Face::parse(&self.data, 0)
            .ok()
            .and_then(|face| face.glyph_index(ch))
            .is_some();
        self.covered.insert(ch, has);
        has
    }
}

/// Registry of loaded fonts with metrics and measurement.
pub struct FontRegistry {
    fonts: Vec<FontEntry>,
    names: HashMap<String, FontId>,
    /// Fonts used per character when the requested font lacks a glyph, in
    /// order. Empty by default; see [`FontRegistry::add_fallback_ttf_bytes`].
    fallbacks: Vec<FontId>,
}

impl FontRegistry {
    pub fn new() -> Self {
        Self {
            fonts: Vec::new(),
            names: HashMap::new(),
            fallbacks: Vec::new(),
        }
    }

    /// Add a fallback font (opt-in).
    ///
    /// When the font of a text lacks a glyph for a character, that character
    /// is measured and drawn with the first fallback font that has it.
    /// Without fallbacks such a character is measured as zero width and left
    /// out of the PDF. A fallback font has no name of its own and is only
    /// embedded in PDFs that use it.
    ///
    /// There is no shaping: characters are drawn one glyph each, left to
    /// right, so scripts that need joining or reordering (Arabic, Indic)
    /// come out as separate letters. Bold and italic text get the fallback's
    /// own style. The font is embedded whole (printpdf does not subset), so
    /// prefer small fonts; TrueType outlines only (no CFF-based `.otf`).
    pub fn add_fallback_ttf_bytes(&mut self, data: Vec<u8>) -> Result<FontId, LayoutError> {
        let entry = FontEntry::load(data)?;
        let id = FontId(self.fonts.len());
        self.fonts.push(entry);
        self.fallbacks.push(id);
        Ok(id)
    }

    /// The fallback fonts, in the order they are tried.
    pub fn fallbacks(&self) -> &[FontId] {
        &self.fallbacks
    }

    /// The font that draws `ch` in text set in `id`: `id` itself when it has
    /// a glyph for `ch`, otherwise the first fallback font that has one,
    /// otherwise `id`.
    pub fn font_for_char(&mut self, id: FontId, ch: char) -> FontId {
        if self.fallbacks.is_empty() || self.fonts[id.0].has_char(ch) {
            return id;
        }
        for i in 0..self.fallbacks.len() {
            let fallback = self.fallbacks[i];
            if self.fonts[fallback.0].has_char(ch) {
                return fallback;
            }
        }
        id
    }

    /// Split `text` set in `id` into runs that each use one font (see
    /// [`FontRegistry::font_for_char`]). Without fallback fonts this is one
    /// run in `id`.
    pub fn text_runs(&mut self, id: FontId, text: &str) -> Vec<(FontId, String)> {
        if self.fallbacks.is_empty() {
            return vec![(id, text.to_string())];
        }
        let mut runs: Vec<(FontId, String)> = Vec::new();
        for ch in text.chars() {
            let font = self.font_for_char(id, ch);
            match runs.last_mut() {
                Some((last, run)) if *last == font => run.push(ch),
                _ => runs.push((font, ch.to_string())),
            }
        }
        runs
    }

    /// Register a TTF/OTF font from file.
    pub fn register_ttf(&mut self, name: &str, path: &Path) -> Result<FontId, LayoutError> {
        let data = std::fs::read(path).map_err(|e| {
            LayoutError::FontNotFound(format!("{}: {}", path.display(), e))
        })?;
        self.register_ttf_bytes(name, data)
    }

    /// Register a TTF/OTF font from bytes.
    pub fn register_ttf_bytes(&mut self, name: &str, data: Vec<u8>) -> Result<FontId, LayoutError> {
        let entry = FontEntry::load(data)?;
        let id = FontId(self.fonts.len());
        self.fonts.push(entry);
        self.names.insert(name.to_string(), id);
        Ok(id)
    }

    /// Register an alias for an existing font name.
    ///
    /// This allows e.g. `"LiberationSans"` to resolve to `"LiberationSans-Regular"`.
    pub fn register_alias(&mut self, alias: &str, target: &str) -> bool {
        if let Some(&id) = self.names.get(target) {
            self.names.insert(alias.to_string(), id);
            true
        } else {
            false
        }
    }

    /// Look up font by name, with automatic `-Regular` suffix fallback.
    pub fn get(&self, name: &str) -> Option<FontId> {
        self.names
            .get(name)
            .or_else(|| self.names.get(&format!("{}-Regular", name)))
            .copied()
    }

    /// Get raw font bytes (for PDF embedding).
    pub fn font_data(&self, id: FontId) -> &[u8] {
        &self.fonts[id.0].data
    }

    /// Measure the width of a text string at a given font size. Characters
    /// the font lacks are measured in the fallback font that draws them.
    pub fn text_width(&mut self, id: FontId, text: &str, size: Pt) -> Pt {
        // Sum font units per run and scale once, so text without fallback
        // characters measures exactly as before fallbacks existed.
        if self.fallbacks.is_empty() {
            let entry = &mut self.fonts[id.0];
            let units: f32 = text.chars().map(|ch| entry.char_advance(ch)).sum();
            return Pt(units * size.0 / entry.units_per_em);
        }
        let mut total = 0.0;
        for (font, run) in self.text_runs(id, text) {
            let entry = &mut self.fonts[font.0];
            let units: f32 = run.chars().map(|ch| entry.char_advance(ch)).sum();
            total += units * size.0 / entry.units_per_em;
        }
        Pt(total)
    }

    /// Measure width of a single character (in the fallback font that draws
    /// it, when `id` lacks it).
    pub fn char_width(&mut self, id: FontId, ch: char, size: Pt) -> Pt {
        let font = self.font_for_char(id, ch);
        let entry = &mut self.fonts[font.0];
        let advance = entry.char_advance(ch);
        Pt(advance * size.0 / entry.units_per_em)
    }

    /// Font ascender at a given size (positive, above baseline).
    pub fn ascent(&self, id: FontId, size: Pt) -> Pt {
        let entry = &self.fonts[id.0];
        Pt(entry.ascender * size.0 / entry.units_per_em)
    }

    /// Font descender at a given size (positive value, below baseline).
    pub fn descent(&self, id: FontId, size: Pt) -> Pt {
        let entry = &self.fonts[id.0];
        Pt(-entry.descender * size.0 / entry.units_per_em)
    }

    /// Recommended line height at a given size.
    pub fn line_height(&self, id: FontId, size: Pt) -> Pt {
        let ascent = self.ascent(id, size);
        let descent = self.descent(id, size);
        Pt(ascent.0 + descent.0)
    }

    /// Number of registered fonts.
    pub fn len(&self) -> usize {
        self.fonts.len()
    }

    /// Whether the registry is empty.
    pub fn is_empty(&self) -> bool {
        self.fonts.is_empty()
    }

    /// Iterator over registered font names and IDs.
    pub fn iter(&self) -> impl Iterator<Item = (&str, FontId)> {
        self.names.iter().map(|(name, &id)| (name.as_str(), id))
    }
}

impl Default for FontRegistry {
    fn default() -> Self {
        Self::new()
    }
}

/// Shared font registry (Arc wrapper for thread safety).
pub type SharedFontRegistry = Arc<std::sync::Mutex<FontRegistry>>;

/// Create a new shared font registry.
pub fn shared_font_registry() -> SharedFontRegistry {
    Arc::new(std::sync::Mutex::new(FontRegistry::new()))
}

#[cfg(test)]
mod tests {
    use super::*;

    // Note: tests that need actual TTF files are in integration tests.
    // These tests verify the API surface.

    #[test]
    fn test_empty_registry() {
        let reg = FontRegistry::new();
        assert!(reg.is_empty());
        assert_eq!(reg.len(), 0);
        assert!(reg.get("anything").is_none());
    }

    // Liberation Sans lacks ₹; Space Grotesk has it and uses 1000 units per
    // em instead of 2048, so the tests also cover scaling per font.
    const LIBERATION: &[u8] =
        include_bytes!("../../../../src/openaec_reports/assets/fonts/LiberationSans-Regular.ttf");
    const GROTESK: &[u8] = include_bytes!("../../../../tenants/default/fonts/SpaceGrotesk-Regular.ttf");

    fn advance(data: &[u8], ch: char) -> f32 {
        let face = ttf_parser::Face::parse(data, 0).unwrap();
        let glyph = face.glyph_index(ch).expect("glyph");
        face.glyph_hor_advance(glyph).unwrap() as f32 / face.units_per_em() as f32
    }

    #[test]
    fn without_fallbacks_a_missing_glyph_has_no_width() {
        let mut reg = FontRegistry::new();
        let id = reg.register_ttf_bytes("LiberationSans", LIBERATION.to_vec()).unwrap();
        assert_eq!(reg.text_width(id, "A₹", Pt(10.0)), reg.text_width(id, "A", Pt(10.0)));
        assert_eq!(reg.text_runs(id, "A₹B"), vec![(id, "A₹B".to_string())]);
    }

    #[test]
    fn fallback_draws_only_the_missing_glyphs() {
        let mut reg = FontRegistry::new();
        let id = reg.register_ttf_bytes("LiberationSans", LIBERATION.to_vec()).unwrap();
        let before = reg.text_width(id, "Totaal 1.000", Pt(10.0));
        let fallback = reg.add_fallback_ttf_bytes(GROTESK.to_vec()).unwrap();

        assert_eq!(reg.fallbacks(), &[fallback]);
        assert!(reg.get("SpaceGrotesk").is_none(), "a fallback has no name");
        // Space Grotesk also has "A", but Liberation draws what it can.
        assert_eq!(
            reg.text_runs(id, "A ₹B"),
            vec![(id, "A ".to_string()), (fallback, "₹".to_string()), (id, "B".to_string())]
        );
        assert_eq!(reg.text_width(id, "Totaal 1.000", Pt(10.0)), before);

        let rupee = reg.char_width(id, '₹', Pt(10.0)).0;
        assert!((rupee - advance(GROTESK, '₹') * 10.0).abs() < 1e-4, "{rupee}");
        let with = reg.text_width(id, "A₹", Pt(10.0)).0;
        let expected = (advance(LIBERATION, 'A') + advance(GROTESK, '₹')) * 10.0;
        assert!((with - expected).abs() < 1e-4, "{with} != {expected}");
    }

    #[test]
    fn a_glyph_no_font_has_stays_in_the_text_font() {
        let mut reg = FontRegistry::new();
        let id = reg.register_ttf_bytes("LiberationSans", LIBERATION.to_vec()).unwrap();
        reg.add_fallback_ttf_bytes(GROTESK.to_vec()).unwrap();
        // U+0E01 (Thai) is in neither font.
        assert_eq!(reg.font_for_char(id, '\u{0E01}'), id);
        assert_eq!(reg.char_width(id, '\u{0E01}', Pt(10.0)), Pt(0.0));
    }

    #[test]
    fn fallbacks_are_tried_in_order() {
        const INTER: &[u8] = include_bytes!("../../../../tenants/default/fonts/Inter-Regular.ttf");
        let mut reg = FontRegistry::new();
        let id = reg.register_ttf_bytes("LiberationSans", LIBERATION.to_vec()).unwrap();
        let first = reg.add_fallback_ttf_bytes(GROTESK.to_vec()).unwrap();
        let second = reg.add_fallback_ttf_bytes(INTER.to_vec()).unwrap();
        // Both have ₹; the first one added wins.
        assert_eq!(reg.font_for_char(id, '₹'), first);
        assert_eq!(reg.fallbacks(), &[first, second]);
    }
}
