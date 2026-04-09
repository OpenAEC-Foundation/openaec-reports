//! Stationery merge — overlay PDF backgrounds onto generated pages.
//!
//! Uses lopdf 0.39 for post-processing (separate from printpdf's internal
//! lopdf 0.31). After printpdf generates the PDF bytes, this module:
//!
//! 1. Opens both the generated PDF and stationery PDFs with lopdf
//! 2. Converts stationery pages into Form XObjects
//! 3. Inserts them as background layers on target pages
//!
//! This approach keeps printpdf's rendering clean while adding
//! stationery as a post-processing step.

use std::collections::HashMap;
use std::path::{Path, PathBuf};

use lopdf::{Document, Object, ObjectId, Stream};

use crate::error::LayoutError;

/// Mapping from output page index (0-based) to stationery source.
#[derive(Debug, Clone)]
pub struct PageStationery {
    /// Path to the stationery PDF file.
    pub pdf_path: PathBuf,
    /// Page index within the stationery PDF (0-based).
    pub source_page: usize,
}

/// Merge stationery PDF backgrounds into an existing PDF document.
///
/// Each entry in `page_map` specifies which stationery PDF page to use
/// as background for a given output page. Pages not in the map are left
/// unchanged.
///
/// The stationery is rendered as a background layer (below content)
/// by prepending the Form XObject `Do` operator to each page's
/// content stream.
pub fn merge_stationery(
    pdf_bytes: Vec<u8>,
    page_map: &HashMap<usize, PageStationery>,
) -> Result<Vec<u8>, LayoutError> {
    if page_map.is_empty() {
        return Ok(pdf_bytes);
    }

    let mut doc = Document::load_mem(&pdf_bytes)
        .map_err(|e| LayoutError::PdfError(format!("Failed to load generated PDF: {e}")))?;

    // Cache loaded stationery documents by path
    let mut stationery_cache: HashMap<PathBuf, Document> = HashMap::new();

    // Cache imported Form XObjects: (path, source_page) → ObjectId in target doc
    let mut xobj_cache: HashMap<(PathBuf, usize), ObjectId> = HashMap::new();

    // Get page object IDs
    let page_ids: Vec<ObjectId> = doc.page_iter().collect();

    for (&target_page_idx, stationery) in page_map {
        if target_page_idx >= page_ids.len() {
            tracing::warn!(
                page = target_page_idx,
                total = page_ids.len(),
                "Stationery target page out of range, skipping"
            );
            continue;
        }

        // Load stationery PDF if not cached
        if !stationery_cache.contains_key(&stationery.pdf_path) {
            let stat_doc = load_stationery_pdf(&stationery.pdf_path)?;
            stationery_cache.insert(stationery.pdf_path.clone(), stat_doc);
        }

        // Get or create the Form XObject for this stationery page
        let cache_key = (stationery.pdf_path.clone(), stationery.source_page);
        let xobj_id = if let Some(&id) = xobj_cache.get(&cache_key) {
            id
        } else {
            let stat_doc = stationery_cache.get(&stationery.pdf_path).unwrap();
            let id = import_page_as_xobject(&mut doc, stat_doc, stationery.source_page)?;
            xobj_cache.insert(cache_key, id);
            id
        };

        // Add the XObject to the target page and prepend it to content
        let page_id = page_ids[target_page_idx];
        apply_stationery_to_page(&mut doc, page_id, xobj_id, target_page_idx)?;
    }

    // Write result
    let mut output = Vec::new();
    doc.save_to(&mut output)
        .map_err(|e| LayoutError::PdfError(format!("Failed to save merged PDF: {e}")))?;

    Ok(output)
}

/// Load a stationery PDF from disk.
fn load_stationery_pdf(path: &Path) -> Result<Document, LayoutError> {
    if !path.exists() {
        return Err(LayoutError::PdfError(format!(
            "Stationery file not found: {}",
            path.display()
        )));
    }

    Document::load(path)
        .map_err(|e| LayoutError::PdfError(format!(
            "Failed to load stationery PDF '{}': {e}",
            path.display()
        )))
}

