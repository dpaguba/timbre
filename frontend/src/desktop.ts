/** The line between running inside the app and running in a browser tab.
 *
 * Everything that only exists in the desktop build lives here, so the rest of
 * the code asks `isDesktop()` once instead of feature-detecting Tauri in five
 * different components.
 */

/** Extensions the decoder handles and the pickers offer.
 *
 * The list exists because a native drop gives us a path with no MIME type, and
 * because `accept` on a file input silently hides containers the OS has no
 * mapping for, `.mkv` and `.opus` among them.
 */
export const MEDIA_EXTENSIONS = [
  "mp3", "wav", "m4a", "aac", "flac", "ogg", "oga", "opus", "wma", "aiff", "aif", "caf",
  "mp4", "mov", "m4v", "mkv", "avi", "webm", "wmv", "flv", "mpg", "mpeg", "ts", "3gp",
];

export function isDesktop(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

export function hasMediaExtension(name: string): boolean {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  return MEDIA_EXTENSIONS.includes(ext);
}

export function baseName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

/** Open the system file picker. Returns absolute paths. */
export async function pickMediaFiles(): Promise<string[]> {
  const { open } = await import("@tauri-apps/plugin-dialog");
  const picked = await open({
    multiple: true,
    filters: [{ name: "Audio and video", extensions: MEDIA_EXTENSIONS }],
  });
  if (!picked) return [];
  return Array.isArray(picked) ? picked : [picked];
}

/** Ask where to write the transcript, then write it. Returns the path, or null
 * if the person cancelled. */
export async function saveTranscript(
  suggestedName: string,
  contents: string
): Promise<string | null> {
  const { save } = await import("@tauri-apps/plugin-dialog");
  const { writeTextFile } = await import("@tauri-apps/plugin-fs");
  const extension = suggestedName.split(".").pop() ?? "txt";
  const path = await save({
    defaultPath: suggestedName,
    filters: [{ name: extension.toUpperCase(), extensions: [extension] }],
  });
  if (!path) return null;
  await writeTextFile(path, contents);
  return path;
}

/** Files dragged from Finder or Explorer.
 *
 * The webview's own drag events are deliberately not used: they hand over a
 * File object with no path, which would force the local file to be uploaded
 * back to a server running on the same disk.
 */
export async function onFilesDropped(
  handler: (paths: string[]) => void,
  onHoverChange: (hovering: boolean) => void
): Promise<() => void> {
  const { getCurrentWebview } = await import("@tauri-apps/api/webview");
  const webview = getCurrentWebview();
  return webview.onDragDropEvent((event) => {
    if (event.payload.type === "over" || event.payload.type === "enter") {
      onHoverChange(true);
    } else if (event.payload.type === "drop") {
      onHoverChange(false);
      handler(event.payload.paths);
    } else {
      onHoverChange(false);
    }
  });
}

/** Menu items emit an event rather than acting directly, so the menu and the
 * on-screen controls cannot drift into doing different things. */
export async function onMenu(handler: (id: string) => void): Promise<() => void> {
  const { getCurrentWindow } = await import("@tauri-apps/api/window");
  return getCurrentWindow().listen<string>("menu", (event) => handler(event.payload));
}

export async function wasOnboarded(): Promise<boolean> {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<boolean>("get_onboarded");
}

export async function markOnboarded(value: boolean): Promise<void> {
  const { invoke } = await import("@tauri-apps/api/core");
  await invoke("set_onboarded", { value });
}

/** Progress on the dock or taskbar icon. Pass null to clear it. */
export async function setDockProgress(fraction: number | null): Promise<void> {
  const { invoke } = await import("@tauri-apps/api/core");
  await invoke("set_dock_progress", { fraction });
}

/** Tell the person a long job finished, but only when they are looking
 * elsewhere. A notification for something already on screen is noise. */
export async function notifyIfUnfocused(title: string, body: string): Promise<void> {
  const { getCurrentWindow } = await import("@tauri-apps/api/window");
  if (await getCurrentWindow().isFocused()) return;

  const { isPermissionGranted, requestPermission, sendNotification } = await import(
    "@tauri-apps/plugin-notification"
  );
  let granted = await isPermissionGranted();
  if (!granted) granted = (await requestPermission()) === "granted";
  if (granted) sendNotification({ title, body });
}
