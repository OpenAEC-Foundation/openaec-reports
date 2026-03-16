use axum::{
    extract::{Path as AxumPath, State},
    http::{header, StatusCode},
    response::IntoResponse,
    routing::{get, post, put},
    Json, Router,
};
use rusqlite::Connection;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tower_http::services::{ServeDir, ServeFile};

use openaec_core::template_loader::TemplateLoader;
use openaec_core::tenant::TenantConfig;

// ── Shared state ────────────────────────────────────────────────────

type Db = Arc<Mutex<Connection>>;

#[derive(Clone)]
struct AppState {
    db: Db,
}

// ── Helpers ─────────────────────────────────────────────────────────

fn tenant_config() -> TenantConfig {
    TenantConfig::new(None, None)
}

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

fn init_db() -> Connection {
    let db_path = std::env::var("OPENAEC_DB_PATH").unwrap_or_else(|_| "/app/data.db".to_string());
    let conn = Connection::open(&db_path).expect("Failed to open SQLite database");
    conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")
        .expect("Failed to set PRAGMA");

    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            template TEXT NOT NULL DEFAULT '',
            project_id TEXT,
            content TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        );",
    )
    .expect("Failed to create tables");

    tracing::info!("Database initialized at {}", db_path);
    conn
}

fn new_id() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let ts = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis();
    format!("{:x}", ts)
}

// ── Main ────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

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

    // Log tenant info
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

    // Initialize database
    let db = Arc::new(Mutex::new(init_db()));
    let state = AppState { db };

    let app = Router::new()
        // API routes
        .route("/api/health", get(health))
        .route("/api/templates", get(list_templates))
        .route("/api/templates/{name}/scaffold", get(get_scaffold))
        .route("/api/brands", get(list_brands))
        .route("/api/stationery", get(list_stationery))
        // Generate — all variants point to same handler
        .route("/api/generate", post(generate))
        .route("/api/generate/v2", post(generate))
        .route("/api/generate/template", post(generate))
        // Projects CRUD
        .route("/api/projects", get(list_projects).post(create_project))
        .route(
            "/api/projects/{id}",
            get(get_project).put(update_project).delete(delete_project),
        )
        // Reports CRUD
        .route("/api/reports", get(list_reports).post(save_report))
        .route(
            "/api/reports/{id}",
            get(get_report).put(save_report_by_id).delete(delete_report),
        )
        .route("/api/reports/{id}/move", put(move_report))
        // Admin
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
        // Auth mock
        .route("/api/auth/me", get(auth_me))
        .route("/api/auth/login", post(auth_login))
        .route("/api/auth/logout", post(auth_logout))
        .route("/api/auth/register", post(auth_register))
        .route("/api/auth/registration-enabled", get(auth_registration))
        .route("/api/auth/oidc/config", get(auth_oidc_config))
        .route("/api/auth/oidc/code-exchange", post(auth_oidc_exchange))
        // Shared state
        .with_state(state)
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

    if let Some(root) = tc.tenants_root() {
        if let Ok(entries) = std::fs::read_dir(root) {
            let mut tenant_names: Vec<String> = entries
                .flatten()
                .filter(|e| e.path().is_dir() && e.path().join("brand.yaml").is_file())
                .filter_map(|e| e.file_name().to_str().map(|s| s.to_string()))
                .collect();
            tenant_names.sort();

            for name in tenant_names {
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
        brands.push(json!({ "name": "default", "slug": "default" }));
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
                        e.path()
                            .extension()
                            .is_some_and(|ext| ext == "pdf" || ext == "png" || ext == "jpg")
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

// ── Generate PDF ────────────────────────────────────────────────────

async fn generate(
    Json(payload): Json<Value>,
) -> Result<impl IntoResponse, (StatusCode, String)> {
    let json_str =
        serde_json::to_string(&payload).map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;

    let report_data = openaec_core::ReportData::from_json(&json_str)
        .map_err(|e| (StatusCode::BAD_REQUEST, format!("Invalid JSON: {}", e)))?;

    let temp_path = std::path::Path::new("temp_output.pdf");
    let pdf_bytes = openaec_core::engine::generate_pdf(&report_data, temp_path).map_err(|e| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            format!("Generation failed: {}", e),
        )
    })?;

    Ok((
        [
            (header::CONTENT_TYPE, "application/pdf"),
            (
                header::CONTENT_DISPOSITION,
                "inline; filename=\"rapport.pdf\"",
            ),
        ],
        pdf_bytes,
    ))
}

// ── Projects CRUD ───────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct CreateProject {
    name: String,
    #[serde(default)]
    description: String,
}

