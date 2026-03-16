//! Brand configuration system.
//!
//! Loads brand definitions from YAML with multi-tenant resolution.
//! Port of the Python `brand.py` module.

use std::collections::HashMap;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::tenant::TenantConfig;

// ── Error Types ───────────────────────────────────────────────────────

#[derive(Debug, thiserror::Error)]
pub enum BrandError {
    #[error("Brand file not found: {0}")]
    NotFound(PathBuf),

    #[error("Failed to read brand file: {0}")]
    Io(#[from] std::io::Error),

    #[error("Failed to parse brand YAML: {0}")]
    Yaml(#[from] serde_yaml::Error),
}

// ── Brand Config ──────────────────────────────────────────────────────

/// Complete brand configuration loaded from YAML.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BrandConfig {
    /// Brand identity.
    #[serde(default)]
    pub brand: BrandIdentity,

    /// Color palette (name -> hex).
    #[serde(default)]
    pub colors: HashMap<String, String>,

    /// Font mapping (role -> font name).
    #[serde(default)]
    pub fonts: HashMap<String, String>,

    /// Logo mapping (variant -> relative path).
    #[serde(default)]
    pub logos: HashMap<String, String>,

    /// Contact information.
    #[serde(default)]
    pub contact: HashMap<String, String>,

    /// Header zone configuration.
    #[serde(default)]
    pub header: ZoneConfig,

    /// Footer zone configuration.
    #[serde(default)]
    pub footer: ZoneConfig,

    /// ReportLab paragraph styles.
    #[serde(default)]
    pub styles: HashMap<String, StyleConfig>,

    /// Page-specific configurations (cover, colofon, toc, etc.).
    #[serde(default)]
    pub pages: HashMap<String, serde_yaml::Value>,

    /// Stationery configuration per page type.
    #[serde(default)]
    pub stationery: HashMap<String, StationeryPageConfig>,

    /// Module styling (table, calculation, check).
    #[serde(default)]
    pub modules: HashMap<String, serde_yaml::Value>,

    /// Module configuration (extended).
    #[serde(default)]
    pub module_config: HashMap<String, serde_yaml::Value>,

    /// Tenant-specific module types.
    #[serde(default)]
    pub tenant_modules: serde_yaml::Value,

    /// Tenant font file mappings (font name -> filename).
    #[serde(default)]
    pub font_files: HashMap<String, String>,

    /// Directory of the YAML file (for resolving relative paths).
    /// Not serialized — set by the loader.
    #[serde(skip)]
    pub brand_dir: Option<PathBuf>,
}

/// Brand identity fields.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct BrandIdentity {
    /// Display name.
    #[serde(default)]
    pub name: String,

    /// URL-safe slug.
    #[serde(default)]
    pub slug: String,

    /// Tenant identifier.
    #[serde(default)]
    pub tenant: Option<String>,

    /// Tagline text.
    #[serde(default)]
    pub tagline: Option<String>,
}

// ── Zone Config (header/footer) ───────────────────────────────────────

/// Header or footer zone configuration.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ZoneConfig {
    /// Zone height in mm (0 = disabled).
    #[serde(default)]
    pub height: f64,

    /// Drawable elements in this zone.
    #[serde(default)]
    pub elements: Vec<ElementConfig>,
}

/// A single drawable element (rectangle, text, image, line).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ElementConfig {
    /// Element type: "rect", "text", "image", "line".
    #[serde(rename = "type")]
    pub element_type: String,

    /// X position in mm from page edge.
    #[serde(default)]
    pub x: f64,

    /// Y position in mm from page edge.
    #[serde(default)]
    pub y: f64,

    /// Width in mm.
    #[serde(default)]
    pub width: Option<f64>,

    /// Height in mm.
    #[serde(default)]
    pub height: Option<f64>,

    /// Fill color (hex or "$primary" variable reference).
    #[serde(default)]
    pub fill: Option<String>,

    /// Text/line color.
    #[serde(default)]
    pub color: Option<String>,

    /// Outline stroke color.
    #[serde(default)]
    pub stroke: Option<String>,

    /// Stroke width.
    #[serde(default)]
    pub stroke_width: Option<f64>,

    /// Text content with variable placeholders like "{page}".
    #[serde(default)]
    pub content: Option<String>,

    /// Image path relative to assets/.
    #[serde(default)]
    pub src: Option<String>,

    /// Font reference (e.g., "$heading" or "Helvetica-Bold").
    #[serde(default)]
    pub font: Option<String>,

    /// Font size in points.
    #[serde(default)]
    pub size: Option<f64>,

    /// Text alignment: "left", "center", "right".
    #[serde(default)]
    pub align: Option<String>,
}

