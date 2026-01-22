import { useRef, useState } from "react";
import { formatBytes } from "../api";
import type { Limits } from "../types";

interface Props {
  limits: Limits | null;
  files: File[];
  onChange: (files: File[]) => void;
  disabled?: boolean;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** Upload dropzone for the browser build.
 *
 * The file input is visually hidden rather than removed, so assistive
 * technology still reaches it, and the wrapping div carries the role, the
 * tabindex and the key handling. It is the only control a keyboard user can
 * reach: without it the primary action of the app is mouse-only.
 *
 * Oversized files are refused here rather than after the upload. The backend
 * answers 413, but only once every byte has been sent, which on a 20 GB drop
 * is an hour of waiting for a refusal that was knowable up front.
 */
export default function FileDropzone({ files, onChange, disabled, limits }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [rejected, setRejected] = useState<string | null>(null);

  function addFiles(list: FileList | null) {
    if (!list) return;
    const incoming = Array.from(list);
    const key = (f: File) => `${f.name}:${f.size}`;
    const existing = new Set(files.map(key));
    const fresh = incoming.filter((f) => !existing.has(key(f)));

    const tooBig: string[] = [];
    const accepted: File[] = [];
    for (const f of fresh) {
      if (limits && f.size > limits.max_upload_bytes) tooBig.push(f.name);
      else accepted.push(f);
    }

    const next = [...files, ...accepted];
    const total = next.reduce((sum, f) => sum + f.size, 0);
    if (limits && total > limits.max_job_bytes) {
      setRejected(
        `That batch is ${formatBytes(total)}, over the ${formatBytes(limits.max_job_bytes)} limit for one job.`
      );
      return;
    }

    setRejected(
      tooBig.length
        ? `Too large for this instance (limit ${formatBytes(limits!.max_upload_bytes)}): ${tooBig.join(", ")}`
        : null
    );
    onChange(next);
  }

  function removeAt(index: number) {
    onChange(files.filter((_, i) => i !== index));
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Choose audio or video files"
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (!disabled && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!disabled) addFiles(e.dataTransfer.files);
        }}
        className={`relative flex cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xxl border border-dashed px-8 py-16 text-center transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink ${
          dragging
            ? "border-ink bg-canvas-soft"
            : "border-hairline-strong bg-canvas-soft hover:border-muted"
        } ${disabled ? "pointer-events-none opacity-40" : ""}`}
      >
        <div
          aria-hidden="true"
          className="orb left-1/2 top-1/2 h-56 w-56 -translate-x-1/2 -translate-y-1/2 sm:h-72 sm:w-72"
        >
          <div
            className="orb-bloom"
            style={{ background: "radial-gradient(circle, #c8b8e0 0%, transparent 70%)" }}
          />
        </div>
        <p className="relative font-display text-display-sm text-ink">
          Drop audio or video here
        </p>
        <p className="relative mt-3 max-w-sm text-body-sm text-muted">
          {limits
            ? `Any format, up to ${formatBytes(limits.max_upload_bytes)} per file.`
            : "Any format."}{" "}
          Click to browse instead.
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          tabIndex={-1}
          accept="audio/*,video/*"
          className="sr-only"
          onChange={(e) => {
            addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {rejected && (
        <p role="alert" className="mt-3 text-body-sm text-semantic-error">
          {rejected}
        </p>
      )}

      {files.length > 0 && (
        <ul className="mt-4 divide-y divide-hairline overflow-hidden rounded-xl border border-hairline bg-surface-card">
          {files.map((f, i) => (
            <li key={`${f.name}:${f.size}`} className="flex items-center justify-between px-5 py-3 text-body-sm">
              <span className="truncate text-ink">{f.name}</span>
              <span className="ml-4 flex items-center gap-4 text-muted-soft">
                {formatSize(f.size)}
                {!disabled && (
                  <button
                    onClick={() => removeAt(i)}
                    className="rounded-pill px-1 text-muted-soft transition hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
                    aria-label={`Remove ${f.name}`}
                  >
                    ✕
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
