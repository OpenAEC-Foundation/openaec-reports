import type { Heading2Block } from '@/types/report';

interface Heading2EditorProps {
  block: Heading2Block;
  onChange: (updates: Partial<Heading2Block>) => void;
}

export function Heading2Editor({ block, onChange }: Heading2EditorProps) {
  return (
    <div className="space-y-2">
      <label className="block text-xs font-medium text-gray-500">Subkop</label>
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={block.number}
          onChange={(e) => onChange({ number: e.target.value })}
          placeholder="1.1"
          className="w-20 rounded border border-gray-200 px-2 py-1.5 text-sm font-mono focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none"
        />
        <input
          type="text"
          value={block.title}
          onChange={(e) => onChange({ title: e.target.value })}
          placeholder="Subtitel"
          className="flex-1 rounded border border-gray-200 px-2 py-1.5 text-sm font-semibold focus:border-blue-300 focus:ring-2 focus:ring-blue-100 outline-none"
        />
      </div>
    </div>
  );
}
