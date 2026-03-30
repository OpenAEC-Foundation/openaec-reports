import type { Heading2Block } from '@/types/report';

interface Heading2EditorProps {
  block: Heading2Block;
  onChange: (updates: Partial<Heading2Block>) => void;
}

export function Heading2Editor({ block, onChange }: Heading2EditorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-xs font-medium text-oaec-text-muted">Subkop</label>
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={block.number}
          onChange={(e) => onChange({ number: e.target.value })}
          placeholder="1.1"
          className="w-20 rounded border border-oaec-border px-2 py-1.5 text-sm font-mono focus:border-oaec-accent focus:ring-2 focus:ring-oaec-accent/20 outline-none"
        />
        <input
          type="text"
          value={block.title}
          onChange={(e) => onChange({ title: e.target.value })}
          placeholder="Subtitel"
          className="flex-1 rounded border border-oaec-border px-2 py-1.5 text-sm font-semibold focus:border-oaec-accent focus:ring-2 focus:ring-oaec-accent/20 outline-none"
        />
      </div>
    </div>
  );
}
