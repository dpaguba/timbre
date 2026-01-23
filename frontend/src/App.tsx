import { useCallback, useEffect, useRef, useState } from "react";
import FileDropzone from "./components/FileDropzone";
import ModelsView from "./components/ModelsView";
import NativeDropzone from "./components/NativeDropzone";
import Onboarding from "./components/Onboarding";
import Shell from "./components/Shell";
import {
  isDesktop,
  markOnboarded,
  notifyIfUnfocused,
  onMenu,
  setDockProgress,
  wasOnboarded,
} from "./desktop";
import LanguageSelect from "./components/LanguageSelect";
import Settings from "./components/Settings";
import JobProgress from "./components/JobProgress";
import { JobNotFoundError, connect, createJob, createLocalJob, fetchLanguages, fetchModels, formatBytes, getJob, type UploadHandle } from "./api";
import type { JobStatus, Language, Limits, TranscribeOptions } from "./types";

const POLL_DELAYS = [1000, 1000, 2000, 5000];

const desktop = isDesktop();

const DEFAULT_OPTIONS: TranscribeOptions = {
  languages: [],
  multilingual: false,
  model: "small",
  output_format: "md",
  include_timestamps: true,
};

export default function App() {
  const [languages, setLanguages] = useState<Language[]>([]);
  const [models, setModels] = useState<string[]>(["tiny", "base", "small", "medium", "large-v3"]);
  const [files, setFiles] = useState<File[]>([]);
  const [paths, setPaths] = useState<string[]>([]);
  const [openRequest, setOpenRequest] = useState(0);
  const [saveRequest, setSaveRequest] = useState(0);
  const [view, setView] = useState<"work" | "models">("work");
  const [enterFrom, setEnterFrom] = useState<"right" | "left" | "up">("up");
  const [options, setOptions] = useState<TranscribeOptions>(DEFAULT_OPTIONS);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [offline, setOffline] = useState(false);
  const [needsSetup, setNeedsSetup] = useState<boolean | null>(null);
  const [limits, setLimits] = useState<Limits | null>(null);
  const [upload, setUpload] = useState<{ sent: number; total: number } | null>(null);
  const uploadRef = useRef<UploadHandle | null>(null);

  const bootstrap = useCallback(() => {
    fetchLanguages()
      .then((data) => {
        setLanguages(data.languages);
        setModels(data.models);
        setLimits(data.limits);
      })
      .catch(() => setError("Could not reach the backend. Is it running on port 8000?"));

    Promise.all([fetchModels(), desktop ? wasOnboarded() : Promise.resolve(true)])
      .then(([data, onboarded]) => {
        const installed = data.models.filter((m) => m.installed);
        setNeedsSetup(!onboarded || installed.length === 0);
        if (installed.length > 0) {
          setOptions((current) => ({
            ...current,
            model: installed.some((m) => m.name === current.model) ? current.model : installed[0].name,
          }));
        }
      })
      .catch(() => setNeedsSetup(false));
  }, []);

  useEffect(() => {
    connect()
      .then(bootstrap)
      .catch(() => setError("Could not reach the transcription service."));
  }, [bootstrap]);

  useEffect(() => {
    if (!desktop) return;
    let unlisten: (() => void) | undefined;
    let cancelled = false;
    onMenu((id) => {
      if (id === "setup") setNeedsSetup(true);
      if (id === "models") goToModels();
      if (id === "open") setOpenRequest((n) => n + 1);
      if (id === "save") setSaveRequest((n) => n + 1);
    }).then((off) => (cancelled ? off() : (unlisten = off)));
    return () => {
      cancelled = true;
      unlisten?.();
    };
  }, []);
  const chosenCount = desktop ? paths.length : files.length;

  const jobId = job?.job_id;
  const jobState = job?.state;

  useEffect(() => {
    if (!jobId || jobState === "done" || jobState === "error") return;

    let cancelled = false;
    let timer: number;
    let failures = 0;

    const tick = async () => {
      try {
        const status = await getJob(jobId);
        if (cancelled) return;
        failures = 0;
        setOffline(false);
        setJob(status);
      } catch (e) {
        if (cancelled) return;
        if (e instanceof JobNotFoundError) {
          setJob(null);
          setError("The backend restarted and this job was lost. Please upload your files again.");
          return;
        }
        failures += 1;
        if (failures >= 3) setOffline(true);
      }
      if (!cancelled) {
        timer = window.setTimeout(tick, POLL_DELAYS[Math.min(failures, POLL_DELAYS.length - 1)]);
      }
    };

    timer = window.setTimeout(tick, POLL_DELAYS[0]);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [jobId, jobState]);

  useEffect(() => {
    if (!desktop) return;
    if (job && (job.state === "queued" || job.state === "running")) {
      const overall =
        job.files.length === 0
          ? 0
          : job.files.reduce((sum, f) => sum + f.progress, 0) / job.files.length;
      void setDockProgress(overall);
      return;
    }
    void setDockProgress(null);
    if (job?.state === "done") {
      const failed = job.files.filter((f) => f.state === "error").length;
      void notifyIfUnfocused(
        "Transcription finished",
        failed ? `${failed} of ${job.files.length} files failed` : "Your transcript is ready."
      );
    }
    if (job?.state === "error") {
      void notifyIfUnfocused("Transcription failed", job.error ?? "Something went wrong.");
    }
  }, [job]);

  async function start() {
    setError(null);
    setSubmitting(true);
    try {
      const opts = { ...options, multilingual: options.languages.length > 1 };

      if (desktop) {
        setJob(await createLocalJob(paths, opts));
        return;
      }

      setUpload({ sent: 0, total: files.reduce((sum, f) => sum + f.size, 0) });
      const handle = createJob(files, opts, (sent, total) => setUpload({ sent, total }));
      uploadRef.current = handle;
      setJob(await handle.promise);
    } catch (e) {
      if (e instanceof TypeError) {
        setError("Could not reach the backend. Is it running on port 8000?");
      } else {
        setError(e instanceof Error ? e.message : "Failed to start transcription");
      }
    } finally {
      setSubmitting(false);
      setUpload(null);
      uploadRef.current = null;
    }
  }

  function cancelUpload() {
    uploadRef.current?.abort();
  }

  function goToModels() {
    setEnterFrom("right");
    setView("models");
  }

  function goToWork() {
    setEnterFrom("left");
    setView("work");
  }

  function reset() {
    setJob(null);
    setFiles([]);
    setPaths([]);
    setError(null);
  }

  if (needsSetup === null) {
    return <div className="h-full" aria-busy="true" />;
  }

  if (needsSetup) {
    return (
      <Shell viewKey="onboarding" animation="up">
        <Onboarding
          onDone={(model) => {
            setOptions((current) => ({ ...current, model }));
            if (desktop) void markOnboarded(true);
            setNeedsSetup(false);
          }}
        />
      </Shell>
    );
  }

  return (
    <Shell
      viewKey={view}
      animation={enterFrom}
      wide
      topRight={
        view === "work" ? (
          <button onClick={goToModels} className="btn-text">
            Models
          </button>
        ) : null
      }
    >
          {view === "models" ? (
            <ModelsView onBack={goToWork} onChanged={bootstrap} />
          ) : (
          <>
          {error && (
            <div
              role="alert"
              className="animate-fade mb-8 rounded-xl border border-hairline bg-surface-card px-4 py-3 text-body-sm text-semantic-error"
            >
              {error}
            </div>
          )}

          {offline && (
            <div
              role="status"
              className="animate-fade mb-8 rounded-xl border border-hairline bg-surface-card px-4 py-3 text-body-sm text-muted"
            >
              Lost contact with the backend. Still retrying, and your transcription
              may be continuing in the background.
            </div>
          )}

          {job ? (
            <div className="animate-rise mx-auto max-w-2xl">
              <JobProgress job={job} onReset={reset} saveRequest={saveRequest} />
            </div>
          ) : (
            <div className="grid items-start gap-10 wide:grid-cols-[1.1fr_1fr] wide:gap-14">
              <section className="animate-rise delay-1 min-w-0">
                {desktop ? (
                  <NativeDropzone
                    paths={paths}
                    onChange={setPaths}
                    disabled={submitting}
                    openRequest={openRequest}
                  />
                ) : (
                  <FileDropzone files={files} onChange={setFiles} disabled={submitting} limits={limits} />
                )}
              </section>

              <section className="animate-rise delay-2 flex min-w-0 flex-col gap-8 wide:border-l wide:border-hairline wide:pl-14">
                <LanguageSelect
                  languages={languages}
                  selected={options.languages}
                  onChange={(languagesSel) => setOptions({ ...options, languages: languagesSel })}
                  disabled={submitting}
                />

                <Settings
                  options={options}
                  models={models}
                  onChange={setOptions}
                  disabled={submitting}
                  onOpenModels={goToModels}
                />

                {upload && (
                  <div className="card animate-fade p-5">
                    <div className="flex items-baseline justify-between gap-4">
                      <span className="text-body-sm text-body">
                        Uploading {formatBytes(upload.sent)} of {formatBytes(upload.total)}
                      </span>
                      <button onClick={cancelUpload} className="btn-text">
                        Cancel
                      </button>
                    </div>
                    <div className="mt-3 h-1 w-full overflow-hidden rounded-pill bg-surface-strong">
                      <div
                        className="h-full bg-ink transition-all duration-300"
                        style={{ width: `${upload.total ? (upload.sent / upload.total) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-x-6 gap-y-3 pt-2">
                  <button onClick={start} disabled={chosenCount === 0 || submitting} className="btn-primary">
                    {submitting
                      ? "Starting"
                      : chosenCount === 1
                        ? "Transcribe 1 file"
                        : `Transcribe ${chosenCount} files`}
                  </button>
                  {chosenCount === 0 && (
                    <span className="text-body-sm text-muted-soft">Add a file to begin</span>
                  )}
                </div>
              </section>
            </div>
          )}
      </>
      )}
    </Shell>
  );
}
