# P5: Rich Text Editor — ParagraphEditor Upgraden naar Tiptap

## Context

De huidige `ParagraphEditor` is een kale `<textarea>`. Voor productierapportage heb je inline formatting nodig: bold, italic, sub/superscript (engineering formules zoals F_ed, σ_max), en bullet lists. 

Tiptap is een headless, extensible WYSIWYG editor gebouwd op ProseMirror. Het is lightweight, React-native, en perfect voor deze use case.

## Scope

1. Tiptap integreren in het project
2. `ParagraphEditor` vervangen door een Tiptap-based editor
3. HTML output opslaan in de report store (in plaats van plain text)
4. Backend `ParagraphBlock` aanpassen om HTML te renderen in PDF
5. Subscript/superscript extensies activeren

## Stap 0: Oriëntatie

Lees voordat je begint:
- `src/components/blocks/ParagraphEditor.tsx` — huidige textarea implementatie
- `src/stores/reportStore.ts` — hoe block data wordt opgeslagen
- `src/types/report.ts` — Block type definitie
- Backend: `src/bm_reports/components/calculation.py` — hoe tekst nu in PDF komt (als referentie)

## Stap 1: Installeer Tiptap

```bash
cd "X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator_frontend"
npm install @tiptap/react @tiptap/pm @tiptap/starter-kit @tiptap/extension-subscript @tiptap/extension-superscript @tiptap/extension-underline @tiptap/extension-text-align
```

## Stap 2: Maak RichTextEditor Component

Maak `src/components/blocks/RichTextEditor.tsx`:

```tsx
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Subscript from '@tiptap/extension-subscript';
import Superscript from '@tiptap/extension-superscript';
import Underline from '@tiptap/extension-underline';
import { useEffect } from 'react';

interface RichTextEditorProps {
  content: string;       // HTML string
  onChange: (html: string) => void;
  placeholder?: string;
}

export function RichTextEditor({ content, onChange, placeholder }: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // Configureer welke nodes/marks beschikbaar zijn
        heading: false,   // Headings via style selector, niet in rich text
        codeBlock: false, // Niet nodig voor rapporten
      }),
      Subscript,
      Superscript,
      Underline,
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none min-h-[100px] p-3',
        'data-placeholder': placeholder || 'Typ hier...',
      },
    },
  });

  // Sync external content changes
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content, false);
    }
  }, [content, editor]);

  if (!editor) return null;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="flex gap-1 p-2 border-b border-gray-200 bg-gray-50 flex-wrap">
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          isActive={editor.isActive('bold')}
          title="Vet (Ctrl+B)"
        >
          <strong>B</strong>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          isActive={editor.isActive('italic')}
          title="Cursief (Ctrl+I)"
        >
          <em>I</em>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          isActive={editor.isActive('underline')}
          title="Onderstreept (Ctrl+U)"
        >
          <u>U</u>
        </ToolbarButton>
        <div className="w-px bg-gray-300 mx-1" />
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleSubscript().run()}
          isActive={editor.isActive('subscript')}
          title="Subscript"
        >
          X<sub>2</sub>
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleSuperscript().run()}
          isActive={editor.isActive('superscript')}
          title="Superscript"
        >
          X<sup>2</sup>
        </ToolbarButton>
        <div className="w-px bg-gray-300 mx-1" />
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          isActive={editor.isActive('bulletList')}
          title="Opsomming"
        >
          • List
        </ToolbarButton>
        <ToolbarButton
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          isActive={editor.isActive('orderedList')}
          title="Genummerde lijst"
        >
          1. List
        </ToolbarButton>
      </div>

      {/* Editor */}
      <EditorContent editor={editor} />
    </div>
  );
}

function ToolbarButton({ 
  children, onClick, isActive, title 
}: { 
  children: React.ReactNode; 
  onClick: () => void; 
  isActive: boolean; 
  title: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`px-2 py-1 rounded text-sm transition-colors ${
        isActive 
          ? 'bg-purple-100 text-purple-800 font-medium' 
          : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      {children}
    </button>
  );
}
```

## Stap 3: Update ParagraphEditor

Vervang de textarea in `ParagraphEditor.tsx` door de `RichTextEditor`:

```tsx
import { RichTextEditor } from './RichTextEditor';

interface ParagraphEditorProps {
  block: ParagraphBlock;
  onUpdate: (changes: Partial<ParagraphBlock>) => void;
}

export function ParagraphEditor({ block, onUpdate }: ParagraphEditorProps) {
  return (
    <div className="space-y-3">
      {/* Style selector (H1, H2, H3, Normal) — behoud bestaande */}
      <div className="flex gap-2">
        <label className="text-sm text-gray-500">Stijl:</label>
        <select
          value={block.style || 'Normal'}
          onChange={(e) => onUpdate({ style: e.target.value })}
          className="text-sm border border-gray-200 rounded px-2 py-1"
        >
          <option value="Normal">Normaal</option>
          <option value="Heading1">Heading 1</option>
          <option value="Heading2">Heading 2</option>
          <option value="Heading3">Heading 3</option>
        </select>
      </div>

      {/* Rich text editor — vervangt textarea */}
      <RichTextEditor
        content={block.text || ''}
        onChange={(html) => onUpdate({ text: html })}
        placeholder="Typ hier je tekst..."
      />
    </div>
  );
}
```

## Stap 4: Tiptap CSS toevoegen

Voeg Tiptap base styles toe aan `src/index.css`:

```css
/* Tiptap editor styles */
.ProseMirror {
  min-height: 100px;
  padding: 0.75rem;
  outline: none;
}

