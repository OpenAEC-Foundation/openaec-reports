/// OpenAEC Reports desktop application.
///
/// Thin wrapper around the web frontend. PDF generation happens via
/// the cloud API (default: report.open-aec.com) — no embedded backend needed.
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running OpenAEC Reports");
}
