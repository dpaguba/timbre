export type OutputFormat = "txt" | "md" | "docx";
export type JobState = "queued" | "running" | "done" | "error";

export interface Language {
  code: string;
  name: string;
  native: string;
}

export interface TranscribeOptions {
  languages: string[];
  multilingual: boolean;
  model: string;
  output_format: OutputFormat;
  include_timestamps: boolean;
}

export interface FileProgress {
  filename: string;
  state: JobState;
  progress: number;
  detected_language: string | null;
  error: string | null;
}

export interface JobStatus {
  job_id: string;
  state: JobState;
  options: TranscribeOptions;
  files: FileProgress[];
  error: string | null;
}

/** Upload guards reported by the backend, so the browser can reject a file
 * before spending an hour sending it. */
export interface Limits {
  max_upload_bytes: number;
  max_job_bytes: number;
}

export interface ModelDownload {
  state: "running" | "done" | "error";
  downloaded: number;
  total: number;
  error: string | null;
}

export interface ModelState {
  name: string;
  installed: boolean;
  size_bytes: number;
  approx_bytes: number;
  download: ModelDownload | null;
}
