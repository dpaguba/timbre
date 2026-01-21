import { useId } from "react";

interface Props {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  hint?: string;
  disabled?: boolean;
}

/** Ink square with a drawn tick.
 *
 * The real input stays in the DOM, visually hidden rather than replaced, so
 * the label association, focus order, form semantics and screen-reader
 * announcement all keep working. Only the box is ours.
 */
export default function Checkbox({ checked, onChange, label, hint, disabled }: Props) {
  const id = useId();

  return (
    <div className="flex items-start gap-3">
      <span className="relative mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(e) => onChange(e.target.checked)}
          className="peer absolute inset-0 h-full w-full cursor-pointer opacity-0 disabled:cursor-not-allowed"
        />
        <span
          aria-hidden="true"
          className={`pointer-events-none flex h-5 w-5 items-center justify-center rounded-xs border transition-colors
                      peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2
                      peer-focus-visible:outline-ink peer-disabled:opacity-40 ${
                        checked ? "border-ink bg-ink" : "border-hairline-strong bg-surface-card"
                      }`}
        >
          {checked && (
            <svg width="12" height="10" viewBox="0 0 12 10" fill="none">
              <path
                d="M1 5.2 4.3 8.5 11 1.5"
                stroke="#ffffff"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="animate-tick"
              />
            </svg>
          )}
        </span>
      </span>

      <label htmlFor={id} className="cursor-pointer select-none text-body-sm text-body">
        {label}
        {hint && <span className="mt-0.5 block text-muted-soft">{hint}</span>}
      </label>
    </div>
  );
}
