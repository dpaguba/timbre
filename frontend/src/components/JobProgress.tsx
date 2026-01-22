import type { JobState, JobStatus } from "../types";
import { useEffect, useState } from "react";

import { downloadUrl, fetchTranscript } from "../api";
import { isDesktop, saveTranscript } from "../desktop";

interface Props {
  job: JobStatus;
  onReset: () => void;
  /** Bumped by the Save Transcript menu item. */
  saveRequest?: number;
}

const STATE_LABEL: Record<JobState, string> = {
  queued: "Queued",
  running: "Transcribing…",
  done: "Done",
  error: "Error",
};

export default function JobProgress({ job, onReset, saveRequest }: Props) {
  const done = job.state === "done";
  const failed = job.state === "error";
  const failedFiles = job.files.filter((f) => f.state === "error").length;
  const format = job.options.output_format.toUpperCase();
  const [saving, setSaving] = useState(false);
  const [savedTo, setSavedTo] = useState<string | null>(null);

  useEffect(() => {
    if (saveRequest && done && !saving) void saveNatively();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [saveRequest]);

  async function saveNatively() {
    setSaving(true);
    try {
      const text = await fetchTranscript(job.job_id);
      const stamp = new Date().toISOString().slice(0, 10);
      const path = await saveTranscript(
        `transcript-${stamp}.${job.options.output_format}`,
        text
      );
      if (path) setSavedTo(path);
    } finally {
      setSaving(false);
    }
  }
  const heading = failedFiles > 0 && done
    ? `Completed with errors (${failedFiles} of ${job.files.length} files failed)`
    : STATE_LABEL[job.state];

  return (
    <div className="space-y-8">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="font-display text-display-md text-ink">{heading}</h2>
        <button onClick={onReset} className="btn-text shrink-0">
          Start over
        </button>
      </div>

      <ul className="divide-y divide-hairline overflow-hidden rounded-xl border border-hairline bg-surface-card">
        {job.files.map((f, i) => (
          <li key={i} className="px-5 py-4">
            <div className="flex items-baseline justify-between gap-4 text-body-sm">
              <span className="truncate text-ink">{f.filename}</span>
              <span className="ml-3 shrink-0 text-muted-soft">
                {f.detected_language ? f.detected_language.toUpperCase() + " · " : ""}
                {STATE_LABEL[f.state]}
              </span>
            </div>
            <div className="mt-3 h-1 w-full overflow-hidden rounded-pill bg-surface-strong">
              <div
                className={`h-full rounded-pill transition-all ${
                  f.state === "error" ? "bg-semantic-error" : "bg-ink"
                }`}
                style={{ width: `${Math.round(f.progress * 100)}%` }}
              />
            </div>
            {f.error && <p className="mt-2 text-body-sm text-semantic-error">{f.error}</p>}
          </li>
        ))}
      </ul>

      {failed && job.error && (
        <p className="rounded-xl border border-hairline bg-surface-card px-4 py-3 text-body-sm text-semantic-error">
          {job.error}
        </p>
      )}

      {done && (
        <div className="border-t border-hairline pt-8">
          {isDesktop() ? (
            <>
              <button onClick={saveNatively} disabled={saving} className="btn-primary">
                {saving ? "Saving" : `Save transcript (${format})`}
              </button>
              {savedTo && (
                <p className="mt-3 text-body-sm text-muted">Saved to {savedTo}</p>
              )}
            </>
          ) : (
            <a href={downloadUrl(job.job_id)} className="btn-primary">
              Download transcript ({format})
            </a>
          )}
        </div>
      )}
    </div>
  );
}
