use axum::{http::StatusCode, routing::{get, post}, Json, Router};
use serde_json::{json, Value};
use std::net::SocketAddr;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let app = Router::new()
        .route("/api/health", get(health))
        .route("/api/templates", get(list_templates))
        .route("/api/brands", get(list_brands))
        .route("/api/validate", post(validate))
        .route("/api/generate", post(generate));

    let addr = SocketAddr::from(([0, 0, 0, 0], 8001));
    tracing::info!("Rust API server listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> Json<Value> {
    Json(json!({
        "status": "ok",
        "version": env!("CARGO_PKG_VERSION"),
        "engine": "rust"
    }))
}

async fn list_templates() -> Json<Value> {
    Json(json!({
        "templates": ["structural", "daylight", "building_code"]
    }))
}

async fn list_brands() -> Json<Value> {
    Json(json!({
        "brands": ["default"]
    }))
}

async fn validate(Json(payload): Json<Value>) -> Result<Json<Value>, (StatusCode, String)> {
    let json_str =
        serde_json::to_string(&payload).map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;

    match openaec_core::ReportData::from_json(&json_str) {
        Ok(report) => Ok(Json(json!({
            "valid": true,
            "sections": report.sections.len(),
            "template": report.template
        }))),
        Err(e) => Ok(Json(json!({
            "valid": false,
            "error": e.to_string()
        }))),
    }
}

async fn generate(Json(payload): Json<Value>) -> Result<Vec<u8>, (StatusCode, String)> {
    let json_str =
        serde_json::to_string(&payload).map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;

    let report_data = openaec_core::ReportData::from_json(&json_str)
        .map_err(|e| (StatusCode::BAD_REQUEST, format!("Invalid JSON: {}", e)))?;

    let temp_path = std::path::Path::new("temp_output.pdf");
    let pdf_bytes = openaec_core::engine::generate_pdf(&report_data, temp_path)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, format!("Generation failed: {}", e)))?;

    Ok(pdf_bytes)
}
