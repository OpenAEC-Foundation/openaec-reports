# Fix: Block Editor bugfixes uit code review

Er zijn 4 bugs gevonden in de block editors. Fix ze in deze volgorde:

## Fix 1: UC-bar berekening in CheckEditor.tsx (KRITIEK)

**Probleem:** Bij UC = 1.0 en limit = 1.0 toont de balk slechts 50% gevuld. Een UC gelijk aan de limiet hoort een volle balk te zijn.

**Huidige code:**
```tsx
const ratio = Math.min(uc / limit, 2);
// ...
style={{ width: `${Math.min(ratio * 50, 100)}%` }}
```

**Fix:** Vervang door:
```tsx
style={{ width: `${Math.min((uc / limit) * 100, 100)}%` }}
```
De `ratio` variabele kan weg. UC = limit → 100%. UC > limit → clipt op 100% + rode kleur.

---

## Fix 2: ParagraphEditor cursor positie na tag insert

**Probleem:** Als je niets selecteert en op B/I/Sub/Sup drukt, wordt `<b></b>` ingevoegd met de cursor *achter* de closing tag. De cursor hoort *tussen* de tags te staan zodat je direct kunt typen.

**Huidige code in `insertTag()`:**
```tsx
const cursorPos = start + openTag.length + selected.length + closeTag.length;
el.setSelectionRange(cursorPos, cursorPos);
```

**Fix:** Pas de cursor logica aan:
```tsx
requestAnimationFrame(() => {
  el.focus();
  if (selected.length === 0) {
    // Cursor tussen de tags plaatsen
    const cursorPos = start + openTag.length;
    el.setSelectionRange(cursorPos, cursorPos);
  } else {
    // Cursor na de closing tag
    const cursorPos = start + openTag.length + selected.length + closeTag.length;
    el.setSelectionRange(cursorPos, cursorPos);
  }
});
```

---

## Fix 3: SpacerEditor commit per slider-stap

**Probleem:** De store wordt bij elke pixel-beweging van de slider geüpdatet. Alle andere editors gebruiken onBlur. Dit is inconsistent en veroorzaakt onnodige re-renders.

**Fix:** Split de handler — lokale state op `onChange`, store commit op `onPointerUp`:

```tsx
function handleInput(value: number) {
  setHeight(value);
}

function handleCommit() {
  onChange({ height_mm: height });
}

// In de JSX:
<input
  type="range"
  min={1}
  max={50}
  step={1}
  value={height}
  onChange={(e) => handleInput(Number(e.target.value))}
  onPointerUp={handleCommit}
  onKeyUp={handleCommit}
  className="w-full accent-gray-400"
/>
```

Doe hetzelfde voor de width sliders in **ImageEditor.tsx** en **MapEditor.tsx** — die hebben hetzelfde probleem. Overal waar `type="range"` staat: lokale state op onChange, store commit op onPointerUp + onKeyUp.

---

## Fix 4: ImageEditor foutafhandeling bij file upload

**Probleem:** `FileReader.readAsDataURL()` heeft geen `onerror` handler. Corrupte of te grote bestanden falen stilzwijgend.

**Fix:** Voeg error handling toe in `handleFile()`:

```tsx
const handleFile = useCallback(
  (file: File) => {
    // Validatie: max 10MB
    if (file.size > 10 * 1024 * 1024) {
      setError('Bestand is te groot (max 10 MB)');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      const base64Data = dataUrl.split(',')[1];
      if (base64Data) {
        const source: ImageSourceBase64 = {
          data: base64Data,
          media_type: getMediaType(file),
          filename: file.name,
        };
        onChange({ src: source });
        setUrlInput('');
        setError(null);
      }
    };
    reader.onerror = () => {
      setError('Kon bestand niet lezen. Probeer een ander bestand.');
    };
    reader.readAsDataURL(file);
  },
  [onChange],
);
```

Voeg `const [error, setError] = useState<string | null>(null);` toe aan de state. Toon de foutmelding onder de dropzone:

```tsx
{error && (
  <p className="text-xs text-red-500 mt-1">{error}</p>
)}
```

---

## Verificatie

Na alle fixes: `npm run dev`, laad `example_structural.json`, en test:
1. **CheckEditor:** Maak een check met UC = 0.85, limit = 1.0 → balk moet ~85% gevuld zijn (groen). Zet UC op 1.0 → balk moet 100% zijn (groen). Zet UC op 1.1 → balk 100% maar rood.
2. **ParagraphEditor:** Klik in een lege tekst, druk op B → cursor moet tussen `<b>` en `</b>` staan. Selecteer tekst, druk op I → tekst moet gewrapped zijn, cursor na closing tag.
3. **SpacerEditor:** Sleep de slider — geen flikkering, waarde update pas bij loslaten.
4. **ImageEditor:** Probeer een corrupt bestand (hernoem een .txt naar .png) → foutmelding moet verschijnen.
