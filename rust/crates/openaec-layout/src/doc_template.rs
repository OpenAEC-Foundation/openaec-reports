//! DocTemplate — multi-page PDF assembly.
//!
//! Takes flowables, lays them out across pages using PageTemplates,
//! and renders the result to PDF via printpdf.

use std::path::Path;

use crate::draw::{DrawList, DrawOp};
use crate::error::LayoutError;
use crate::flowable::{Flowable, LayoutContext};
use crate::fonts::SharedFontRegistry;
use crate::page_template::PageTemplate;
use crate::types::{Pt, Size};

/// Helper: convert our Pt to printpdf Mm.
fn to_pdf_mm(pt: Pt) -> printpdf::Mm {
    let mm: crate::types::Mm = pt.into();
    printpdf::Mm(mm.0)
}

/// A rendered page (draw list + size).
#[derive(Debug)]
struct RenderedPage {
    draw_list: DrawList,
    page_size: Size,
    template_name: String,
}

/// A pre-rendered page (canvas-drawn, not flowable-based).
/// Used for cover, colofon, TOC, backcover etc.
#[derive(Debug, Clone)]
pub struct RawPage {
    pub page_size: Size,
    pub draw_list: DrawList,
}

/// Document template — the top-level layout engine.
pub struct DocTemplate {
    page_templates: Vec<PageTemplate>,
    fonts: SharedFontRegistry,
    title: String,
    /// Pages prepended before content (cover, colofon, TOC).
    pre_pages: Vec<RawPage>,
    /// Pages appended after content (backcover).
    post_pages: Vec<RawPage>,
}

impl DocTemplate {
    pub fn new(title: impl Into<String>, fonts: SharedFontRegistry) -> Self {
        Self {
            page_templates: Vec::new(),
            fonts,
            title: title.into(),
            pre_pages: Vec::new(),
            post_pages: Vec::new(),
        }
    }

    /// Add a page template. The first one added is the default.
    pub fn add_page_template(&mut self, template: PageTemplate) {
        self.page_templates.push(template);
    }

    /// Add a pre-rendered page before the content (e.g., cover, colofon, TOC).
    pub fn add_pre_page(&mut self, page: RawPage) {
        self.pre_pages.push(page);
    }

    /// Add a pre-rendered page after the content (e.g., backcover).
    pub fn add_post_page(&mut self, page: RawPage) {
        self.post_pages.push(page);
    }

    /// Get page template by name, or the first one as default.
    fn get_template(&self, _name: Option<&str>) -> &PageTemplate {
        // For now, always return the first template.
        // TODO: support named template selection.
        &self.page_templates[0]
    }

    /// Build the document from flowables and write to a file.
    pub fn build(
        &self,
        flowables: Vec<Box<dyn Flowable>>,
        output: &Path,
    ) -> Result<(), LayoutError> {
        let pdf_bytes = self.build_to_bytes(flowables)?;
        std::fs::write(output, pdf_bytes)?;
        Ok(())
    }

    /// Build the document from flowables and return PDF bytes.
    pub fn build_to_bytes(
        &self,
        flowables: Vec<Box<dyn Flowable>>,
    ) -> Result<Vec<u8>, LayoutError> {
        if self.page_templates.is_empty() {
            return Err(LayoutError::PdfError(
                "No page templates defined".to_string(),
            ));
        }

        let ctx = LayoutContext {
            fonts: self.fonts.clone(),
        };

        // Phase 1: Build pre-pages
        let pre: Vec<RenderedPage> = self
            .pre_pages
            .iter()
            .map(|rp| RenderedPage {
                draw_list: rp.draw_list.clone(),
                page_size: rp.page_size,
                template_name: "raw".to_string(),
            })
            .collect();

        // Phase 2: Layout content flowables across pages
        let content = self.layout_pages(flowables, &ctx);

        // Phase 3: Build post-pages
        let post: Vec<RenderedPage> = self
            .post_pages
            .iter()
            .map(|rp| RenderedPage {
                draw_list: rp.draw_list.clone(),
                page_size: rp.page_size,
                template_name: "raw".to_string(),
            })
            .collect();

        // Combine all pages
        let mut all_pages = pre;
        all_pages.extend(content);
        all_pages.extend(post);

        // Phase 4: Render to PDF
        self.render_pdf(&all_pages)
    }

