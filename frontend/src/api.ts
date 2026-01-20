import { isDesktop } from "./desktop";
import type { JobStatus, Language, Limits, ModelState, TranscribeOptions } from "./types";

let BASE = "/api";
let TOKEN: string | null = null;

/** Learn where the API is. Called once, before anything else talks to it. */
export async function connect(): Promise<void> {
  if (!isDesktop()) return;
  const { invoke } = await import("@tauri-apps/api/core");
  const info = await invoke<{ base_url: string; token: string }>("server_info");
  BASE = `${info.base_url}/api`;
  TOKEN = info.token;
}

function authHeaders(): HeadersInit {
  return TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {};
}

/** Start a job from paths the shell picked, with no upload at all. */
export async function createLocalJob(
  paths: string[],
  options: TranscribeOptions
): Promise<JobStatus> {
  const res = await fetch(`${BASE}/jobs/local`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ paths, options }),
  });
  if (!res.ok) throw new Error(await errorText(res));
  return res.json();
}

/** The finished transcript as text, for the native save panel. */
export async function fetchTranscript(jobId: string): Promise<string> {
  const res = await fetch(`${BASE}/jobs/${jobId}/download`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await errorText(res));
  return res.text();
}

/** Download links are followed by the browser, which cannot carry a header. */
export function withToken(url: string): string {
  if (!TOKEN) return url;
  return url + (url.includes("?") ? "&" : "?") + `token=${encodeURIComponent(TOKEN)}`;
}

export async function fetchLanguages(): Promise<{
  languages: Language[];
  models: string[];
  limits: Limits;
}> {
  const res = await fetch(`${BASE}/languages`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load languages");
  return res.json();
}

export interface UploadHandle {
  /** Resolves with the created job, rejects on error or abort. */
  promise: Promise<JobStatus>;
  /** Stop the upload. The promise rejects with an "aborted" error. */
  abort: () => void;
}

/** Start a job, reporting how much of the upload has been sent.
 *
 * XMLHttpRequest rather than fetch: fetch still has no request-progress event,
 * and a multi-gigabyte upload with no feedback looks identical to a hang.
 */
export function createJob(
  files: File[],
  options: TranscribeOptions,
  onProgress?: (sentBytes: number, totalBytes: number) => void
): UploadHandle {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  form.append("options", JSON.stringify(options));

  const xhr = new XMLHttpRequest();
  const promise = new Promise<JobStatus>((resolve, reject) => {
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) onProgress?.(e.loaded, e.total);
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("The backend returned a response that could not be read."));
        }
        return;
      }
      reject(new Error(messageForStatus(xhr.status, xhr.responseText)));
    });

    xhr.addEventListener("error", () =>
      reject(new Error("Could not reach the backend. Is it running on port 8000?"))
    );
    xhr.addEventListener("abort", () => reject(new Error("Upload cancelled.")));

    xhr.open("POST", `${BASE}/jobs`);
    if (TOKEN) xhr.setRequestHeader("Authorization", `Bearer ${TOKEN}`);
    xhr.send(form);
  });

  return { promise, abort: () => xhr.abort() };
}

/** Pull a usable message out of an error response body.
 *
 * FastAPI returns `detail` as a string for our own HTTPExceptions, but as an
 * array of objects for request-validation failures. Rendering the latter
 * directly puts "[object Object]" in front of the user.
 */
function detailFromBody(body: string): string | null {
  try {
    const parsed: unknown = JSON.parse(body);
    if (parsed && typeof parsed === "object" && "detail" in parsed) {
      const detail = (parsed as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
    }
    return null;
  } catch {
    return null;
  }
}

function messageForStatus(status: number, body: string): string {
  const detail = detailFromBody(body);
  if (detail) return detail;
  if (status === 403) return "This server only accepts requests from its own page.";
  if (status === 413) return "Those files are larger than this instance accepts.";
  if (status === 422) return "The request was rejected as malformed. Please try again.";
  if (status >= 500) return "The backend failed while starting the job. Check its terminal output.";
  return "Failed to start job";
}

/** Thrown when the backend no longer knows about a job (e.g. after a restart). */
export class JobNotFoundError extends Error {
  constructor(jobId: string) {
    super(`Job ${jobId} no longer exists`);
    this.name = "JobNotFoundError";
  }
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${BASE}/jobs/${jobId}`, { headers: authHeaders() });
  if (res.status === 404) throw new JobNotFoundError(jobId);
  if (!res.ok) throw new Error("Failed to fetch job status");
  return res.json();
}

export function downloadUrl(jobId: string): string {
  return withToken(`${BASE}/jobs/${jobId}/download`);
}

/** Human-readable size, matching how the backend words its limits. */
export function formatBytes(num: number): string {
  const units: [number, string][] = [
    [1024 ** 3, "GB"],
    [1024 ** 2, "MB"],
    [1024, "KB"],
  ];
  for (const [threshold, unit] of units) {
    if (num >= threshold) {
      const value = num / threshold;
      return `${value >= 10 ? value.toFixed(0) : value.toFixed(1)} ${unit}`;
    }
  }
  return `${num} bytes`;
}

export async function fetchModels(): Promise<{ models: ModelState[] }> {
  const res = await fetch(`${BASE}/models`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load models");
  return res.json();
}

export async function downloadModel(name: string): Promise<void> {
  const res = await fetch(`${BASE}/models/${name}/download`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await errorText(res));
}

export async function removeModel(name: string): Promise<void> {
  const res = await fetch(`${BASE}/models/${name}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(await errorText(res));
}

async function errorText(res: Response): Promise<string> {
  const body: unknown = await res.json().catch(() => null);
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return `Request failed with ${res.status}`;
}
