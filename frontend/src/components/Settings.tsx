import Checkbox from "./Checkbox";
import Select from "./Select";
import type { OutputFormat, TranscribeOptions } from "../types";

interface Props {
  options: TranscribeOptions;
  models: string[];
  onChange: (options: TranscribeOptions) => void;
  disabled?: boolean;
  /** Navigates to the models page. */
  onOpenModels: () => void;
}

const FORMATS = [
  { value: "txt", label: "Plain text", hint: ".txt" },
  { value: "md", label: "Markdown", hint: ".md" },
  { value: "docx", label: "Word", hint: ".docx" },
];

/** Short enough to read inside the closed select; the panel carries the rest. */
const MODEL_HINT: Record<string, string> = {
  tiny: "fastest",
  base: "fast",
  small: "recommended",
  medium: "accurate",
  "large-v3": "most accurate",
};

export default function Settings({ options, models, onChange, disabled, onOpenModels }: Props) {
  function set<K extends keyof TranscribeOptions>(key: K, value: TranscribeOptions[K]) {
    onChange({ ...options, [key]: value });
  }

  return (
    <div className="space-y-8">
      <div>
        <Select
          label="Model"
          value={options.model}
          disabled={disabled}
          onChange={(value) => set("model", value)}
          options={models.map((m) => ({ value: m, label: m, hint: MODEL_HINT[m] }))}
        />
        <button type="button" onClick={onOpenModels} className="btn-text mt-3">
          Which model should I pick?
        </button>
      </div>

      <Select
        label="Output format"
        value={options.output_format}
        disabled={disabled}
        onChange={(value) => set("output_format", value as OutputFormat)}
        options={FORMATS}
      />

      <Checkbox
        checked={options.include_timestamps}
        disabled={disabled}
        onChange={(checked) => set("include_timestamps", checked)}
        label="Include timestamps"
        hint="Each line prefixed with its position in the recording."
      />

    </div>
  );
}
