interface ShortcutHelpProps {
  open: boolean;
  onClose: () => void;
}

function ShortcutGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">{title}</h3>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Shortcut({ keys, action }: { keys: string; action: string }) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-gray-600">{action}</span>
      <kbd className="rounded bg-gray-100 px-2 py-0.5 text-xs font-mono text-gray-500">{keys}</kbd>
    </div>
  );
}

export function ShortcutHelp({ open, onClose }: ShortcutHelpProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="w-[480px] rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Sneltoetsen</h2>

        <div className="space-y-4 text-sm">
          <ShortcutGroup title="Document">
            <Shortcut keys="Ctrl+S" action="Export JSON" />
            <Shortcut keys="Ctrl+Z" action="Ongedaan maken" />
            <Shortcut keys="Ctrl+Y" action="Opnieuw" />
            <Shortcut keys="Ctrl+Enter" action="Genereer PDF" />
          </ShortcutGroup>

          <ShortcutGroup title="Weergave">
            <Shortcut keys="Ctrl+1" action="Editor" />
            <Shortcut keys="Ctrl+2" action="Split (editor + preview)" />
            <Shortcut keys="Ctrl+3" action="JSON" />
            <Shortcut keys="Ctrl+4" action="Preview" />
          </ShortcutGroup>

          <ShortcutGroup title="Blocks toevoegen">
            <Shortcut keys="Ctrl+Shift+P" action="Tekst" />
            <Shortcut keys="Ctrl+Shift+K" action="Berekening" />
            <Shortcut keys="Ctrl+Shift+T" action="Tabel" />
          </ShortcutGroup>

          <ShortcutGroup title="Navigatie">
            <Shortcut keys="Escape" action="Block deselecteren" />
            <Shortcut keys="?" action="Deze help" />
          </ShortcutGroup>
        </div>

        <button
          onClick={onClose}
          className="mt-4 w-full rounded-lg bg-gray-100 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 transition-colors"
        >
          Sluiten
        </button>
      </div>
    </div>
  );
}