async fn list_projects(State(state): State<AppState>) -> Result<Json<Value>, (StatusCode, String)> {
    let db = state.db.lock().unwrap();
    let mut stmt = db
        .prepare("SELECT id, name, description, created_at, updated_at FROM projects ORDER BY updated_at DESC")
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    let projects: Vec<Value> = stmt
        .query_map([], |row| {
            Ok(json!({
                "id": row.get::<_, String>(0)?,
                "name": row.get::<_, String>(1)?,
                "description": row.get::<_, String>(2)?,
                "created_at": row.get::<_, String>(3)?,
                "updated_at": row.get::<_, String>(4)?,
            }))
        })
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?
        .filter_map(|r| r.ok())
        .collect();

    Ok(Json(json!(projects)))
}

async fn create_project(
    State(state): State<AppState>,
    Json(payload): Json<CreateProject>,
) -> Result<(StatusCode, Json<Value>), (StatusCode, String)> {
    let id = new_id();
    let db = state.db.lock().unwrap();
    db.execute(
        "INSERT INTO projects (id, name, description) VALUES (?1, ?2, ?3)",
        rusqlite::params![id, payload.name, payload.description],
    )
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    Ok((
        StatusCode::CREATED,
        Json(json!({
            "id": id,
            "name": payload.name,
            "description": payload.description,
        })),
    ))
}

async fn get_project(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let db = state.db.lock().unwrap();
    let project = db
        .query_row(
            "SELECT id, name, description, created_at, updated_at FROM projects WHERE id = ?1",
            rusqlite::params![id],
            |row| {
                Ok(json!({
                    "id": row.get::<_, String>(0)?,
                    "name": row.get::<_, String>(1)?,
                    "description": row.get::<_, String>(2)?,
                    "created_at": row.get::<_, String>(3)?,
                    "updated_at": row.get::<_, String>(4)?,
                }))
            },
        )
        .map_err(|_| (StatusCode::NOT_FOUND, "Project not found".to_string()))?;

    Ok(Json(project))
}

async fn update_project(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
    Json(payload): Json<CreateProject>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let db = state.db.lock().unwrap();
    let rows = db
        .execute(
            "UPDATE projects SET name = ?1, description = ?2, updated_at = datetime('now') WHERE id = ?3",
            rusqlite::params![payload.name, payload.description, id],
        )
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    if rows == 0 {
        return Err((StatusCode::NOT_FOUND, "Project not found".to_string()));
    }

    Ok(Json(json!({
        "id": id,
        "name": payload.name,
        "description": payload.description,
    })))
}

async fn delete_project(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let db = state.db.lock().unwrap();
    db.execute("DELETE FROM projects WHERE id = ?1", rusqlite::params![id])
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    Ok(Json(json!({"detail": "Project verwijderd"})))
}

// ── Reports CRUD ────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
struct SaveReport {
    #[serde(default)]
    id: String,
    title: String,
    #[serde(default)]
    template: String,
    #[serde(default)]
    project_id: Option<String>,
    #[serde(default)]
    content: Value,
}

async fn list_reports(
    State(state): State<AppState>,
    axum::extract::Query(params): axum::extract::Query<std::collections::HashMap<String, String>>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let db = state.db.lock().unwrap();

    let (sql, param): (String, Option<String>) = if let Some(project_id) = params.get("project_id")
    {
        (
            "SELECT id, title, template, project_id, created_at, updated_at FROM reports WHERE project_id = ?1 ORDER BY updated_at DESC".to_string(),
            Some(project_id.clone()),
        )
    } else {
        (
            "SELECT id, title, template, project_id, created_at, updated_at FROM reports ORDER BY updated_at DESC".to_string(),
            None,
        )
    };

    let mut stmt = db
        .prepare(&sql)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    let row_to_json = |row: &rusqlite::Row| -> rusqlite::Result<Value> {
        Ok(json!({
            "id": row.get::<_, String>(0)?,
            "title": row.get::<_, String>(1)?,
            "template": row.get::<_, String>(2)?,
            "project_id": row.get::<_, Option<String>>(3)?,
            "created_at": row.get::<_, String>(4)?,
            "updated_at": row.get::<_, String>(5)?,
        }))
    };

    let reports: Vec<Value> = if let Some(ref pid) = param {
        stmt.query_map(rusqlite::params![pid], row_to_json)
    } else {
        stmt.query_map([], row_to_json)
    }
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?
    .filter_map(|r| r.ok())
    .collect();

    Ok(Json(json!(reports)))
}

