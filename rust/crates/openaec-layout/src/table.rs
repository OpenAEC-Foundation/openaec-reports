//! Table flowable — grid layout with optional headers, styling, and page splitting.

use crate::draw::DrawList;
use crate::flowable::{Flowable, LayoutContext, SplitResult};
use crate::types::{Color, Padding, Pt, Size};

/// Table cell content.
#[derive(Debug, Clone)]
pub enum CellContent {
    Text(String),
    Empty,
}

/// Table visual style.
#[derive(Debug, Clone)]
pub struct TableStyleConfig {
    pub header_background: Option<Color>,
    pub header_text_color: Color,
    pub grid_color: Color,
    pub grid_width: Pt,
    pub row_backgrounds: Vec<Option<Color>>,
    pub cell_padding: Padding,
    pub font_name: String,
    pub font_size: Pt,
    pub header_font_size: Pt,
}

impl Default for TableStyleConfig {
    fn default() -> Self {
        Self {
            header_background: Some(Color::rgb(64, 18, 74)), // 3BM purple
            header_text_color: Color::WHITE,
            grid_color: Color::rgb(200, 200, 200),
            grid_width: Pt(0.5),
            row_backgrounds: vec![None, Some(Color::rgb(245, 245, 245))],
            cell_padding: Padding::new(Pt(3.0), Pt(4.0), Pt(3.0), Pt(4.0)),
            font_name: "LiberationSans".to_string(),
            font_size: Pt(9.0),
            header_font_size: Pt(9.0),
        }
    }
}

/// Row data (pre-computed heights).
#[derive(Debug, Clone)]
struct RowLayout {
    cells: Vec<String>,
    height: Pt,
    is_header: bool,
}

/// Table flowable.
#[derive(Debug)]
pub struct Table {
    headers: Vec<String>,
    rows: Vec<Vec<String>>,
    col_widths: Option<Vec<Pt>>,
    style: TableStyleConfig,
    repeat_header: bool,
    // Computed after wrap()
    computed_col_widths: Vec<Pt>,
    row_layouts: Vec<RowLayout>,
    wrapped_height: Pt,
}

impl Table {
    pub fn new(headers: Vec<String>, rows: Vec<Vec<String>>) -> Self {
        Self {
            headers,
            rows,
            col_widths: None,
            style: TableStyleConfig::default(),
            repeat_header: true,
            computed_col_widths: Vec::new(),
            row_layouts: Vec::new(),
            wrapped_height: Pt::ZERO,
        }
    }

    pub fn with_col_widths(mut self, widths: Vec<Pt>) -> Self {
        self.col_widths = Some(widths);
        self
    }

    pub fn with_col_widths_mm(mut self, widths_mm: Vec<f64>) -> Self {
        self.col_widths = Some(
            widths_mm
                .into_iter()
                .map(|w| crate::types::Mm(w as f32).into())
                .collect(),
        );
        self
    }

    pub fn with_style(mut self, style: TableStyleConfig) -> Self {
        self.style = style;
        self
    }

    pub fn with_repeat_header(mut self, repeat: bool) -> Self {
        self.repeat_header = repeat;
        self
    }

    /// Calculate column widths (equal distribution if not specified).
    fn compute_col_widths(&self, available_width: Pt) -> Vec<Pt> {
        if let Some(ref widths) = self.col_widths {
            return widths.clone();
        }

        let num_cols = self.headers.len().max(
            self.rows
                .first()
                .map(|r| r.len())
                .unwrap_or(self.headers.len()),
        );
        if num_cols == 0 {
            return Vec::new();
        }

        let col_width = Pt(available_width.0 / num_cols as f32);
        vec![col_width; num_cols]
    }

    /// Calculate row height based on content (single line for now).
    fn row_height(&self) -> Pt {
        let padding = self.style.cell_padding.vertical();
        Pt(self.style.font_size.0 + padding.0 + 2.0)
    }

    /// Draw a single row.
    fn draw_row(
        &self,
        row: &RowLayout,
        x: Pt,
        y: Pt,
        draw_list: &mut DrawList,
        row_index: usize,
    ) {
        let bg_color = if row.is_header {
            self.style.header_background
        } else {
            let pattern_idx = row_index % self.style.row_backgrounds.len().max(1);
            self.style
                .row_backgrounds
                .get(pattern_idx)
                .cloned()
                .flatten()
        };

        // Draw row background
        if let Some(bg) = bg_color {
            draw_list.set_fill_color(bg);
            let total_width: f32 = self.computed_col_widths.iter().map(|w| w.0).sum();
            draw_list.draw_rect(x, y, Pt(total_width), row.height, true, false);
        }

        // Draw cell text
        let text_color = if row.is_header {
            self.style.header_text_color
        } else {
            Color::BLACK
        };

        let font_size = if row.is_header {
            self.style.header_font_size
        } else {
            self.style.font_size
        };

        let font_name = if row.is_header {
            format!("{}-Bold", self.style.font_name)
        } else {
            self.style.font_name.clone()
        };

        draw_list.set_font(&font_name, font_size);
        draw_list.set_fill_color(text_color);

        let text_y = Pt(y.0 + self.style.cell_padding.top.0 + font_size.0 * 0.8);
        let mut cx = x;

        for (col_idx, cell_text) in row.cells.iter().enumerate() {
            let col_width = self
                .computed_col_widths
                .get(col_idx)
                .copied()
                .unwrap_or(Pt(50.0));

            let text_x = Pt(cx.0 + self.style.cell_padding.left.0);
            draw_list.draw_text(text_x, text_y, cell_text);
            cx = Pt(cx.0 + col_width.0);
        }

        // Draw grid lines
        draw_list.set_stroke_color(self.style.grid_color);
        draw_list.set_line_width(self.style.grid_width);

        let total_width: f32 = self.computed_col_widths.iter().map(|w| w.0).sum();
        // Bottom line
        draw_list.draw_line(x, Pt(y.0 + row.height.0), Pt(x.0 + total_width), Pt(y.0 + row.height.0));

        // Vertical lines
        let mut vx = x;
        for col_width in &self.computed_col_widths {
            draw_list.draw_line(vx, y, vx, Pt(y.0 + row.height.0));
            vx = Pt(vx.0 + col_width.0);
        }
        // Right edge
        draw_list.draw_line(vx, y, vx, Pt(y.0 + row.height.0));
    }
}

