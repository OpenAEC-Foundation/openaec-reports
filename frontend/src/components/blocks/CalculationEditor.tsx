import { useState } from 'react';
import type { CalculationBlock } from '@/types/report';

interface CalculationEditorProps {
  block: CalculationBlock & { id: string };
  onChange: (updates: Partial<CalculationBlock>) => void;
}

const inputClass =
  'w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none';
const monoInputClass = `${inputClass} font-mono`;
const labelClass = 'text-xs font-medium text-gray-500 mb-1';

export function CalculationEditor({ block, onChange }: CalculationEditorProps) {
  const [values, setValues] = useState({
    title: block.title,
    formula: block.formula ?? '',
    substitution: block.substitution ?? '',
    result: block.result ?? '',
    unit: block.unit ?? '',
    reference: block.reference ?? '',
  });

  function handleBlur() {
    const updates: Partial<CalculationBlock> = {};
    if (values.title !== block.title) updates.title = values.title;
    if (values.formula !== (block.formula ?? '')) updates.formula = values.formula || undefined;
    if (values.substitution !== (block.substitution ?? '')) updates.substitution = values.substitution || undefined;
    if (values.result !== (block.result ?? '')) updates.result = values.result || undefined;
    if (values.unit !== (block.unit ?? '')) updates.unit = values.unit || undefined;
    if (values.reference !== (block.reference ?? '')) updates.reference = values.reference || undefined;
    if (Object.keys(updates).length > 0) {
      onChange(updates);
    }
  }

  function handleChange(field: keyof typeof values, value: string) {
    setValues((prev) => ({ ...prev, [field]: value }));
  }

  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-3">
      {/* Title — full width */}
      <div className="col-span-2">
        <label className={labelClass}>Titel</label>
        <input
          type="text"
          className={inputClass}
          value={values.title}
          onChange={(e) => handleChange('title', e.target.value)}
          onBlur={handleBlur}
          placeholder="Naam van de berekening"
        />
      </div>

      {/* Formula */}
      <div className="col-span-2">
        <label className={labelClass}>Formule</label>
        <input
          type="text"
          className={monoInputClass}
          value={values.formula}
          onChange={(e) => handleChange('formula', e.target.value)}
          onBlur={handleBlur}
          placeholder="bijv. M_Ed = q × L² / 8"
        />
      </div>

      {/* Substitution */}
      <div className="col-span-2">
        <label className={labelClass}>Substitutie</label>
        <input
          type="text"
          className={monoInputClass}
          value={values.substitution}
          onChange={(e) => handleChange('substitution', e.target.value)}
          onBlur={handleBlur}
          placeholder="bijv. = 5.0 × 6.0² / 8"
        />
      </div>

      {/* Result + Unit */}
      <div>
        <label className={labelClass}>Resultaat</label>
        <input
          type="text"
          className={inputClass}
          value={values.result}
          onChange={(e) => handleChange('result', e.target.value)}
          onBlur={handleBlur}
          placeholder="bijv. 22.5"
        />
      </div>
      <div>
        <label className={labelClass}>Eenheid</label>
        <input
          type="text"
          className={inputClass}
          value={values.unit}
          onChange={(e) => handleChange('unit', e.target.value)}
          onBlur={handleBlur}
          placeholder="bijv. kNm"
        />
      </div>

      {/* Reference */}
      <div className="col-span-2">
        <label className={labelClass}>Referentie</label>
        <input
          type="text"
          className={inputClass}
          value={values.reference}
          onChange={(e) => handleChange('reference', e.target.value)}
          onBlur={handleBlur}
          placeholder="bijv. NEN-EN 1992-1-1 §6.1"
        />
      </div>
    </div>
  );
}