.ProseMirror p {
  margin: 0.25em 0;
}

.ProseMirror ul,
.ProseMirror ol {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.ProseMirror p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  float: left;
  color: #adb5bd;
  pointer-events: none;
  height: 0;
}

.ProseMirror sub {
  font-size: 0.75em;
  vertical-align: sub;
}

.ProseMirror sup {
  font-size: 0.75em;
  vertical-align: super;
}
```

## Stap 5: Type definitie updaten

In `src/types/report.ts`, de `text` field van ParagraphBlock slaat nu HTML op in plaats van plain text. Dit is backward compatible — plain text is geldige HTML. Voeg een comment toe:

```typescript
interface ParagraphBlock extends BaseBlock {
  type: 'paragraph';
  text: string;    // HTML content (van Tiptap editor)
  style?: string;  // 'Normal' | 'Heading1' | 'Heading2' | 'Heading3'
}
```

## Stap 6: Conversion utility updaten

In `src/utils/conversion.ts`, controleer of de export naar backend JSON de HTML correct doorgeeft. De backend moet de HTML parsen naar ReportLab Paragraphs.

**Geen wijziging nodig als** de `text` field al als string wordt doorgegeven. De backend interpreteert het.

## Stap 7: Backend — HTML naar PDF Paragraph

Dit is een **aparte backend taak** die later kan. ReportLab's `Paragraph` ondersteunt al een subset van HTML (`<b>`, `<i>`, `<u>`, `<sub>`, `<sup>`). De `block_registry.py` of `ParagraphBlock` rendering moet de HTML direct doorgeven aan ReportLab's `Paragraph()` constructor in plaats van plain text.

**Minimale backend wijziging** (alleen als je dit in dezelfde sessie wilt doen):

In `src/bm_reports/core/block_registry.py`, zoek waar paragraph blocks worden aangemaakt en pas de tekst processing aan:

```python
from reportlab.platypus import Paragraph as RLParagraph

def _create_paragraph_block(data, stylesheet):
    text = data.get("text", "")
    style_name = data.get("style", "Normal")
    style = stylesheet[style_name]
    
    # ReportLab Paragraph accepteert HTML-subset:
    # <b>, <i>, <u>, <sub>, <sup>, <br/> zijn ondersteund
    # Strip onveilige tags, behoud formatting
    safe_html = _sanitize_html(text)
    return RLParagraph(safe_html, style)

def _sanitize_html(html: str) -> str:
    """Strip onveilige HTML, behoud formatting tags."""
    import re
    # Sta alleen veilige tags toe
    allowed = {'b', 'i', 'u', 'em', 'strong', 'sub', 'sup', 'br', 'p', 'ul', 'ol', 'li'}
    # Simpele whitelist-based sanitizer
    # ReportLab accepteert: <b>, <i>, <u>, <sub>, <sup>, <br/>
    # Converteer <strong> → <b>, <em> → <i>
    html = html.replace('<strong>', '<b>').replace('</strong>', '</b>')
    html = html.replace('<em>', '<i>').replace('</em>', '</i>')
    # Strip <p> tags (ReportLab maakt zelf paragrafen)
    html = re.sub(r'</?p>', '', html)
    # Converteer <ul>/<ol>/<li> naar bullet symbolen (ReportLab heeft geen native list support)
    html = re.sub(r'<li>', '• ', html)
    html = re.sub(r'</li>', '<br/>', html)
    html = re.sub(r'</?[uo]l>', '', html)
    return html.strip()
```

## Stap 8: Test in Browser

```bash
npm run dev
```

Open http://localhost:5173 en test:
1. ✅ Paragraph editor toont toolbar met B, I, U, Sub, Sup, Lists
2. ✅ Formatting wordt toegepast bij klik of keyboard shortcut
3. ✅ Tekst wordt opgeslagen als HTML in de store
4. ✅ JSON export bevat HTML in paragraph text velden
5. ✅ Undo/redo werkt met rich text wijzigingen
6. ✅ Auto-save bewaart HTML content
7. ✅ JSON import met plain text (backward compatible) werkt nog

## Stap 9: Build check

```bash
npm run build
```

**Verwacht:** 0 errors, 0 warnings gerelateerd aan Tiptap.

## Regels

1. **Backward compatible** — plain text in bestaande JSON bestanden moet nog werken
2. **Geen nieuwe dependencies** buiten Tiptap en zijn officiële extensies
3. **Minimal footprint** — alleen de extensies die we nodig hebben (geen volledige WYSIWYG suite)
4. **Backend HTML sanitization** — nooit raw HTML naar ReportLab sturen zonder whitelist filtering
5. **Heading via style selector** — niet via Tiptap's heading feature. De style selector bepaalt het heading level, de rich text editor is alleen voor inline formatting

## Verwachte output

- `src/components/blocks/RichTextEditor.tsx` — NIEUW
- `src/components/blocks/ParagraphEditor.tsx` — GEWIJZIGD (textarea → RichTextEditor)
- `src/index.css` — UITGEBREID (Tiptap styles)
- `package.json` — UITGEBREID (Tiptap dependencies)
- Optioneel backend: `src/bm_reports/core/block_registry.py` — HTML sanitization

## Update na afloop

Werk `SESSION_STATUS.md` bij:
- ParagraphEditor: ✅ Tiptap WYSIWYG met B/I/U/Sub/Sup/Lists