async fn save_report(
    State(state): State<AppState>,
    Json(payload): Json<SaveReport>,
) -> Result<(StatusCode, Json<Value>), (StatusCode, String)> {
    let id = if payload.id.is_empty() {
        new_id()
    } else {
        payload.id.clone()
    };
    let content_str =
        serde_json::to_string(&payload.content).unwrap_or_else(|_| "{}".to_string());

    let db = state.db.lock().unwrap();
    db.execute(
        "INSERT INTO reports (id, title, template, project_id, content) VALUES (?1, ?2, ?3, ?4, ?5)
         ON CONFLICT(id) DO UPDATE SET title=?2, template=?3, project_id=?4, content=?5, updated_at=datetime('now')",
        rusqlite::params![id, payload.title, payload.template, payload.project_id, content_str],
    )
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    Ok((
        StatusCode::CREATED,
        Json(json!({
            "id": id,
            "title": payload.title,
            "template": payload.template,
            "project_id": payload.project_id,
        })),
    ))
}

async fn get_report(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let db = state.db.lock().unwrap();
    let report = db
        .query_row(
            "SELECT id, title, template, project_id, content, created_at, updated_at FROM reports WHERE id = ?1",
            rusqlite::params![id],
            |row| {
                let content_str: String = row.get(4)?;
                let content: Value =
                    serde_json::from_str(&content_str).unwrap_or(json!({}));
                Ok(json!({
                    "id": row.get::<_, String>(0)?,
                    "title": row.get::<_, String>(1)?,
                    "template": row.get::<_, String>(2)?,
                    "project_id": row.get::<_, Option<String>>(3)?,
                    "content": content,
                    "created_at": row.get::<_, String>(5)?,
                    "updated_at": row.get::<_, String>(6)?,
                }))
            },
        )
        .map_err(|_| (StatusCode::NOT_FOUND, "Report not found".to_string()))?;

    Ok(Json(report))
}

async fn save_report_by_id(
    state: State<AppState>,
    AxumPath(id): AxumPath<String>,
    Json(mut payload): Json<SaveReport>,
) -> Result<(StatusCode, Json<Value>), (StatusCode, String)> {
    payload.id = id;
    save_report(state, Json(payload)).await
}

async fn delete_report(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let db = state.db.lock().unwrap();
    db.execute("DELETE FROM reports WHERE id = ?1", rusqlite::params![id])
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    Ok(Json(json!({"detail": "Report verwijderd"})))
}

async fn move_report(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
    Json(payload): Json<Value>,
) -> Result<Json<Value>, (StatusCode, String)> {
    let project_id = payload
        .get("project_id")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string());

    let db = state.db.lock().unwrap();
    db.execute(
        "UPDATE reports SET project_id = ?1, updated_at = datetime('now') WHERE id = ?2",
        rusqlite::params![project_id, id],
    )
    .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    Ok(Json(json!({"detail": "Report verplaatst"})))
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

async fn auth_register() -> (StatusCode, Json<Value>) {
    (
        StatusCode::CREATED,
        Json(json!({
            "user": {
                "id": "new-user",
                "username": "newuser",
                "email": "new@example.com",
                "display_name": "New User",
                "role": "user",
                "tenant": "default",
                "is_active": true,
                "auth_provider": "local"
            }
        })),
    )
}

async fn auth_registration() -> Json<Value> {
    Json(json!({"enabled": false}))
}

async fn auth_oidc_config() -> Json<Value> {
    Json(json!({"enabled": false}))
}

async fn auth_oidc_exchange() -> Json<Value> {
    // Mock: return test user (real OIDC not implemented yet)
    Json(json!({
        "user": {
            "id": "rust-test-user",
            "username": "testuser",
            "email": "test@open-aec.com",
            "display_name": "Rust Test User",
            "role": "admin",
            "tenant": "default",
            "is_active": true,
            "auth_provider": "oidc"
        }
    }))
}