    /// Layout flowables across pages, returning rendered pages.
    fn layout_pages(
        &self,
        mut flowables: Vec<Box<dyn Flowable>>,
        ctx: &LayoutContext,
    ) -> Vec<RenderedPage> {
        let mut pages = Vec::new();
        let mut idx = 0;

        while idx < flowables.len() {
            let template = self.get_template(None);
            let frame = template.primary_frame();
            let inner_w = frame.inner_width();
            let inner_h = frame.inner_height();
            let start_x = Pt(frame.rect.x.0 + frame.padding.left.0);
            let start_y = Pt(frame.rect.y.0 + frame.padding.top.0);

            let mut draw_list = DrawList::new();
            let mut cursor_y = Pt(0.0);

            while idx < flowables.len() {
                let flowable = &mut flowables[idx];

                if flowable.is_page_break() {
                    idx += 1;
                    break;
                }

                let remaining = Pt(inner_h.0 - cursor_y.0);
                let size = flowable.wrap(inner_w, remaining, ctx);

                if size.height.0 <= remaining.0 || cursor_y.0 == 0.0 {
                    // Fits, or first item on page (force draw even if too tall)
                    flowable.draw(start_x, Pt(start_y.0 + cursor_y.0), &mut draw_list);
                    cursor_y = Pt(cursor_y.0 + size.height.0);
                    idx += 1;
                } else {
                    // Doesn't fit — new page
                    break;
                }
            }

            // Don't run callbacks in first pass — we need total page count.
            pages.push(RenderedPage {
                draw_list,
                page_size: template.page_size,
                template_name: template.name.clone(),
            });
        }

        // Single pass: run callbacks with correct total page count
        let total_pages = pages.len();
        for (i, page) in pages.iter_mut().enumerate() {
            if let Some(template) = self
                .page_templates
                .iter()
                .find(|t| t.name == page.template_name)
                && let Some(ref callback) = template.on_page
            {
                callback.on_page(&mut page.draw_list, i + 1, total_pages, page.page_size);
            }
        }

        pages
    }

    /// Render pages to PDF bytes using printpdf.
    fn render_pdf(&self, pages: &[RenderedPage]) -> Result<Vec<u8>, LayoutError> {
        if pages.is_empty() {
            return Err(LayoutError::PdfError("No pages to render".to_string()));
        }

        let first_page = &pages[0];
        let (doc, first_page_idx, first_layer_idx) = printpdf::PdfDocument::new(
            &self.title,
            to_pdf_mm(first_page.page_size.width),
            to_pdf_mm(first_page.page_size.height),
            "Content",
        );

        // Register fonts with printpdf
        let fonts_guard = self.fonts.lock().unwrap();
        let mut pdf_fonts: std::collections::HashMap<String, printpdf::IndirectFontRef> =
            std::collections::HashMap::new();

        for (name, font_id) in fonts_guard.iter() {
            let font_data = fonts_guard.font_data(font_id);
            match doc.add_external_font(font_data) {
                Ok(font_ref) => {
                    pdf_fonts.insert(name.to_string(), font_ref);
                }
                Err(e) => {
                    tracing::warn!("Failed to register font '{}': {}", name, e);
                }
            }
        }
        drop(fonts_guard);

        // Render each page
        for (page_idx, rendered_page) in pages.iter().enumerate() {
            let (page_ref, layer_ref) = if page_idx == 0 {
                (first_page_idx, first_layer_idx)
            } else {
                doc.add_page(
                    to_pdf_mm(rendered_page.page_size.width),
                    to_pdf_mm(rendered_page.page_size.height),
                    "Content",
                )
            };

            let layer = doc.get_page(page_ref).get_layer(layer_ref);
            self.render_draw_list(&layer, &rendered_page.draw_list, rendered_page.page_size.height, &pdf_fonts);
        }

        // Save to bytes
        let mut buf = std::io::BufWriter::new(Vec::new());
        doc.save(&mut buf)
            .map_err(|e| LayoutError::PdfError(e.to_string()))?;

        buf.into_inner()
            .map_err(|e| LayoutError::PdfError(e.to_string()))
    }

