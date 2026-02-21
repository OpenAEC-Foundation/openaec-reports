import { useState } from 'react';
import type { CheckBlock } from '@/types/report';

interface CheckEditorProps {
  block: CheckBlock & { id: string };
  onChange: (updates: Partial<CheckBlock>) => void;
}

const inputClass =
  'w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none';
const labelClass = 'text-xs font-medium text-gray-500 mb-1';

export function CheckEditor({ block, onChange }: CheckEditorProps) {
  const [values, setValues] = useState({
    description: block.description,
    required_value: block.required_value ?? '',
    calculated_value: block.calculated_value ?? '',
    unity_check: block.unity_check ?? 0,
    limit: block.limit ?? 1.0,
    reference: block.reference ?? '',
  });

  function handleChange(field: keyof typeof values, value: string | number) {
    setValues((prev) => ({ ...prev, [field]: value }));
  }

  function handleTextBlur() {
    const updates: Partial<CheckBlock> = {};
    if (values.description !== block.description) updates.description = values.description;
    if (values.required_value !== (block.required_value ?? '')) updates.required_value = values.required_value || undefined;
    if (values.calculated_value !== (block.calculated_value ?? '')) updates.calculated_value = values.calculated_value || undefined;
    if (values.reference !== (block.reference ?? '')) updates.reference = values.reference || undefined;
    if (Object.keys(updates).length > 0) {
      onChange(updates);
    }
  }

  function handleNumberBlur() {
    const updates: Partial<CheckBlock> = {};
    if (values.unity_check !== (block.unity_check ?? 0)) updates.unity_check = values.unity_check;
    if (values.limit !== (block.limit ?? 1.0)) updates.limit = values.limit;
    if (Object.keys(updates).length > 0) {
      onChange(updates);
    }
  }

  const uc = values.unity_check;
  const limit = values.limit || 1.0;
  const pass = uc <= limit;

  return (
    <div className="space-y-3">
      {/* Description — full width */}
      <div>
        <label className={labelClass}>Omschrijving</label>
        <input
          type="text"
          className={inputClass}
          value={values.description}
          onChange={(e) => handleChange('description', e.target.value)}
          onBlur={handleTextBlur}
          placeholder="Beschrijving van de toets"
        />
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3">
        {/* Required value */}
        <div>
          <label className={labelClass}>Eis</label>
          <input
            type="text"
            className={inputClass}
            value={values.required_value}
            onChange={(e) => handleChange('required_value', e.target.value)}
            onBlur={handleTextBlur}
            placeholder="bijv. M_Rd ≥ M_Ed"
          />
        </div>

        {/* Calculated value */}
        <div>
          <label className={labelClass}>Berekende waarde</label>
          <input
            type="text"
            className={inputClass}
            value={values.calculated_value}
            onChange={(e) => handleChange('calculated_value', e.target.value)}
            onBlur={handleTextBlur}
            placeholder="bijv. 45.2 kNm"
          />
        </div>

        {/* Unity check */}
        <div>
          <label className={labelClass}>Unity check (UC)</label>
          <input
            type="number"
            step={0.01}
            min={0}
            className={inputClass}
            value={values.unity_check}
            onChange={(e) => handleChange('unity_check', parseFloat(e.target.value) || 0)}
            onBlur={handleNumberBlur}
          />
        </div>

        {/* Limit */}
        <div>
          <label className={labelClass}>Limiet</label>
          <input
            type="number"
            step={0.01}
            min={0}
            className={inputClass}
            value={values.limit}
            onChange={(e) => handleChange('limit', parseFloat(e.target.value) || 1.0)}
            onBlur={handleNumberBlur}
          />
        </div>
      </div>

      {/* Reference */}
      <div>
        <label className={labelClass}>Referentie</label>
        <input
          type="text"
          className={inputClass}
          value={values.reference}
          onChange={(e) => handleChange('reference', e.target.value)}
          onBlur={handleTextBlur}
          placeholder="bijv. NEN-EN 1993-1-1 §6.2.5"
        />
      </div>

      {/* UC bar */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className={`font-semibold ${pass ? 'text-green-600' : 'text-red-600'}`}>
            UC = {uc.toFixed(2)} / {limit.toFixed(2)}
          </span>
          <span className={`font-semibold ${pass ? 'text-green-600' : 'text-red-600'}`}>
            {pass ? 'VOLDOET' : 'VOLDOET NIET'}
          </span>
        </div>
        <div className="h-3 w-full rounded-full bg-gray-100 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${pass ? 'bg-green-500' : 'bg-red-500'}`}
            style={{ width: `${Math.min((uc / limit) * 100, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