// ── Style Config ──────────────────────────────────────────────────────

/// Paragraph style definition (maps to ReportLab/Typst styles).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StyleConfig {
    #[serde(rename = "fontName")]
    pub font_name: Option<String>,

    #[serde(rename = "fontSize")]
    pub font_size: Option<f64>,

    /// Line spacing (leading).
    pub leading: Option<f64>,

    #[serde(rename = "textColor")]
    pub text_color: Option<String>,
}

// ── Stationery Config ─────────────────────────────────────────────────

/// Stationery template for a specific page type.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct StationeryPageConfig {
    /// Path to stationery PDF/PNG (relative to brand dir).
    #[serde(default)]
    pub source: String,

    /// Which header/footer to apply.
    #[serde(default)]
    pub header_footer: Option<String>,

    /// Text placement zones.
    #[serde(default)]
    pub text_zones: Vec<serde_yaml::Value>,

    /// Content area definition.
    #[serde(default)]
    pub content_frame: Option<ContentFrame>,
}

/// Content frame positioning for stationery pages.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentFrame {
    pub x_pt: f64,
    pub y_pt: f64,
    pub width_pt: f64,
    pub height_pt: f64,
}

// ── Brand Loader ──────────────────────────────────────────────────────

/// Loads and resolves brand YAML files with multi-tenant support.
pub struct BrandLoader {
    tenant_config: TenantConfig,
}

impl BrandLoader {
    /// Create a new BrandLoader with the given tenant configuration.
    pub fn new(tenant_config: TenantConfig) -> Self {
        Self { tenant_config }
    }

    /// Load a brand by name.
    ///
    /// Resolution order:
    /// 1. Tenant brand.yaml (if slug matches or name matches)
    /// 2. Tenants root: `<tenants_root>/<name>/brand.yaml`
    /// 3. Package brands: `assets/brands/<name>.yaml`
    pub fn load(&self, name: Option<&str>) -> Result<BrandConfig, BrandError> {
        match name {
            Some(name) => self.load_named(name),
            None => self.load_default(),
        }
    }

    /// Load the default brand (from tenant or package defaults).
    pub fn load_default(&self) -> Result<BrandConfig, BrandError> {
        match self.tenant_config.brand_path() {
            Some(path) => self.load_from_file(&path),
            None => Err(BrandError::NotFound(PathBuf::from("default brand"))),
        }
    }

    /// Load a brand by name, searching through resolution chain.
    fn load_named(&self, name: &str) -> Result<BrandConfig, BrandError> {
        // 1. Check tenant brand.yaml
        if let Some(td) = self.tenant_config.tenant_dir() {
            let tenant_brand = td.join("brand.yaml");
            if tenant_brand.is_file() {
                // Check if slug matches
                let config = self.load_from_file(&tenant_brand)?;
                if config.brand.slug == name || config.brand.name == name {
                    return Ok(config);
                }
            }
        }

        // 2. Check tenants root
        if let Some(root) = self.tenant_config.tenants_root() {
            let brand_path = root.join(name).join("brand.yaml");
            if brand_path.is_file() {
                return self.load_from_file(&brand_path);
            }
        }

        // 3. Package brands (would need package_assets_dir exposure)
        // For now, return not found
        Err(BrandError::NotFound(PathBuf::from(name)))
    }

    /// Load a brand configuration from a specific YAML file.
    pub fn load_from_file(&self, path: &Path) -> Result<BrandConfig, BrandError> {
        if !path.is_file() {
            return Err(BrandError::NotFound(path.to_path_buf()));
        }

        let content = std::fs::read_to_string(path)?;
        let mut config: BrandConfig = serde_yaml::from_str(&content)?;
        config.brand_dir = path.parent().map(PathBuf::from);

        Ok(config)
    }

