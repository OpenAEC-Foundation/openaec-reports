use axum::{http::StatusCode, routing::{get, post}, Json, Router};
use serde_json::{json, Value};
use std::net::SocketAddr;
use tower_http::services::{ServeDir, ServeFile};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    // SPA: serve frontend from /app/static (Docker) or ../frontend/dist (dev)
    let static_dir = std::env::var("OPENAEC_STATIC_DIR")
        .unwrap_or_else(|_| {
            // Try common paths
            for candidate in &["./static", "../frontend/dist", "/app/static"] {
                if std::path::Path::new(candidate).is_dir() {
                    return candidate.to_string();
                }
            }
            "./static".to_string()
        });

    let spa_service = ServeDir::new(&static_dir)
        .not_found_service(ServeFile::new(format!("{}/index.html", static_dir)));

    let app = Router::new()
        // API routes
        .route("/api/health", get(health))
        .route("/api/templates", get(list_templates))
        .route("/api/brands", get(list_brands))
        .route("/api/validate", post(validate))
        .route("/api/generate", post(generate))
        // Auth mock — auto-login as test user (no real auth yet)
        .route("/api/auth/me", get(auth_me))
        .route("/api/auth/login", post(auth_login))
        .route("/api/auth/logout", post(auth_logout))
        .route("/api/auth/registration-enabled", get(auth_registration))
        .route("/api/auth/oidc/config", get(auth_oidc_config))
        // SPA fallback: serve static files, index.html for unknown routes
        .fallback_service(spa_service);

    let addr = SocketAddr::from(([0, 0, 0, 0], 8001));
    tracing::info!("Rust API server listening on {}", addr);
    tracing::info!("Serving frontend from: {}", static_dir);

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

// ── Auth mock endpoints ──────────────────────────────────────────────

async fn auth_me() -> Json<Value> {
    Json(json!({
        "user": {
            "id": "rust-test-user",
            "username": "testuser",
            "email": "test@3bm.co.nl",
            "display_name": "Rust Test User",
            "role": "admin",
            "tenant": "3bm_cooperatie",
            "is_active": true,
            "company": "3BM Bouwkunde",
            "auth_provider": "local"
        }
    }))
}

async fn auth_login() -> Json<Value> {
    auth_me().await
}

async fn auth_logout() -> Json<Value> {
    Json(json!({"detail": "logged out"}))
}

async fn auth_registration() -> Json<Value> {
    Json(json!({"enabled": false}))
}

async fn auth_oidc_config() -> Json<Value> {
    Json(json!({"enabled": false}))
}

// ── Report generation ────────────────────────────────────────────────

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