/// Import a page from a stationery PDF as a Form XObject into the target document.
///
/// Returns the ObjectId of the new Form XObject in the target document.
fn import_page_as_xobject(
    target: &mut Document,
    source: &Document,
    page_index: usize,
) -> Result<ObjectId, LayoutError> {
    let source_pages: Vec<ObjectId> = source.page_iter().collect();

    if page_index >= source_pages.len() {
        return Err(LayoutError::PdfError(format!(
            "Stationery page index {} out of range (has {} pages)",
            page_index,
            source_pages.len()
        )));
    }

    let page_id = source_pages[page_index];
    // Verify page exists in source
    let _page_obj = source
        .get_object(page_id)
        .map_err(|e| LayoutError::PdfError(format!("Failed to get stationery page object: {e}")))?;

    // Get MediaBox from the stationery page
    let media_box = get_page_media_box(source, page_id)?;

    // Collect the page's content stream(s)
    let content_data = collect_page_content(source, page_id)?;

    // Collect page resources
    let resources = get_page_resources(source, page_id, target)?;

    // Build the Form XObject stream
    let mut xobj_dict = lopdf::Dictionary::new();
    xobj_dict.set("Type", Object::Name(b"XObject".to_vec()));
    xobj_dict.set("Subtype", Object::Name(b"Form".to_vec()));
    xobj_dict.set("FormType", Object::Integer(1));
    xobj_dict.set("BBox", media_box);
    xobj_dict.set("Resources", resources);

    // Create stream with content data
    let xobj_stream = Stream::new(xobj_dict, content_data);

    // Add to target document
    let xobj_id = target.add_object(Object::Stream(xobj_stream));

    Ok(xobj_id)
}

/// Get the MediaBox array from a page object (walks up to parent if needed).
fn get_page_media_box(doc: &Document, page_id: ObjectId) -> Result<Object, LayoutError> {
    let page = doc
        .get_object(page_id)
        .map_err(|e| LayoutError::PdfError(format!("Failed to get page: {e}")))?;

    if let Ok(dict) = page.as_dict() {
        // Try direct MediaBox first
        if let Ok(mb) = dict.get(b"MediaBox") {
            return Ok(deep_clone_object(doc, mb));
        }
        // Walk up to parent
        if let Ok(parent_ref) = dict.get(b"Parent") {
            if let Ok(parent_id) = parent_ref.as_reference() {
                return get_page_media_box(doc, parent_id);
            }
        }
    }

    // Default A4 MediaBox
    Ok(Object::Array(vec![
        Object::Integer(0),
        Object::Integer(0),
        Object::Real(595.28),
        Object::Real(841.89),
    ]))
}

/// Collect all content streams from a page into a single byte buffer.
fn collect_page_content(doc: &Document, page_id: ObjectId) -> Result<Vec<u8>, LayoutError> {
    let page = doc
        .get_object(page_id)
        .map_err(|e| LayoutError::PdfError(format!("Failed to get page for content: {e}")))?;

    let dict = page
        .as_dict()
        .map_err(|_| LayoutError::PdfError("Page is not a dictionary".to_string()))?;

    let contents = match dict.get(b"Contents") {
        Ok(c) => c,
        Err(_) => return Ok(Vec::new()), // No content
    };

    collect_content_streams(doc, contents)
}

/// Recursively collect content stream bytes from a Contents entry.
fn collect_content_streams(doc: &Document, obj: &Object) -> Result<Vec<u8>, LayoutError> {
    match obj {
        Object::Reference(id) => {
            let resolved = doc
                .get_object(*id)
                .map_err(|e| LayoutError::PdfError(format!("Failed to resolve content ref: {e}")))?;
            collect_content_streams(doc, resolved)
        }
        Object::Stream(stream) => {
            let data = stream.decompressed_content()
                .unwrap_or_else(|_| stream.content.clone());
            Ok(data)
        }
        Object::Array(arr) => {
            let mut result = Vec::new();
            for item in arr {
                let chunk = collect_content_streams(doc, item)?;
                if !result.is_empty() && !chunk.is_empty() {
                    result.push(b'\n');
                }
                result.extend_from_slice(&chunk);
            }
            Ok(result)
        }
        _ => Ok(Vec::new()),
    }
}

