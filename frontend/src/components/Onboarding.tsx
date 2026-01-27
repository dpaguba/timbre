import { useEffect, useState } from "react";

import { downloadModel, fetchModels, formatBytes } from "../api";
import type { ModelState } from "../types";

interface Props {
  onDone: (model: string) => void;
}

const STEPS = ["What this is", "Choose a model", "Download"] as const;

/** Shown once, on the first run.
 *
 * The app cannot ship a model, so somebody has to choose one and wait for it.
 * That is the only unavoidable friction in the product, and the honest thing
 * is to explain it rather than to hide it behind a spinner.
 */
export default function Onboarding({ onDone }: Props) {
  const [step, setStep] = useState(0);
  const [models, setModels] = useState<ModelState[]>([]);
  const [chosen, setChosen] = useState("small");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchModels()
      .then((data) => setModels(data.models))
      .catch(() => setError("Could not read the model list from the backend."));
  }, []);

  useEffect(() => {
    if (step !== 2) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const data = await fetchModels();
        if (cancelled) return;
        setModels(data.models);
        const current = data.models.find((m) => m.name === chosen);
        if (current?.installed) onDone(chosen);
        if (current?.download?.state === "error") {
          setError(current.download.error ?? "The download failed.");
        }
      } catch {
        return;
      }
    };
    const id = window.setInterval(tick, 800);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [step, chosen, onDone]);

  const current = models.find((m) => m.name === chosen);
  const progress = current?.download
    ? Math.min(1, current.download.downloaded / Math.max(1, current.download.total))
    : 0;

  async function beginDownload() {
    setError(null);
    if (current?.installed) {
      onDone(chosen);
      return;
    }
    try {
      await downloadModel(chosen);
      setStep(2);
    } catch {
      setError("Could not start the download.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl py-10">
      <ol className="mb-10 flex gap-2" aria-label="Setup progress">
        {STEPS.map((name, i) => (
          <li key={name} className="flex flex-1 flex-col gap-2">
            <span
              className={`h-0.5 rounded-pill transition-colors ${i <= step ? "bg-ink" : "bg-hairline"}`}
            />
            <span className={`text-caption-uppercase uppercase ${i <= step ? "text-ink" : "text-muted-soft"}`}>
              {name}
            </span>
          </li>
        ))}
      </ol>

      {error && (
        <p role="alert" className="mb-6 rounded-xl border border-hairline bg-surface-card px-4 py-3 text-body-sm text-semantic-error">
          {error}
        </p>
      )}

      {step === 0 && (
        <div className="animate-rise">
          <h1 className="font-display text-display-lg text-ink">Welcome to Timbre</h1>
          <p className="mt-5 max-w-[54ch] text-body-md text-body">
            Drop in audio or video, get back one document. Recordings are
            transcribed by a model running on this computer, so nothing you add
            is uploaded and nothing leaves the machine.
          </p>
          <p className="mt-4 max-w-[54ch] text-body-md text-body">
            There is one exception, and it happens next: the model itself has to
            be downloaded once. After that the app works with the network off.
          </p>
          <button onClick={() => setStep(1)} className="btn-primary mt-10">
            Continue
          </button>
        </div>
      )}

      {step === 1 && (
        <div className="animate-rise">
          <h1 className="font-display text-display-lg text-ink">Choose a model</h1>
          <p className="mt-4 max-w-[54ch] text-body-md text-body">
            Bigger models hear accents, crosstalk and rare words better. Smaller
            ones finish sooner. You can add or remove models later.
          </p>

          <ul className="mt-8 space-y-3">
            {models.map((model) => {
              const active = model.name === chosen;
              return (
                <li key={model.name}>
                  <button
                    onClick={() => setChosen(model.name)}
                    aria-pressed={active}
                    className={`w-full rounded-xl border px-5 py-4 text-left transition
                      focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink ${
                        active ? "border-ink bg-surface-card" : "border-hairline bg-surface-card hover:border-muted"
                      }`}
                  >
                    <span className="flex flex-wrap items-baseline justify-between gap-x-4">
                      <span className="font-display text-display-sm text-ink">{model.name}</span>
                      <span className="text-body-sm text-muted">
                        {model.installed
                          ? `already downloaded, ${formatBytes(model.size_bytes)}`
                          : `${formatBytes(model.approx_bytes)} download`}
                      </span>
                    </span>
                    {model.name === "small" && (
                      <span className="mt-1 block text-body-sm text-muted-soft">
                        Recommended for most recordings.
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>

          <div className="mt-10 flex items-center gap-6">
            <button onClick={beginDownload} className="btn-primary">
              {current?.installed ? "Start using Timbre" : "Download and continue"}
            </button>
            <button onClick={() => setStep(0)} className="btn-text">
              Back
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="animate-rise">
          <h1 className="font-display text-display-lg text-ink">Downloading {chosen}</h1>
          <p className="mt-4 max-w-[54ch] text-body-md text-body">
            This happens once. The file is cached, so switching back to this
            model later costs nothing.
          </p>

          <div className="mt-8 h-1 w-full overflow-hidden rounded-pill bg-surface-strong">
            <div
              className="h-full bg-ink transition-all duration-500"
              style={{ width: `${Math.round(progress * 100)}%` }}
            />
          </div>
          <p className="mt-3 text-body-sm text-muted">
            {current?.download
              ? `${formatBytes(current.download.downloaded)} of about ${formatBytes(
                  current.download.total
                )}`
              : "Starting…"}
          </p>
        </div>
      )}
    </div>
  );
}
