use std::path::PathBuf;

use openaec_core::template_loader::TemplateLoader;
use openaec_core::tenant::{TenantConfig, DEFAULT_TENANT};

pub fn tenant_config() -> TenantConfig {
    TenantConfig::new(None, None)
}

pub fn template_loader() -> TemplateLoader {
    let tc = tenant_config();

    // Collect template directories from all tenants
    let mut dirs = tc.templates_dirs();

    // Also scan all tenants in tenants_root for their templates
    if let Some(root) = tc.tenants_root() {
        if let Ok(entries) = std::fs::read_dir(root) {
            for entry in entries.flatten() {
                let templates_dir = entry.path().join("templates");
                if templates_dir.is_dir() && !dirs.contains(&templates_dir) {
                    dirs.push(templates_dir);
                }
            }
        }
    }

    if dirs.is_empty() {
        tracing::warn!("No template directories found");
        TemplateLoader::new(PathBuf::from(format!(
            "tenants/{}/templates",
            DEFAULT_TENANT
        )))
    } else {
        TemplateLoader::with_dirs(dirs)
    }
}
