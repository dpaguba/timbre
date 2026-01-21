import { useEffect, useId, useRef, useState } from "react";

export interface SelectOption {
  value: string;
  label: string;
  hint?: string;
}

interface Props {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  disabled?: boolean;
}

/** A listbox that replaces the native select.
 *
 * Everything the native control gives away for free is re-implemented here on
 * purpose: arrows, Home, End, Escape, type-ahead, and an announced active
 * option. A custom control that drops those is a downgrade wearing a redesign.
 */
export default function Select({ label, value, options, onChange, disabled }: Props) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(() =>
    Math.max(0, options.findIndex((o) => o.value === value))
  );
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const typeAhead = useRef({ query: "", at: 0 });
  const id = useId();

  const selected = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    listRef.current?.querySelector<HTMLElement>(`[data-index="${activeIndex}"]`)?.scrollIntoView({
      block: "nearest",
    });
  }, [open, activeIndex]);

  function commit(index: number) {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    setOpen(false);
    buttonRef.current?.focus();
  }

  function openList() {
    setActiveIndex(Math.max(0, options.findIndex((o) => o.value === value)));
    setOpen(true);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (disabled) return;

    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) {
        e.preventDefault();
        openList();
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, options.length - 1));
        return;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
        return;
      case "Home":
        e.preventDefault();
        setActiveIndex(0);
        return;
      case "End":
        e.preventDefault();
        setActiveIndex(options.length - 1);
        return;
      case "Enter":
      case " ":
        e.preventDefault();
        commit(activeIndex);
        return;
      case "Escape":
        e.preventDefault();
        setOpen(false);
        buttonRef.current?.focus();
        return;
      case "Tab":
        setOpen(false);
        return;
    }

    if (e.key.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey) {
      const now = Date.now();
      const state = typeAhead.current;
      state.query = now - state.at > 1000 ? e.key : state.query + e.key;
      state.at = now;
      const match = options.findIndex((o) => o.label.toLowerCase().startsWith(state.query.toLowerCase()));
      if (match >= 0) setActiveIndex(match);
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <span id={`${id}-label`} className="label">
        {label}
      </span>

      <button
        ref={buttonRef}
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-labelledby={`${id}-label`}
        aria-controls={open ? `${id}-list` : undefined}
        aria-activedescendant={open ? `${id}-option-${activeIndex}` : undefined}
        disabled={disabled}
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={onKeyDown}
        className="field"
      >
        <span className="truncate">{selected?.label ?? "Select"}</span>
        <svg
          width="12"
          height="8"
          viewBox="0 0 12 8"
          fill="none"
          aria-hidden="true"
          className={`ml-3 shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        >
          <path d="M1 1.5 6 6.5 11 1.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>

      {open && (
        <ul
          ref={listRef}
          id={`${id}-list`}
          role="listbox"
          aria-labelledby={`${id}-label`}
          tabIndex={-1}
          className="animate-panel absolute z-30 mt-2 max-h-64 w-full overflow-auto rounded-xxl border border-hairline
                     bg-surface-card p-2 shadow-soft scroll-clean"
        >
          {options.map((option, index) => {
            const isSelected = option.value === value;
            const isActive = index === activeIndex;
            return (
              // eslint-disable-next-line jsx-a11y/click-events-have-key-events
              <li
                key={option.value}
                id={`${id}-option-${index}`}
                data-index={index}
                role="option"
                aria-selected={isSelected}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => commit(index)}
                className={`cursor-pointer rounded-pill px-4 py-2.5 text-body-sm transition-colors ${
                  isActive ? "bg-surface-strong text-ink" : "text-body"
                }`}
              >
                <span className={isSelected ? "text-ink" : undefined}>{option.label}</span>
                {option.hint && <span className="ml-2 text-muted-soft">{option.hint}</span>}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