    /// List all available brands (deduplicated by slug).
    pub fn list_brands(&self) -> Vec<BrandInfo> {
        let mut brands = Vec::new();
        let mut seen_slugs = std::collections::HashSet::new();

        // Tenant brand
        if let Some(td) = self.tenant_config.tenant_dir() {
            let brand_path = td.join("brand.yaml");
            if let Ok(config) = self.load_from_file(&brand_path)
                && seen_slugs.insert(config.brand.slug.clone()) {
                    brands.push(BrandInfo {
                        name: config.brand.name,
                        slug: config.brand.slug,
                        source: BrandSource::Tenant,
                    });
                }
        }

        // Tenants root scan
        if let Some(ref root) = self.tenant_config.tenants_root()
            && let Ok(entries) = std::fs::read_dir(root) {
                for entry in entries.flatten() {
                    let brand_path = entry.path().join("brand.yaml");
                    if let Ok(config) = self.load_from_file(&brand_path)
                        && seen_slugs.insert(config.brand.slug.clone()) {
                            brands.push(BrandInfo {
                                name: config.brand.name,
                                slug: config.brand.slug,
                                source: BrandSource::TenantsRoot,
                            });
                        }
                }
            }

        brands
    }
}

/// Summary info for a discovered brand.
#[derive(Debug, Clone)]
pub struct BrandInfo {
    pub name: String,
    pub slug: String,
    pub source: BrandSource,
}

/// Where a brand was found.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BrandSource {
    Tenant,
    TenantsRoot,
    Package,
}

// ── Color Resolution ──────────────────────────────────────────────────

impl BrandConfig {
    /// Resolve a color reference.
    ///
    /// Supports:
    /// - Direct hex: "#40124A"
    /// - Variable: "$primary" → looks up in colors map
    /// - Extended: "$colors.primary" → same lookup
    pub fn resolve_color<'a>(&'a self, reference: &'a str) -> Option<&'a str> {
        if reference.starts_with('#') {
            return Some(reference);
        }

        let key = reference
            .strip_prefix("$colors.")
            .or_else(|| reference.strip_prefix('$'));

        key.and_then(|k| self.colors.get(k).map(|s| s.as_str()))
    }

    /// Resolve a font reference.
    ///
    /// Supports:
    /// - Variable: "$heading" → looks up in fonts map
    /// - Literal: "Helvetica-Bold" → returned as-is
    pub fn resolve_font<'a>(&'a self, reference: &'a str) -> &'a str {
        if let Some(key) = reference.strip_prefix('$') {
            self.fonts
                .get(key)
                .map(|s| s.as_str())
                .unwrap_or(reference)
        } else {
            reference
        }
    }

