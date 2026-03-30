import { useApiStore } from '@/stores/apiStore';

export function ValidationBanner() {
  const validationErrors = useApiStore((s) => s.validationErrors);
  const clearValidation = useApiStore((s) => s.clearValidation);

  if (validationErrors.length === 0) return null;

  return (
    <div className="border-b border-oaec-border bg-oaec-danger-soft px-4 py-2">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-oaec-danger mb-1">
            Validatie fouten ({validationErrors.length})
          </p>
          <ul className="space-y-0.5">
            {validationErrors.map((err, i) => (
              <li key={i} className="text-xs text-oaec-danger">
                <span className="font-mono text-oaec-danger">{err.path}</span>{' '}
                {err.message}
              </li>
            ))}
          </ul>
        </div>
        <button
          onClick={clearValidation}
          className="shrink-0 flex h-5 w-5 items-center justify-center rounded text-oaec-danger hover:bg-oaec-danger-soft hover:text-oaec-danger"
          title="Sluiten"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