    /// Render a draw list to a printpdf layer.
    fn render_draw_list(
        &self,
        layer: &printpdf::PdfLayerReference,
        draw_list: &DrawList,
        page_height: Pt,
        fonts: &std::collections::HashMap<String, printpdf::IndirectFontRef>,
    ) {
        let mut current_font: Option<&printpdf::IndirectFontRef> = None;
        let mut current_font_size: f32 = 10.0;

        for op in &draw_list.ops {
            match op {
                DrawOp::SetFont { name, size } => {
                    current_font_size = size.0;
                    current_font = fonts.get(name.as_str())
                        .or_else(|| {
                            // Fallback 1: try with -Regular suffix
                            fonts.get(&format!("{}-Regular", name))
                        })
                        .or_else(|| {
                            // Fallback 2: try base name without variant suffix
                            let base = name.split('-').next().unwrap_or(name);
                            fonts.get(base)
                                .or_else(|| fonts.get(&format!("{}-Regular", base)))
                        });
                    if current_font.is_none() {
                        tracing::warn!(font = %name, "Font not found, text will be invisible");
                    }
                }

                DrawOp::DrawText { x, y, text }
                | DrawOp::DrawTextRight { x, y, text }
                | DrawOp::DrawTextCenter { x, y, text } => {
                    if let Some(font) = current_font {
                        let pdf_y = page_height.0 - y.0;
                        layer.begin_text_section();
                        layer.set_font(font, current_font_size);
                        layer.set_text_cursor(to_pdf_mm(*x), to_pdf_mm(Pt(pdf_y)));
                        layer.write_text(text, font);
                        layer.end_text_section();
                    }
                }

                DrawOp::SetFillColor(color) => {
                    let (r, g, b) = color.to_pdf_rgb();
                    layer.set_fill_color(printpdf::Color::Rgb(printpdf::Rgb::new(
                        r, g, b, None,
                    )));
                }

                DrawOp::SetStrokeColor(color) => {
                    let (r, g, b) = color.to_pdf_rgb();
                    layer.set_outline_color(printpdf::Color::Rgb(printpdf::Rgb::new(
                        r, g, b, None,
                    )));
                }

                DrawOp::SetLineWidth(width) => {
                    layer.set_outline_thickness(width.0);
                }

                DrawOp::DrawRect {
                    x,
                    y,
                    width,
                    height,
                    fill,
                    stroke,
                } => {
                    let pdf_y = Pt(page_height.0 - y.0 - height.0);
                    let mode = match (fill, stroke) {
                        (true, true) => printpdf::path::PaintMode::FillStroke,
                        (true, false) => printpdf::path::PaintMode::Fill,
                        (false, true) => printpdf::path::PaintMode::Stroke,
                        (false, false) => continue, // nothing to draw
                    };
                    let ring = vec![
                        (printpdf::Point::new(to_pdf_mm(*x), to_pdf_mm(pdf_y)), false),
                        (printpdf::Point::new(to_pdf_mm(Pt(x.0 + width.0)), to_pdf_mm(pdf_y)), false),
                        (printpdf::Point::new(to_pdf_mm(Pt(x.0 + width.0)), to_pdf_mm(Pt(pdf_y.0 + height.0))), false),
                        (printpdf::Point::new(to_pdf_mm(*x), to_pdf_mm(Pt(pdf_y.0 + height.0))), false),
                    ];
                    let polygon = printpdf::Polygon {
                        rings: vec![ring],
                        mode,
                        winding_order: printpdf::path::WindingOrder::NonZero,
                    };
                    layer.add_polygon(polygon);
                }

                DrawOp::DrawLine { x1, y1, x2, y2 } => {
                    let pdf_y1 = page_height.0 - y1.0;
                    let pdf_y2 = page_height.0 - y2.0;

                    let points = vec![
                        (
                            printpdf::Point::new(
                                to_pdf_mm(*x1),
                                to_pdf_mm(Pt(pdf_y1)),
                            ),
                            false,
                        ),
                        (
                            printpdf::Point::new(
                                to_pdf_mm(*x2),
                                to_pdf_mm(Pt(pdf_y2)),
                            ),
                            false,
                        ),
                    ];

                    let line = printpdf::Line {
                        points,
                        is_closed: false,
                    };
                    layer.add_line(line);
                }

                DrawOp::DrawImage {
                    data,
                    x,
                    y,
                    width,
                    height,
                } => {
                    if let Ok(dynamic_img) = ::image::load_from_memory(data) {
                        let (img_w, img_h) = (
                            dynamic_img.width() as f32,
                            dynamic_img.height() as f32,
                        );
                        // Convert to raw RGB pixels for printpdf
                        let rgb = dynamic_img.to_rgb8();
                        let raw_pixels = rgb.into_raw();
                        let image_xobj = printpdf::ImageXObject {
                            width: printpdf::Px(img_w as usize),
                            height: printpdf::Px(img_h as usize),
                            color_space: printpdf::ColorSpace::Rgb,
                            bits_per_component: printpdf::ColorBits::Bit8,
                            interpolate: true,
                            image_data: raw_pixels,
                            image_filter: None,
                            smask: None,
                            clipping_bbox: None,
                        };
                        let pdf_image = printpdf::Image::from(image_xobj);
                        let pdf_y = Pt(page_height.0 - y.0 - height.0);
                        let transform = printpdf::ImageTransform {
                            translate_x: Some(to_pdf_mm(*x)),
                            translate_y: Some(to_pdf_mm(pdf_y)),
                            scale_x: Some(width.0 / img_w),
                            scale_y: Some(height.0 / img_h),
                            ..Default::default()
                        };
                        pdf_image.add_to_layer(layer.clone(), transform);
                    }
                }

                DrawOp::SaveState => {
                    layer.save_graphics_state();
                }
                DrawOp::RestoreState => {
                    layer.restore_graphics_state();
                }
            }
        }
    }
}