    /// Get a logo path, resolved relative to brand_dir.
    pub fn logo_path(&self, variant: &str) -> Option<PathBuf> {
        let relative = self.logos.get(variant)?;
        self.brand_dir
            .as_ref()
            .map(|dir| dir.join(relative))
            .or_else(|| Some(PathBuf::from(relative)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_yaml() -> &'static str {
        r##"
brand:
  name: "Test Brand"
  slug: "test-brand"
  tagline: "Engineering excellence"

colors:
  primary: "#40124A"
  secondary: "#38BDA0"
  text: "#45243D"

fonts:
  heading: "Inter-Bold"
  body: "Inter-Regular"

logos:
  main: "logos/main.png"
  white: "logos/white.png"

contact:
  name: "Test Company"
  address: "Street 1 | City"

header:
  height: 0
  elements: []

footer:
  height: 17
  elements:
    - type: text
      content: "{page}"
      x: 188
      y: 5
      font: "$body"
      size: 9.5
      color: "$text"
      align: right

styles:
  Normal:
    fontName: "Inter-Regular"
    fontSize: 9.5
    leading: 12.0
    textColor: "#45243D"
  Heading1:
    fontName: "Inter-Bold"
    fontSize: 18.0
    leading: 23.4
    textColor: "#45243D"

stationery:
  cover:
    source: ""
    text_zones: []
  content:
    source: ""
    header_footer: "content"
    content_frame:
      x_pt: 90.0
      y_pt: 38.9
      width_pt: 451.6
      height_pt: 746.0
"##
    }

    #[test]
    fn test_parse_brand_yaml() {
        let config: BrandConfig = serde_yaml::from_str(sample_yaml()).unwrap();
        assert_eq!(config.brand.name, "Test Brand");
        assert_eq!(config.brand.slug, "test-brand");
        assert_eq!(config.colors.get("primary").unwrap(), "#40124A");
        assert_eq!(config.fonts.get("heading").unwrap(), "Inter-Bold");
        assert_eq!(config.logos.get("main").unwrap(), "logos/main.png");
    }

    #[test]
    fn test_resolve_color() {
        let config: BrandConfig = serde_yaml::from_str(sample_yaml()).unwrap();

        // Direct hex
        assert_eq!(config.resolve_color("#FF0000"), Some("#FF0000"));

        // Variable shorthand
        assert_eq!(config.resolve_color("$primary"), Some("#40124A"));

        // Extended reference
        assert_eq!(config.resolve_color("$colors.secondary"), Some("#38BDA0"));

        // Unknown
        assert_eq!(config.resolve_color("$unknown"), None);
    }

    #[test]
    fn test_resolve_font() {
        let config: BrandConfig = serde_yaml::from_str(sample_yaml()).unwrap();

        assert_eq!(config.resolve_font("$heading"), "Inter-Bold");
        assert_eq!(config.resolve_font("$body"), "Inter-Regular");
        assert_eq!(config.resolve_font("Helvetica"), "Helvetica");
        assert_eq!(config.resolve_font("$unknown"), "$unknown");
    }

    #[test]
    fn test_zone_config() {
        let config: BrandConfig = serde_yaml::from_str(sample_yaml()).unwrap();

        assert_eq!(config.header.height, 0.0);
        assert!(config.header.elements.is_empty());

        assert_eq!(config.footer.height, 17.0);
        assert_eq!(config.footer.elements.len(), 1);
        assert_eq!(config.footer.elements[0].element_type, "text");
        assert_eq!(
            config.footer.elements[0].content.as_deref(),
            Some("{page}")
        );
    }

    #[test]
    fn test_stationery_config() {
        let config: BrandConfig = serde_yaml::from_str(sample_yaml()).unwrap();

        let content = config.stationery.get("content").unwrap();
        assert_eq!(content.header_footer.as_deref(), Some("content"));
        let frame = content.content_frame.as_ref().unwrap();
        assert_eq!(frame.x_pt, 90.0);
        assert_eq!(frame.height_pt, 746.0);
    }

    #[test]
    fn test_styles() {
        let config: BrandConfig = serde_yaml::from_str(sample_yaml()).unwrap();

        let normal = config.styles.get("Normal").unwrap();
        assert_eq!(normal.font_name.as_deref(), Some("Inter-Regular"));
        assert_eq!(normal.font_size, Some(9.5));
        assert_eq!(normal.text_color.as_deref(), Some("#45243D"));

        let h1 = config.styles.get("Heading1").unwrap();
        assert_eq!(h1.font_size, Some(18.0));
    }

    #[test]
    fn test_brand_loader_from_file() {
        let tmp = tempfile::tempdir().unwrap();
        let brand_path = tmp.path().join("brand.yaml");
        std::fs::write(&brand_path, sample_yaml()).unwrap();

        let tenant = TenantConfig::new(None, None);
        let loader = BrandLoader::new(tenant);
        let config = loader.load_from_file(&brand_path).unwrap();

        assert_eq!(config.brand.name, "Test Brand");
        assert_eq!(config.brand_dir, Some(tmp.path().to_path_buf()));
    }

    #[test]
    fn test_brand_loader_default_from_tenant() {
        let tmp = tempfile::tempdir().unwrap();
        let tenant_dir = tmp.path().join("my_tenant");
        std::fs::create_dir_all(&tenant_dir).unwrap();
        std::fs::write(tenant_dir.join("brand.yaml"), sample_yaml()).unwrap();

        let tenant = TenantConfig::new(Some(&tenant_dir), None);
        let loader = BrandLoader::new(tenant);
        let config = loader.load_default().unwrap();

        assert_eq!(config.brand.name, "Test Brand");
    }

    #[test]
    fn test_logo_path() {
        let tmp = tempfile::tempdir().unwrap();
        let brand_path = tmp.path().join("brand.yaml");
        std::fs::write(&brand_path, sample_yaml()).unwrap();

        let tenant = TenantConfig::new(None, None);
        let loader = BrandLoader::new(tenant);
        let config = loader.load_from_file(&brand_path).unwrap();

        let logo = config.logo_path("main").unwrap();
        assert!(logo.ends_with("logos/main.png"));
    }
}
