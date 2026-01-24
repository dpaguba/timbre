import { useEffect, useState } from "react";

import { downloadModel, fetchModels, formatBytes, removeModel } from "../api";
import type { ModelState } from "../types";

interface ModelInfo {
  name: string;
  download: string;
  speed: string;
  pick: string;
}
/** Sizes are the faster-whisper int8 downloads; speed is relative to `small`
 * on a laptop CPU, which is what this tool runs on by default. */
const MODELS: ModelInfo[] = [
  {
    name: "tiny",
    download: "~75 MB",
    speed: "about 5x faster",
    pick: "Checking that the setup works, or a clean recording of one speaker where a stray word costs nothing.",
  },
  {
    name: "base",
    download: "~145 MB",
    speed: "about 3x faster",
    pick: "Short notes and voice memos in one language. Noticeably better than tiny on names and numbers.",
  },
  {
    name: "small",
    download: "~480 MB",
    speed: "baseline",
    pick: "The default, and the right answer most of the time. Handles accents and background noise without much loss.",
  },
  {
    name: "medium",
    download: "~1.5 GB",
    speed: "about 2x slower",
    pick: "Interviews, several speakers, or audio you cannot re-record. Worth the wait when the transcript is the deliverable.",
  },
  {
    name: "large-v3",
    download: "~3 GB",
    speed: "about 4x slower",
    pick: "Difficult audio: heavy accents, crosstalk, technical vocabulary, or languages other than English where accuracy matters most.",
  },
];

interface Props {
  onBack: () => void;
  onChanged?: () => void;
}

/** The models page.
 *
 * This used to be a slide-over. As a page it can be navigated to, linked from
 * the menu, and left with the back control people already look for, instead of
 * being a layer that traps focus over the work.
 */
export default function ModelsView({ onBack, onChanged }: Props) {
  const [state, setState] = useState<ModelState[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      try {
        const data = await fetchModels();
        if (!cancelled) setState(data.models);
      } catch {
        return;
      }
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onBack();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onBack]);

  async function act(name: string, action: "download" | "remove") {
    setBusy(name);
    setError(null);
    try {
      await (action === "download" ? downloadModel(name) : removeModel(name));
      const data = await fetchModels();
      setState(data.models);
      onChanged?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "That did not work.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <button onClick={onBack} className="btn-text mb-8 inline-flex items-center gap-2">
        <span aria-hidden="true">&#8592;</span> Back
      </button>

      <h1 className="font-display text-display-lg text-ink">Which model should I pick?</h1>
      <p className="mt-4 max-w-[54ch] text-body-md text-body">
        Every model transcribes the same way. They differ in how much they get
        right and how long they take. Bigger models hear accents, crosstalk and
        rare words better; smaller ones finish sooner.
      </p>

      {error && (
        <p role="alert" className="mt-6 rounded-xl border border-hairline bg-surface-card px-4 py-3 text-body-sm text-semantic-error">
          {error}
        </p>
      )}

      <ul className="mt-8 space-y-4">
        {MODELS.map((model) => {
          const live = state.find((m) => m.name === model.name);
          const downloading = live?.download?.state === "running";
          const progress = downloading
            ? Math.min(1, live!.download!.downloaded / Math.max(1, live!.download!.total))
            : 0;
          return (
            <li key={model.name} className="card p-5">
              <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                <span className="font-display text-display-sm text-ink">{model.name}</span>
                <span className="text-body-sm text-muted-soft">
                  {live?.installed ? `on disk, ${formatBytes(live.size_bytes)}` : model.download} · {model.speed}
                </span>
              </div>
              <p className="mt-2 text-body-sm text-body">{model.pick}</p>

              {downloading && (
                <div className="mt-3">
                  <div className="h-1 w-full overflow-hidden rounded-pill bg-surface-strong">
                    <div
                      className="h-full bg-ink transition-all duration-500"
                      style={{ width: `${Math.round(progress * 100)}%` }}
                    />
                  </div>
                  <p className="mt-2 text-body-sm text-muted">
                    {formatBytes(live!.download!.downloaded)} downloaded
                  </p>
                </div>
              )}

              {!downloading && (
                <div className="mt-4">
                  {live?.installed ? (
                    <button
                      onClick={() => act(model.name, "remove")}
                      disabled={busy === model.name}
                      className="btn-text"
                    >
                      {busy === model.name ? "Removing" : "Remove from disk"}
                    </button>
                  ) : (
                    <button
                      onClick={() => act(model.name, "download")}
                      disabled={busy === model.name}
                      className="btn-text"
                    >
                      {busy === model.name ? "Starting" : "Download"}
                    </button>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>

      <div className="mt-10 border-t border-hairline pt-6 text-body-sm text-muted">
        <p>
          The first run with a given model downloads it once and caches it. That
          download is the only time this tool touches the network. After it,
          everything happens on this machine, including when you are offline.
        </p>
        <p className="mt-3">
          Switching models later re-uses the cache, so trying{" "}
          <span className="text-ink">small</span> and then{" "}
          <span className="text-ink">medium</span> costs one download each, not
          one per run.
        </p>
      </div>
    </div>
  );
}
