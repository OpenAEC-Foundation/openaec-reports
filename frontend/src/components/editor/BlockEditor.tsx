import { useReportStore } from '@/stores/reportStore';
import type { EditorBlock, ContentBlock } from '@/types/report';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { SpacerEditor } from '@/components/blocks/SpacerEditor';
import { PageBreakEditor } from '@/components/blocks/PageBreakEditor';
import { CalculationEditor } from '@/components/blocks/CalculationEditor';
import { ParagraphEditor } from '@/components/blocks/ParagraphEditor';
import { CheckEditor } from '@/components/blocks/CheckEditor';
import { ImageEditor } from '@/components/blocks/ImageEditor';
import { TableEditor } from '@/components/blocks/TableEditor';
import { MapEditor } from '@/components/blocks/MapEditor';
import { BulletListEditor } from '@/components/blocks/BulletListEditor';
import { Heading2Editor } from '@/components/blocks/Heading2Editor';
import { SpreadsheetEditor } from '@/components/blocks/SpreadsheetEditor';

interface BlockEditorProps {
  block: EditorBlock;
  sectionId: string;
  isAppendix?: boolean;
}

export function BlockEditor({ block, sectionId, isAppendix }: BlockEditorProps) {
  const updateBlock = useReportStore((s) => s.updateBlock);
  const updateAppendixBlock = useReportStore((s) => s.updateAppendixBlock);

  function handleChange(updates: Partial<ContentBlock>) {
    if (isAppendix) {
      updateAppendixBlock(sectionId, block.id, updates);
    } else {
      updateBlock(sectionId, block.id, updates);
    }
  }

  return (
    <ErrorBoundary context={`${block.type} block`}>
      <BlockEditorInner block={block} onChange={handleChange} />
    </ErrorBoundary>
  );
}

function BlockEditorInner({
  block,
  onChange,
}: {
  block: EditorBlock;
  onChange: (updates: Partial<ContentBlock>) => void;
}) {
  switch (block.type) {
    case 'spacer':
      return <SpacerEditor block={block} onChange={onChange} />;
    case 'page_break':
      return <PageBreakEditor />;
    case 'calculation':
      return <CalculationEditor block={block} onChange={onChange} />;
    case 'paragraph':
      return <ParagraphEditor block={block} onChange={onChange} />;
    case 'check':
      return <CheckEditor block={block} onChange={onChange} />;
    case 'image':
      return <ImageEditor block={block} onChange={onChange} />;
    case 'table':
      return <TableEditor block={block} onChange={onChange} />;
    case 'map':
      return <MapEditor block={block} onChange={onChange} />;
    case 'bullet_list':
      return <BulletListEditor block={block} onChange={onChange} />;
    case 'heading_2':
      return <Heading2Editor block={block} onChange={onChange} />;
    case 'spreadsheet':
      return <SpreadsheetEditor block={block} onChange={onChange} />;
    case 'raw_flowable':
      return (
        <p className="text-xs italic text-oaec-text-faint">
          Raw flowable — niet bewerkbaar in de editor
        </p>
      );
    default:
      return null;
  }
}