impl Flowable for Table {
    fn wrap(&mut self, available_width: Pt, _available_height: Pt, _ctx: &LayoutContext) -> Size {
        self.computed_col_widths = self.compute_col_widths(available_width);
        let row_h = self.row_height();

        self.row_layouts.clear();

        // Header row
        if !self.headers.is_empty() {
            self.row_layouts.push(RowLayout {
                cells: self.headers.clone(),
                height: row_h,
                is_header: true,
            });
        }

        // Data rows
        for row in &self.rows {
            self.row_layouts.push(RowLayout {
                cells: row.clone(),
                height: row_h,
                is_header: false,
            });
        }

        self.wrapped_height = Pt(self.row_layouts.iter().map(|r| r.height.0).sum());

        Size::new(available_width, self.wrapped_height)
    }

    fn draw(&self, x: Pt, y: Pt, draw_list: &mut DrawList) {
        // Top border
        let total_width: f32 = self.computed_col_widths.iter().map(|w| w.0).sum();
        draw_list.set_stroke_color(self.style.grid_color);
        draw_list.set_line_width(self.style.grid_width);
        draw_list.draw_line(x, y, Pt(x.0 + total_width), y);

        let mut cy = y;
        let mut data_row_idx = 0;

        for row in &self.row_layouts {
            self.draw_row(row, x, cy, draw_list, data_row_idx);
            cy = Pt(cy.0 + row.height.0);
            if !row.is_header {
                data_row_idx += 1;
            }
        }
    }

    fn split(
        &self,
        available_width: Pt,
        available_height: Pt,
        ctx: &LayoutContext,
    ) -> SplitResult {
        if self.wrapped_height.0 <= available_height.0 {
            return SplitResult::Fits;
        }

        // Find how many rows fit
        let mut used_height = 0.0_f32;
        let mut split_at = 0;

        for (i, row) in self.row_layouts.iter().enumerate() {
            if used_height + row.height.0 > available_height.0 {
                split_at = i;
                break;
            }
            used_height += row.height.0;
            split_at = i + 1;
        }

        // Need at least header + 1 data row
        let min_rows = if self.headers.is_empty() { 1 } else { 2 };
        if split_at < min_rows {
            return SplitResult::CannotSplit;
        }

        // Split rows
        let first_data_rows: Vec<Vec<String>> = self.row_layouts[..split_at]
            .iter()
            .filter(|r| !r.is_header)
            .map(|r| r.cells.clone())
            .collect();

        let second_data_rows: Vec<Vec<String>> = self.row_layouts[split_at..]
            .iter()
            .filter(|r| !r.is_header)
            .map(|r| r.cells.clone())
            .collect();

        let mut first = Table::new(self.headers.clone(), first_data_rows)
            .with_style(self.style.clone());
        if let Some(ref widths) = self.col_widths {
            first = first.with_col_widths(widths.clone());
        }

        let mut second = Table::new(
            if self.repeat_header {
                self.headers.clone()
            } else {
                Vec::new()
            },
            second_data_rows,
        )
        .with_style(self.style.clone());
        if let Some(ref widths) = self.col_widths {
            second = second.with_col_widths(widths.clone());
        }

        first.wrap(available_width, Pt(f32::MAX), ctx);
        second.wrap(available_width, Pt(f32::MAX), ctx);

        SplitResult::Split(Box::new(first), Box::new(second))
    }

    fn height(&self) -> Pt {
        self.wrapped_height
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::fonts::{shared_font_registry, SharedFontRegistry};

    fn test_ctx() -> LayoutContext {
        LayoutContext {
            fonts: shared_font_registry(),
        }
    }

    #[test]
    fn test_table_wrap() {
        let mut table = Table::new(
            vec!["A".into(), "B".into(), "C".into()],
            vec![
                vec!["1".into(), "2".into(), "3".into()],
                vec!["4".into(), "5".into(), "6".into()],
            ],
        );

        let ctx = test_ctx();
        let size = table.wrap(Pt(500.0), Pt(1000.0), &ctx);

        assert!(size.height.0 > 0.0);
        assert_eq!(table.row_layouts.len(), 3); // 1 header + 2 data
    }

    #[test]
    fn test_equal_col_widths() {
        let table = Table::new(
            vec!["A".into(), "B".into()],
            vec![vec!["1".into(), "2".into()]],
        );

        let widths = table.compute_col_widths(Pt(200.0));
        assert_eq!(widths.len(), 2);
        assert!((widths[0].0 - 100.0).abs() < 0.01);
    }
}
