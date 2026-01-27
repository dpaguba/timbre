import { useCallback, useEffect, useState } from "react";

import { baseName, hasMediaExtension, onFilesDropped, pickMediaFiles } from "../desktop";

interface Props {
  paths: string[];
  onChange: (paths: string[]) => void;
  disabled?: boolean;
  /** Bumped by the Open menu item. A counter, because a second ⌘O has to open
   * the panel again and a boolean already true would do nothing. */
  openRequest?: number;
}

/** The desktop drop target.
 *
 * Separate from the browser one on purpose: this deals in absolute paths, the
 * other in File objects. Merging them would mean a component whose every line
 * asks which mode it is in.
 */
export default function NativeDropzone({ paths, onChange, disabled, openRequest }: Props) {
  const [hovering, setHovering] = useState(false);
  const [rejected, setRejected] = useState<string | null>(null);

  const add = useCallback(
    (incoming: string[]) => {
      const accepted: string[] = [];
      const refused: string[] = [];
      for (const path of incoming) {
        if (!hasMediaExtension(path)) refused.push(baseName(path));
        else if (!paths.includes(path)) accepted.push(path);
      }

      setRejected(refused.length ? `Not audio or video: ${refused.join(", ")}` : null);
      if (accepted.length) onChange([...paths, ...accepted]);
    },
    [paths, onChange]
  );

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    let cancelled = false;

    onFilesDropped(
      (dropped) => {
        if (disabled) return;
        add(dropped);
      },
      (isOver) => setHovering(isOver && !disabled)
    ).then((off) => {
      if (cancelled) off();
      else unlisten = off;
    });

    return () => {
      cancelled = true;
      unlisten?.();
    };
  }, [add, disabled]);

  useEffect(() => {
    if (openRequest) void browse();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openRequest]);

  async function browse() {
    if (disabled) return;
    const picked = await pickMediaFiles();
    if (picked.length) add(picked);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Choose audio or video files"
        onClick={browse}
        onKeyDown={(e) => {
          if (!disabled && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            void browse();
          }
        }}
        className={`relative flex cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xxl
          border border-dashed px-8 py-16 text-center transition
          focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink ${
            hovering
              ? "scale-[1.01] border-ink bg-canvas-soft"
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
          {hovering ? "Drop to add" : "Drop audio or video here"}
        </p>
        <p className="relative mt-3 max-w-sm text-body-sm text-muted">
          Any format. Files are read where they are, nothing is copied.
        </p>
      </div>

      {rejected && (
        <p role="alert" className="mt-3 text-body-sm text-semantic-error">
          {rejected}
        </p>
      )}

      {paths.length > 0 && (
        <ul className="mt-4 divide-y divide-hairline overflow-hidden rounded-xl border border-hairline bg-surface-card">
          {paths.map((path, i) => (
            <li key={path} className="flex items-center justify-between px-5 py-3 text-body-sm">
              <span className="truncate text-ink" title={path}>
                {baseName(path)}
              </span>
              {!disabled && (
                <button
                  onClick={() => onChange(paths.filter((_, index) => index !== i))}
                  className="ml-4 rounded-pill px-1 text-muted-soft transition hover:text-ink
                             focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
                  aria-label={`Remove ${baseName(path)}`}
                >
                  ✕
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
