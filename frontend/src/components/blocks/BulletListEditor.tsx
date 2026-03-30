import type { BulletListBlock } from '@/types/report';

interface BulletListEditorProps {
  block: BulletListBlock;
  onChange: (updates: Partial<BulletListBlock>) => void;
}

export function BulletListEditor({ block, onChange }: BulletListEditorProps) {
  const items = block.items.length > 0 ? block.items : [''];

  function updateItem(index: number, value: string) {
    const next = [...items];
    next[index] = value;
    onChange({ items: next });
  }

  function addItem() {
    onChange({ items: [...items, ''] });
  }

  function removeItem(index: number) {
    if (items.length <= 1) return;
    onChange({ items: items.filter((_, i) => i !== index) });
  }

  function handleKeyDown(index: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const next = [...items];
      next.splice(index + 1, 0, '');
      onChange({ items: next });
      // Focus volgende input na render
      setTimeout(() => {
        const inputs = e.currentTarget.closest('.bullet-list-editor')?.querySelectorAll('input');
        inputs?.[index + 1]?.focus();
      }, 0);
    }
    if (e.key === 'Backspace' && items[index] === '' && items.length > 1) {
      e.preventDefault();
      removeItem(index);
    }
  }

  return (
    <div className="bullet-list-editor space-y-1.5">
      <label className="block text-xs font-medium text-oaec-text-muted mb-1">Opsomming</label>
      {items.map((item, index) => (
        <div key={index} className="group flex items-center gap-2">
          <span className="text-oaec-text-faint text-sm select-none">&bull;</span>
          <input
            type="text"
            value={item}
            onChange={(e) => updateItem(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            placeholder={`Item ${index + 1}`}
            className="flex-1 rounded border border-oaec-border px-2 py-1.5 text-sm focus:border-oaec-accent focus:ring-2 focus:ring-oaec-accent/20 outline-none"
          />
          {items.length > 1 && (
            <button
              onClick={() => removeItem(index)}
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-oaec-text-faint opacity-0 group-hover:opacity-100 hover:bg-oaec-danger-soft hover:text-oaec-danger transition-opacity"
              title="Verwijder item"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      ))}
      <button
        onClick={addItem}
        className="flex items-center gap-1 rounded px-2 py-1 text-xs text-oaec-text-faint hover:bg-oaec-accent-soft hover:text-oaec-accent transition-colors"
      >
        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Item toevoegen
      </button>
    </div>
  );
}
