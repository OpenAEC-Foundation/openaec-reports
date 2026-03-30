import { useState } from 'react';

const inputClass =
  'w-full rounded border border-oaec-border px-2 py-1.5 text-sm focus:border-oaec-accent focus:ring-2 focus:ring-oaec-accent/20 outline-none';

interface ExtraFieldRowProps {
  fieldKey: string;
  fieldValue: string;
  onKeyChange: (key: string) => void;
  onValueChange: (value: string) => void;
  onRemove: () => void;
}

export function ExtraFieldRow({ fieldKey, fieldValue, onKeyChange, onValueChange, onRemove }: ExtraFieldRowProps) {
  const [localKey, setLocalKey] = useState(fieldKey);
  const [localValue, setLocalValue] = useState(fieldValue);

  return (
    <div className="flex items-center gap-2">
      <input
        type="text"
        className={`${inputClass} flex-1`}
        value={localKey}
        onChange={(e) => setLocalKey(e.target.value)}
        onBlur={() => {
          if (localKey !== fieldKey) onKeyChange(localKey);
        }}
        placeholder="Label"
      />
      <input
        type="text"
        className={`${inputClass} flex-1`}
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        onBlur={() => {
          if (localValue !== fieldValue) onValueChange(localValue);
        }}
        placeholder="Waarde"
      />
      <button
        onClick={onRemove}
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded text-oaec-text-faint hover:bg-oaec-danger-soft hover:text-oaec-danger"
        title="Verwijder veld"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
