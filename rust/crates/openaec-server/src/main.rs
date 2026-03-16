use axum::{
    extract::Path as AxumPath,
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use serde_json::{json, Value};
use std::net::SocketAddr;
use std::path::PathBuf;
use tower_http::services::{ServeDir, ServeFile};

use openaec_core::template_loader::TemplateLoader;
use openaec_core::tenant::TenantConfig;

/// Build a `TenantConfig` from environment variables.
fn tenant_config() -> TenantConfig {
    TenantConfig::new(None, None)
}

/// Build a `TemplateLoader` for the active tenant.
fn template_loader() -> TemplateLoader {
    let tc = tenant_config();
    let dirs = tc.templates_dirs();
    if dirs.is_empty() {
        tracing::warn!("No template directories found");
        TemplateLoader::new(PathBuf::from("/app/tenants/default/templates"))
    } else {
        TemplateLoader::with_dirs(dirs)
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    // SPA: serve frontend from /app/static (Docker) or ../frontend/dist (dev)
    let static_dir = std::env::var("OPENAEC_STATIC_DIR").unwrap_or_else(|_| {
        for candidate in &["./static", "../frontend/dist", "/app/static"] {
            if std::path::Path::new(candidate).is_dir() {
                return candidate.to_string();
            }
        }
        "./static".to_string()
    });

    let spa_service = ServeDir::new(&static_dir)
        .not_found_service(ServeFile::new(format!("{}/index.html", static_dir)));

    // Log tenant info at startup
    let tc = tenant_config();
    if let Some(td) = tc.tenant_dir() {
        tracing::info!("Active tenant: {}", td.display());
    }
    if let Some(tr) = tc.tenants_root() {
        tracing::info!("Tenants root: {}", tr.display());
    }
    let loader = template_loader();
    let templates = loader.list_templates();
    tracing::info!("Loaded {} templates", templates.len());

    let app = Router::new()
        // API routes
        .route("/api/health", get(health))
        .route("/api/templates", get(list_templates))
        .route("/api/templates/{name}/scaffold", get(get_scaffold))
        .route("/api/brands", get(list_brands))
        .route("/api/stationery", get(list_stationery))
        .route("/api/admin/tenants", get(list_tenants))
        .route(
            "/api/admin/tenants/{tenant}/templates",
            get(list_tenant_templates),
        )
        .route(
            "/api/admin/tenants/{tenant}/brand",
            get(get_tenant_brand),
        )
        .route("/api/validate", post(validate))
        .route("/api/generate", post(generate))
        // Auth mock — auto-login as test user (no real auth yet)
        .route("/api/auth/me", get(auth_me))
        .route("/api/auth/login", post(auth_login))
        .route("/api/auth/logout", post(auth_logout))
        .route("/api/auth/registration-enabled", get(auth_registration))
        .route("/api/auth/oidc/config", get(auth_oidc_config))
        // SPA fallback
        .fallback_service(spa_service);

    let addr = SocketAddr::from(([0, 0, 0, 0], 8001));
    tracing::info!("Rust API server listening on {}", addr);
    tracing::info!("Serving frontend from: {}", static_dir);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

// ── Health ──────────────────────────────────────────────────────────

async fn health() -> Json<Value> {
    Json(json!({
        "status": "ok",
        "version": env!("CARGO_PKG_VERSION"),
        "engine": "rust"
    }))
}

// ── Templates ───────────────────────────────────────────────────────

async fn list_templates() -> Json<Value> {
    let loader = template_loader();
    let templates: Vec<Value> = loader
        .list_templates()
        .into_iter()
        .map(|t| {
            json!({
                "name": t.name,
                "report_type": t.report_type,
            })
        })
        .collect();

    Json(json!({ "templates": templates }))
}

async fn get_scaffold(
    AxumPath(name): AxumPath<String>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let loader = template_loader();
    match loader.to_scaffold(&name) {
        Ok(scaffold) => Ok(Json(scaffold)),
        Err(e) => Err((StatusCode::NOT_FOUND, e.to_string())),
    }
}

// ── Brands ──────────────────────────────────────────────────────────

async fn list_brands() -> Json<Value> {
    let tc = tenant_config();
    let mut brands = Vec::new();

    // Active tenant brand
    if let Some(td) = tc.tenant_dir() {
        let brand_path = td.join("brand.yaml");
        if brand_path.is_file() {
            let name = td
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("default");
            brands.push(json!({
                "name": name.replace('_', " "),
                "slug": name,
            }));
        }
    }

    // All tenants in tenants_root
    if let Some(root) = tc.tenants_root() {
        if let Ok(entries) = std::fs::read_dir(root) {
            let mut tenant_names: Vec<String> = entries
                .flatten()
                .filter(|e| e.path().is_dir() && e.path().join("brand.yaml").is_file())
                .filter_map(|e| e.file_name().to_str().map(|s| s.to_string()))
                .collect();
            tenant_names.sort();

            for name in tenant_names {
                // Skip if already added as active tenant
                if brands.iter().any(|b| b["slug"] == name) {
                    continue;
                }
                brands.push(json!({
                    "name": name.replace('_', " "),
                    "slug": name,
                }));
            }
        }
    }

    if brands.is_empty() {
        brands.push(json!({
            "name": "default",
            "slug": "default",
        }));
    }

    Json(json!({ "brands": brands }))
}

// ── Stationery ──────────────────────────────────────────────────────

async fn list_stationery() -> Json<Value> {
    let tc = tenant_config();
    let mut result = serde_json::Map::new();

    if let Some(root) = tc.tenants_root() {
        if let Ok(entries) = std::fs::read_dir(root) {
            for entry in entries.flatten() {
                let path = entry.path();
                if !path.is_dir() {
                    continue;
                }
                let tenant_name = entry.file_name().to_str().unwrap_or("").to_string();
                let stat_dir = path.join("stationery");
                if !stat_dir.is_dir() {
                    continue;
                }
                let files: Vec<String> = std::fs::read_dir(&stat_dir)
                    .into_iter()
                    .flatten()
                    .flatten()
                    .filter(|e| {
                        e.path().extension().is_some_and(|ext| {
                            ext == "pdf" || ext == "png" || ext == "jpg"
                        })
                    })
                    .filter_map(|e| e.file_name().to_str().map(|s| s.to_string()))
                    .collect();

                result.insert(
                    tenant_name,
                    json!({
                        "complete": !files.is_empty(),
                        "files": files,
                        "missing": [],
                    }),
                );
            }
        }
    }

    Json(json!({ "brands": result }))
}

// ── Admin: Tenants ──────────────────────────────────────────────────

fn count_files_in_dir(dir: &std::path::Path, extensions: &[&str]) -> usize {
    std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .flatten()
        .filter(|e| {
            e.path()
                .extension()
                .is_some_and(|ext| extensions.iter().any(|x| ext == *x))
        })
        .count()
}

async fn list_tenants() -> Json<Value> {
    let tc = tenant_config();
    let mut tenants = Vec::new();

    if let Some(root) = tc.tenants_root() {
        if let Ok(entries) = std::fs::read_dir(root) {
            let mut dirs: Vec<_> = entries.flatten().filter(|e| e.path().is_dir()).collect();
            dirs.sort_by_key(|e| e.file_name());

            for entry in dirs {
                let path = entry.path();
                let name = entry.file_name().to_str().unwrap_or("").to_string();

                tenants.push(json!({
                    "name": name,
                    "has_brand": path.join("brand.yaml").is_file(),
                    "template_count": count_files_in_dir(&path.join("templates"), &["yaml"]),
                    "page_type_count": count_files_in_dir(&path.join("page_types"), &["yaml"]),
                    "module_count": count_files_in_dir(&path.join("modules"), &["yaml"]),
                    "stationery_count": count_files_in_dir(&path.join("stationery"), &["pdf", "png", "jpg"]),
                    "logo_count": count_files_in_dir(&path.join("logos"), &["svg", "png", "jpg"]),
                    "font_count": count_files_in_dir(&path.join("fonts"), &["ttf", "otf", "woff", "woff2"]),
                }));
            }
        }
    }

    Json(json!({ "tenants": tenants }))
}

async fn list_tenant_templates(
    AxumPath(tenant): AxumPath<String>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let tc = tenant_config();
    let root = tc
        .tenants_root()
        .ok_or((StatusCode::NOT_FOUND, "No tenants root".to_string()))?;

    let templates_dir = root.join(&tenant).join("templates");
    if !templates_dir.is_dir() {
        return Ok(Json(json!({ "templates": [] })));
    }

    let templates: Vec<Value> = std::fs::read_dir(&templates_dir)
        .into_iter()
        .flatten()
        .flatten()
        .filter(|e| e.path().extension().is_some_and(|ext| ext == "yaml"))
        .map(|e| {
            let size = e.metadata().map(|m| m.len()).unwrap_or(0);
            json!({
                "filename": e.file_name().to_str().unwrap_or(""),
                "size": size,
            })
        })
        .collect();

    Ok(Json(json!({ "templates": templates })))
}

async fn get_tenant_brand(
    AxumPath(tenant): AxumPath<String>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let tc = tenant_config();
    let root = tc
        .tenants_root()
        .ok_or((StatusCode::NOT_FOUND, "No tenants root".to_string()))?;

    let brand_path = root.join(&tenant).join("brand.yaml");
    if !brand_path.is_file() {
        return Ok(Json(json!({
            "exists": false,
            "parsed": null,
            "raw": "",
        })));
    }

    let raw = std::fs::read_to_string(&brand_path)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    let parsed: Option<Value> = serde_yaml::from_str::<serde_yaml::Value>(&raw)
        .ok()
        .and_then(|v| serde_json::to_value(v).ok());

    Ok(Json(json!({
        "exists": true,
        "parsed": parsed,
        "raw": raw,
    })))
}

// ── Validate ────────────────────────────────────────────────────────

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

// ── Auth mock ───────────────────────────────────────────────────────

async fn auth_me() -> Json<Value> {
    let tc = tenant_config();
    let tenant_name = tc
        .tenant_dir()
        .and_then(|p| p.file_name())
        .and_then(|n| n.to_str())
        .unwrap_or("default");

    Json(json!({
        "user": {
            "id": "rust-test-user",
            "username": "testuser",
            "email": "test@open-aec.com",
            "display_name": "Rust Test User",
            "role": "admin",
            "tenant": tenant_name,
            "is_active": true,
            "company": "OpenAEC",
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

// ── Report generation ───────────────────────────────────────────────

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