/// Get the Resources dictionary from a page, importing referenced objects into target.
fn get_page_resources(
    source: &Document,
    page_id: ObjectId,
    target: &mut Document,
) -> Result<Object, LayoutError> {
    let page = source
        .get_object(page_id)
        .map_err(|e| LayoutError::PdfError(format!("Failed to get page for resources: {e}")))?;

    let dict = page
        .as_dict()
        .map_err(|_| LayoutError::PdfError("Page is not a dictionary".to_string()))?;

    match dict.get(b"Resources") {
        Ok(res) => {
            // Deep-clone and import all referenced objects into target
            Ok(deep_import_object(source, target, res))
        }
        Err(_) => {
            // Walk up to parent
            if let Ok(parent_ref) = dict.get(b"Parent") {
                if let Ok(parent_id) = parent_ref.as_reference() {
                    return get_page_resources(source, parent_id, target);
                }
            }
            // Empty resources
            Ok(Object::Dictionary(lopdf::Dictionary::new()))
        }
    }
}

/// Deep-clone an object from source document, importing all referenced objects
/// into the target document.
fn deep_import_object(source: &Document, target: &mut Document, obj: &Object) -> Object {
    match obj {
        Object::Reference(id) => {
            // Resolve in source, import recursively, add to target
            if let Ok(resolved) = source.get_object(*id) {
                let imported = deep_import_object(source, target, resolved);
                let new_id = target.add_object(imported);
                Object::Reference(new_id)
            } else {
                Object::Null
            }
        }
        Object::Dictionary(dict) => {
            let mut new_dict = lopdf::Dictionary::new();
            for (key, value) in dict.iter() {
                new_dict.set(key.clone(), deep_import_object(source, target, value));
            }
            Object::Dictionary(new_dict)
        }
        Object::Array(arr) => {
            Object::Array(
                arr.iter()
                    .map(|item| deep_import_object(source, target, item))
                    .collect(),
            )
        }
        Object::Stream(stream) => {
            let new_dict = if let Object::Dictionary(d) =
                deep_import_object(source, target, &Object::Dictionary(stream.dict.clone()))
            {
                d
            } else {
                lopdf::Dictionary::new()
            };
            Object::Stream(Stream::new(new_dict, stream.content.clone()))
        }
        // Value types: clone directly
        other => other.clone(),
    }
}

/// Deep-clone an object within the same document (no cross-document import).
fn deep_clone_object(doc: &Document, obj: &Object) -> Object {
    match obj {
        Object::Reference(id) => {
            if let Ok(resolved) = doc.get_object(*id) {
                deep_clone_object(doc, resolved)
            } else {
                Object::Null
            }
        }
        Object::Array(arr) => {
            Object::Array(arr.iter().map(|item| deep_clone_object(doc, item)).collect())
        }
        other => other.clone(),
    }
}

