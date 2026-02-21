import type { ParagraphBlock } from '@/types/report';
import { RichTextEditor } from './RichTextEditor';

interface ParagraphEditorProps {
  block: ParagraphBlock & { id: string };
  onChange: (updates: Partial<ParagraphBlock>) => void;
}

export function ParagraphEditor({ block, onChange }: ParagraphEditorProps) {
  return (
    <div className="space-y-3">
      {/* Style selector (H1, H2, H3, Normal) */}
      <div className="flex gap-2">
        <label className="text-sm text-gray-500">Stijl:</label>
        <select
          value={block.style || 'Normal'}
          onChange={(e) => onChange({ style: e.target.value })}
          className="text-sm border border-gray-200 rounded px-2 py-1"
        >
          <option value="Normal">Normaal</option>
          <option value="Heading1">Heading 1</option>
          <option value="Heading2">Heading 2</option>
          <option value="Heading3">Heading 3</option>
        </select>
      </div>

      {/* Rich text editor */}
      <RichTextEditor
        content={block.text || ''}
        onChange={(html) => onChange({ text: html })}
        placeholder="Typ hier je tekst..."
      />
    </div>
  );
}
