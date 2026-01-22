import type { Language } from "../types";

interface Props {
  languages: Language[];
  selected: string[];
  onChange: (codes: string[]) => void;
  disabled?: boolean;
}

export default function LanguageSelect({ languages, selected, onChange, disabled }: Props) {
  function toggle(code: string) {
    if (selected.includes(code)) {
      onChange(selected.filter((c) => c !== code));
    } else {
      onChange([...selected, code]);
    }
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span id="language-group-label" className="mb-3 block text-caption-uppercase uppercase text-muted">Languages in the media</span>
        <span className="text-body-sm text-muted-soft">
          {selected.length === 0 ? "Auto-detect" : `${selected.length} selected`}
        </span>
      </div>
      <div role="group" aria-labelledby="language-group-label" className="flex flex-wrap gap-2">
        {languages.map((lang) => {
          const active = selected.includes(lang.code);
          return (
            <button
            aria-pressed={active}
              key={lang.code}
              type="button"
              disabled={disabled}
              onClick={() => toggle(lang.code)}
              className={`rounded-pill border px-3.5 py-1.5 text-body-sm transition
              focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink
              disabled:opacity-40 ${
                active
                  ? "border-ink bg-ink text-on-primary"
                  : "border-hairline-strong bg-surface-card text-body hover:border-muted hover:text-ink"
              }`}
              title={lang.name}
            >
              {lang.native}
            </button>
          );
        })}
      </div>
      <p className="mt-3 text-body-sm text-muted-soft">
        Pick one for a single-language file, or several when a file mixes languages.
        Leave empty to let Timbre detect automatically.
      </p>
    </div>
  );
}