/// Apply a stationery Form XObject as background to a target page.
///
/// This adds the XObject to the page's Resources/XObject dictionary
/// and prepends a `Do` operator to the content stream so it renders
/// behind existing content.
fn apply_stationery_to_page(
    doc: &mut Document,
    page_id: ObjectId,
    xobj_id: ObjectId,
    page_index: usize,
) -> Result<(), LayoutError> {
    let xobj_name = format!("Stat{}", page_index);
    let xobj_name_bytes = xobj_name.as_bytes().to_vec();

    // Step 1: Add XObject reference to page Resources
    {
        let page_obj = doc
            .get_object_mut(page_id)
            .map_err(|e| LayoutError::PdfError(format!("Failed to get mutable page: {e}")))?;

        let page_dict = page_obj
            .as_dict_mut()
            .map_err(|_| LayoutError::PdfError("Page is not a dict".to_string()))?;

        // Ensure Resources exists
        if page_dict.get(b"Resources").is_err() {
            page_dict.set("Resources", Object::Dictionary(lopdf::Dictionary::new()));
        }

        let resources = page_dict
            .get_mut(b"Resources")
            .map_err(|e| LayoutError::PdfError(format!("Failed to get Resources: {e}")))?;

        let res_dict = match resources {
            Object::Dictionary(d) => d,
            _ => {
                return Err(LayoutError::PdfError(
                    "Resources is not a dictionary".to_string(),
                ));
            }
        };

        // Ensure XObject sub-dictionary exists
        if res_dict.get(b"XObject").is_err() {
            res_dict.set("XObject", Object::Dictionary(lopdf::Dictionary::new()));
        }

        let xobjects = res_dict
            .get_mut(b"XObject")
            .map_err(|e| LayoutError::PdfError(format!("Failed to get XObject dict: {e}")))?;

        let xobj_dict = match xobjects {
            Object::Dictionary(d) => d,
            _ => {
                return Err(LayoutError::PdfError(
                    "XObject is not a dictionary".to_string(),
                ));
            }
        };

        xobj_dict.set(xobj_name_bytes.clone(), Object::Reference(xobj_id));
    }

    // Step 2: Prepend the Do operator to the page's content stream
    // We wrap existing content in q/Q (save/restore) and prepend the stationery
    let prepend_ops = format!("q /{} Do Q\n", xobj_name);
    let prepend_bytes = prepend_ops.into_bytes();

    let page_obj = doc
        .get_object(page_id)
        .map_err(|e| LayoutError::PdfError(format!("Failed to get page: {e}")))?
        .clone();

    let page_dict = page_obj
        .as_dict()
        .map_err(|_| LayoutError::PdfError("Page is not a dict".to_string()))?;

    // Get existing Contents
    match page_dict.get(b"Contents") {
        Ok(contents) => {
            // Collect existing content bytes
            let existing_content = collect_content_streams(doc, contents)?;

            // Create new combined stream: stationery + q/Q wrapped original
            let mut combined = prepend_bytes;
            combined.extend_from_slice(b"q\n");
            combined.extend_from_slice(&existing_content);
            combined.extend_from_slice(b"\nQ\n");

            let new_stream = Stream::new(lopdf::Dictionary::new(), combined);
            let new_stream_id = doc.add_object(Object::Stream(new_stream));

            // Update page's Contents to point to new stream
            let page_mut = doc
                .get_object_mut(page_id)
                .map_err(|e| LayoutError::PdfError(format!("Failed to get mutable page: {e}")))?;
            let page_dict_mut = page_mut.as_dict_mut().unwrap();
            page_dict_mut.set("Contents", Object::Reference(new_stream_id));
        }
        Err(_) => {
            // No existing content — just add the stationery
            let content = format!("q /{} Do Q\n", xobj_name).into_bytes();
            let stream = Stream::new(lopdf::Dictionary::new(), content);
            let stream_id = doc.add_object(Object::Stream(stream));

            let page_mut = doc
                .get_object_mut(page_id)
                .map_err(|e| LayoutError::PdfError(format!("Failed to get mutable page: {e}")))?;
            let page_dict_mut = page_mut.as_dict_mut().unwrap();
            page_dict_mut.set("Contents", Object::Reference(stream_id));
        }
    }

    Ok(())
}

/// Add PDF bookmarks (outlines) to a document.
///
/// Each bookmark entry specifies a title, nesting level, and target page.
/// This creates the /Outlines dictionary in the PDF catalog.
pub fn add_bookmarks(
    pdf_bytes: Vec<u8>,
    bookmarks: &[BookmarkEntry],
) -> Result<Vec<u8>, LayoutError> {
    if bookmarks.is_empty() {
        return Ok(pdf_bytes);
    }

    let mut doc = Document::load_mem(&pdf_bytes)
        .map_err(|e| LayoutError::PdfError(format!("Failed to load PDF for bookmarks: {e}")))?;

    let page_ids: Vec<ObjectId> = doc.page_iter().collect();
    if page_ids.is_empty() {
        return Ok(pdf_bytes);
    }

    // Create outline items (flat list with hierarchy via First/Last/Parent/Next/Prev)
    let mut outline_items: Vec<(ObjectId, i64)> = Vec::new();

    for bm in bookmarks {
        let target_page = bm.page.min(page_ids.len().saturating_sub(1));
        let page_id = page_ids[target_page];

        let mut item_dict = lopdf::Dictionary::new();
        item_dict.set("Title", Object::String(
            bm.title.as_bytes().to_vec(),
            lopdf::StringFormat::Literal,
        ));
        // Destination: [page /Fit]
        item_dict.set("Dest", Object::Array(vec![
            Object::Reference(page_id),
            Object::Name(b"Fit".to_vec()),
        ]));

        let item_id = doc.add_object(Object::Dictionary(item_dict));
        outline_items.push((item_id, bm.level as i64));
    }

    if outline_items.is_empty() {
        return save_doc(doc);
    }

    // Build the outline tree — connect siblings via Next/Prev
    // For simplicity, we build a flat list under the root
    let root_dict = {
        let mut d = lopdf::Dictionary::new();
        d.set("Type", Object::Name(b"Outlines".to_vec()));

        let first_id = outline_items[0].0;
        let last_id = outline_items[outline_items.len() - 1].0;
        d.set("First", Object::Reference(first_id));
        d.set("Last", Object::Reference(last_id));
        d.set("Count", Object::Integer(outline_items.len() as i64));
        d
    };

    let outlines_id = doc.add_object(Object::Dictionary(root_dict));

    // Set Parent/Next/Prev on each item
    for i in 0..outline_items.len() {
        let (item_id, _level) = outline_items[i];
        let item = doc.get_object_mut(item_id).unwrap();
        let dict = item.as_dict_mut().unwrap();

        dict.set("Parent", Object::Reference(outlines_id));

        if i + 1 < outline_items.len() {
            dict.set("Next", Object::Reference(outline_items[i + 1].0));
        }
        if i > 0 {
            dict.set("Prev", Object::Reference(outline_items[i - 1].0));
        }
    }

    // Add Outlines to the catalog
    // lopdf 0.39: catalog() returns &Dictionary, we need the trailer Root ref
    let catalog_ref = doc
        .trailer
        .get(b"Root")
        .ok()
        .and_then(|r| r.as_reference().ok())
        .ok_or_else(|| LayoutError::PdfError("No Root in trailer".to_string()))?;

    let catalog_obj = doc
        .get_object_mut(catalog_ref)
        .map_err(|e| LayoutError::PdfError(format!("Failed to get mutable catalog: {e}")))?;
    let catalog_dict = catalog_obj
        .as_dict_mut()
        .map_err(|_| LayoutError::PdfError("Catalog is not a dict".to_string()))?;

    catalog_dict.set("Outlines", Object::Reference(outlines_id));
    catalog_dict.set("PageMode", Object::Name(b"UseOutlines".to_vec()));

    save_doc(doc)
}

