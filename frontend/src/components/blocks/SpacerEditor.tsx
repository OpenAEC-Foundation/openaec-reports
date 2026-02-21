import { useState } from 'react';
import type { SpacerBlock } from '@/types/report';

interface SpacerEditorProps {
  block: SpacerBlock & { id: string };
  onChange: (updates: Partial<SpacerBlock>) => void;
}

export function SpacerEditor({ block, onChange }: SpacerEditorProps) {
  const [height, setHeight] = useState(block.height_mm ?? 5);

  function handleInput(value: number) {
    setHeight(value);
  }

  function handleCommit() {
    onChange({ height_mm: height });
  }

  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-gray-500">
        Hoogte: {height} mm
      </label>
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
      <div className="flex justify-between text-[10px] text-gray-400">
        <span>1 mm</span>
        <span>50 mm</span>
      </div>
    </div>
  );
}
