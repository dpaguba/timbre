//! Timbre desktop shell.
//!
//! The shell starts the bundled server, waits until it is actually listening,
//! and makes sure the process dies when the app does.
//!
//! The frontend is part of the app rather than a page the server serves. That
//! is what makes the Tauri APIs reachable from it: native dialogs, drag and
//! drop, menus. It also means the window paints immediately instead of waiting
//! on the server.
//!
//! Startup reads the server's stdout until it announces its address. The server
//! prints that line only once it is accepting connections, so reading it
//! doubles as the readiness wait; a slow machine takes longer rather than
//! showing an error. Stdout keeps being drained afterwards, otherwise the pipe
//! fills and the server blocks on its next print.
//!
//! Shutdown is covered twice over. Killing the child on the exit event handles
//! a normal quit, which may never unwind the managed state and run `Drop`. The
//! child also holds the read end of this process's stdin: when the shell is
//! killed outright and no cleanup code of its own can run, the write end closes
//! and the server sees EOF.
//!
//! Window size and position survive a restart. An app that opens at the same
//! default rectangle every time reads as a web page in a frame.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

mod menu;

use tauri::Manager;

/// Small persistent settings beside the app's data.
///
/// Only what has to survive a restart lives here. Everything else is derived
/// from what is on disk, so there is no state to fall out of sync.
fn settings_path(app: &tauri::AppHandle) -> Option<std::path::PathBuf> {
    let dir = app.path().app_config_dir().ok()?;
    let _ = std::fs::create_dir_all(&dir);
    Some(dir.join("settings.json"))
}

/// Progress on the dock or taskbar icon.
///
/// A twenty-minute transcription is exactly the case where the window is not
/// the thing being looked at, so the icon has to carry the state.
#[tauri::command]
fn set_dock_progress(app: tauri::AppHandle, fraction: Option<f64>) {
    use tauri::window::{ProgressBarState, ProgressBarStatus};
    if let Some(window) = app.get_webview_window("main") {
        let state = match fraction {
            Some(value) => ProgressBarState {
                status: Some(ProgressBarStatus::Normal),
                progress: Some((value.clamp(0.0, 1.0) * 100.0) as u64),
            },
            None => ProgressBarState {
                status: Some(ProgressBarStatus::None),
                progress: Some(0),
            },
        };
        let _ = window.set_progress_bar(state);
    }
}

#[tauri::command]
fn get_onboarded(app: tauri::AppHandle) -> bool {
    settings_path(&app)
        .and_then(|p| std::fs::read_to_string(p).ok())
        .and_then(|s| serde_json::from_str::<serde_json::Value>(&s).ok())
        .and_then(|v| v.get("onboarded").and_then(|b| b.as_bool()))
        .unwrap_or(false)
}

#[tauri::command]
fn set_onboarded(app: tauri::AppHandle, value: bool) {
    if let Some(path) = settings_path(&app) {
        let body = serde_json::json!({ "onboarded": value });
        let _ = std::fs::write(path, body.to_string());
    }
}

/// Where the sidecar is listening, handed to the frontend once at startup.
#[derive(Clone, serde::Serialize)]
struct ServerInfo {
    base_url: String,
    token: String,
}

#[tauri::command]
fn server_info(info: tauri::State<ServerInfo>) -> ServerInfo {
    info.inner().clone()
}

/// Kills the sidecar when the app exits, including when the exit was a panic.
/// Without this the server keeps running headless, holding its port and its
/// model in memory, and the next launch starts a second one.
struct Server(Mutex<Option<Child>>);

impl Drop for Server {
    fn drop(&mut self) {
        if let Ok(mut guard) = self.0.lock() {
            if let Some(mut child) = guard.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}

/// 32 hex characters from the OS random source. Another process on this machine
/// cannot guess it, which is the guarantee that replaces the browser build's
/// origin check.
fn random_token() -> String {
    let mut bytes = [0u8; 16];
    getrandom(&mut bytes);
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

#[cfg(unix)]
fn getrandom(buf: &mut [u8]) {
    use std::io::Read;
    std::fs::File::open("/dev/urandom")
        .expect("no /dev/urandom")
        .read_exact(buf)
        .expect("could not read random bytes");
}

/// ProcessPrng is the documented user-mode entry point and cannot fail.
#[cfg(windows)]
fn getrandom(buf: &mut [u8]) {
    extern "system" {
        fn ProcessPrng(pbdata: *mut u8, cbdata: usize) -> i32;
    }
    unsafe {
        ProcessPrng(buf.as_mut_ptr(), buf.len());
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .invoke_handler(tauri::generate_handler![
            server_info,
            get_onboarded,
            set_onboarded,
            set_dock_progress
        ])
        .setup(|app| {
            let token = random_token();

            let resource_dir = app.path().resource_dir()?;
            let exe_name = if cfg!(windows) {
                "timbre-server.exe"
            } else {
                "timbre-server"
            };
            let server_path = resource_dir.join("server").join(exe_name);

            let mut child = Command::new(&server_path)
                .arg("--port")
                .arg("0")
                .arg("--token")
                .arg(&token)
                .arg("--exit-with-parent")
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::inherit())
                .spawn()
                .map_err(|e| format!("could not start {}: {e}", server_path.display()))?;

            let stdout = child.stdout.take().expect("stdout was piped");
            let mut reader = BufReader::new(stdout);
            let mut line = String::new();
            let mut base_url = None;

            for _ in 0..200 {
                line.clear();
                match reader.read_line(&mut line) {
                    Ok(0) => break,
                    Ok(_) => {
                        if let Some(rest) = line.trim().strip_prefix("TIMBRE_READY ") {
                            base_url = Some(rest.to_string());
                            break;
                        }
                    }
                    Err(_) => break,
                }
            }

            std::thread::spawn(move || {
                let mut sink = String::new();
                while reader.read_line(&mut sink).unwrap_or(0) > 0 {
                    sink.clear();
                }
            });

            let base_url = base_url.ok_or("the server did not report a ready address")?;
            app.manage(Server(Mutex::new(Some(child))));

            app.manage(ServerInfo {
                base_url: base_url.clone(),
                token: token.clone(),
            });

            app.set_menu(menu::build(app.handle())?)?;
            app.on_menu_event(|app, event| menu::on_event(app, event.id().as_ref()));

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building Timbre")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(server) = app.try_state::<Server>() {
                    if let Ok(mut guard) = server.0.lock() {
                        if let Some(mut child) = guard.take() {
                            let _ = child.kill();
                            let _ = child.wait();
                        }
                    }
                }
            }
        });
}