/// A bookmark entry for the PDF outline tree.
#[derive(Debug, Clone)]
pub struct BookmarkEntry {
    /// Display title.
    pub title: String,
    /// Nesting level (0 = top-level chapter).
    pub level: usize,
    /// Target page index (0-based).
    pub page: usize,
}

/// Save document to bytes.
fn save_doc(mut doc: Document) -> Result<Vec<u8>, LayoutError> {
    // Compress streams for smaller output
    doc.compress();

    let mut output = Vec::new();
    doc.save_to(&mut output)
        .map_err(|e| LayoutError::PdfError(format!("Failed to save PDF: {e}")))?;
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_merge_stationery_empty_map() {
        let fake_pdf = create_minimal_pdf();
        let result = merge_stationery(fake_pdf.clone(), &HashMap::new()).unwrap();
        // Should return unchanged
        assert_eq!(result, fake_pdf);
    }

    #[test]
    fn test_bookmark_entry_creation() {
        let bm = BookmarkEntry {
            title: "Chapter 1".to_string(),
            level: 0,
            page: 2,
        };
        assert_eq!(bm.title, "Chapter 1");
        assert_eq!(bm.page, 2);
    }

    #[test]
    fn test_add_bookmarks_empty() {
        let pdf = create_minimal_pdf();
        let result = add_bookmarks(pdf.clone(), &[]).unwrap();
        assert_eq!(result, pdf);
    }

    #[test]
    fn test_add_bookmarks_to_pdf() {
        let pdf = create_minimal_pdf();
        let bookmarks = vec![
            BookmarkEntry {
                title: "Chapter 1".to_string(),
                level: 0,
                page: 0,
            },
            BookmarkEntry {
                title: "Chapter 2".to_string(),
                level: 0,
                page: 0,
            },
        ];
        let result = add_bookmarks(pdf, &bookmarks).unwrap();
        // Should be a valid PDF with bookmarks
        let doc = Document::load_mem(&result).unwrap();
        let catalog = doc.catalog().unwrap();
        assert!(catalog.get(b"Outlines").is_ok());
    }

    /// Create a minimal valid PDF for testing.
    fn create_minimal_pdf() -> Vec<u8> {
        let (doc, _page, _layer) =
            printpdf::PdfDocument::new("Test", printpdf::Mm(210.0), printpdf::Mm(297.0), "Layer1");
        let mut buf = std::io::BufWriter::new(Vec::new());
        doc.save(&mut buf).unwrap();
        buf.into_inner().unwrap()
    }
}
