//! The application menu.
//!
//! A window with the platform's default menu and nothing of its own is one of
//! the clearest signals that an app is a web page in a frame. Every item here
//! maps to something the interface can already do, reached by the shortcut a
//! person would try first.

use tauri::menu::{AboutMetadata, Menu, MenuItem, PredefinedMenuItem, Submenu};
use tauri::{AppHandle, Emitter, Manager, Runtime};

pub fn build<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<Menu<R>> {
    let open = MenuItem::with_id(app, "open", "Open…", true, Some("CmdOrCtrl+O"))?;
    let save = MenuItem::with_id(app, "save", "Save Transcript…", true, Some("CmdOrCtrl+S"))?;
    let setup = MenuItem::with_id(app, "setup", "Show Setup Again", true, None::<&str>)?;
    let models = MenuItem::with_id(app, "models", "Models…", true, Some("CmdOrCtrl+,"))?;

    let app_menu = Submenu::with_items(
        app,
        "Timbre",
        true,
        &[
            &PredefinedMenuItem::about(app, Some("About Timbre"), Some(AboutMetadata::default()))?,
            &PredefinedMenuItem::separator(app)?,
            &models,
            &setup,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::hide(app, None)?,
            &PredefinedMenuItem::hide_others(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::quit(app, None)?,
        ],
    )?;

    let file_menu = Submenu::with_items(
        app,
        "File",
        true,
        &[
            &open,
            &save,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::close_window(app, None)?,
        ],
    )?;

    let edit_menu = Submenu::with_items(
        app,
        "Edit",
        true,
        &[
            &PredefinedMenuItem::undo(app, None)?,
            &PredefinedMenuItem::redo(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::cut(app, None)?,
            &PredefinedMenuItem::copy(app, None)?,
            &PredefinedMenuItem::paste(app, None)?,
            &PredefinedMenuItem::select_all(app, None)?,
        ],
    )?;

    let window_menu = Submenu::with_items(
        app,
        "Window",
        true,
        &[
            &PredefinedMenuItem::minimize(app, None)?,
            &PredefinedMenuItem::maximize(app, None)?,
            &PredefinedMenuItem::separator(app)?,
            &PredefinedMenuItem::fullscreen(app, None)?,
        ],
    )?;

    let help = MenuItem::with_id(app, "repo", "Timbre on GitHub", true, None::<&str>)?;
    let licences = MenuItem::with_id(app, "licences", "Licences", true, None::<&str>)?;
    let help_menu = Submenu::with_items(app, "Help", true, &[&help, &licences])?;

    Menu::with_items(
        app,
        &[&app_menu, &file_menu, &edit_menu, &window_menu, &help_menu],
    )
}

/// Menu items do not act on the interface directly. They emit an event the
/// frontend already knows how to handle, so the menu and the on-screen
/// controls cannot drift into doing different things.
pub fn on_event<R: Runtime>(app: &AppHandle<R>, id: &str) {
    match id {
        "licences" => {
            use tauri_plugin_opener::OpenerExt;
            if let Ok(dir) = app.path().resource_dir() {
                let path = dir.join("licenses").to_string_lossy().into_owned();
                let _ = app.opener().open_path(path, None::<&str>);
            }
        }
        "repo" => {
            use tauri_plugin_opener::OpenerExt;
            let _ = app
                .opener()
                .open_url("https://github.com/dpaguba/timbre", None::<&str>);
        }
        other => {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.emit("menu", other);
            }
        }
    }
}
