import { useTranslation } from "react-i18next";

interface ShortcutHelpProps {
  open: boolean;
  onClose: () => void;
}

function ShortcutGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider mb-1.5" style={{ color: "var(--theme-accent)" }}>{title}</h3>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Shortcut({ keys, action }: { keys: string; action: string }) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span style={{ color: "var(--theme-text)" }}>{action}</span>
      <kbd
        className="rounded px-2 py-0.5 text-xs font-mono"
        style={{ background: "var(--theme-bg-lighter)", color: "var(--theme-text-secondary)" }}
      >
        {keys}
      </kbd>
    </div>
  );
}

export function ShortcutHelp({ open, onClose }: ShortcutHelpProps) {
  const { t } = useTranslation();
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "var(--theme-dialog-overlay)" }}
      onClick={onClose}
    >
      <div
        className="w-[480px] rounded-xl p-6"
        style={{
          background: "var(--theme-dialog-bg)",
          border: "1px solid var(--theme-dialog-border)",
          boxShadow: "var(--theme-dialog-shadow)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--theme-dialog-header-text)" }}>
          {t("shortcuts")}
        </h2>

        <div className="space-y-4 text-sm">
          <ShortcutGroup title={t("shortcutGroups.document")}>
            <Shortcut keys="Ctrl+N" action={t("shortcutActions.new")} />
            <Shortcut keys="Ctrl+S" action={t("shortcutActions.save")} />
            <Shortcut keys="Ctrl+Z" action={t("shortcutActions.undo")} />
            <Shortcut keys="Ctrl+Y" action={t("shortcutActions.redo")} />
            <Shortcut keys="Ctrl+Enter" action={t("shortcutActions.generatePdf")} />
          </ShortcutGroup>

          <ShortcutGroup title={t("shortcutGroups.view")}>
            <Shortcut keys="Ctrl+1" action={t("shortcutActions.editor")} />
            <Shortcut keys="Ctrl+2" action={t("shortcutActions.split")} />
            <Shortcut keys="Ctrl+3" action="JSON" />
            <Shortcut keys="Ctrl+4" action={t("shortcutActions.preview")} />
          </ShortcutGroup>

          <ShortcutGroup title={t("shortcutGroups.addBlocks")}>
            <Shortcut keys="Ctrl+Shift+P" action={t("shortcutActions.paragraph")} />
            <Shortcut keys="Ctrl+Shift+K" action={t("shortcutActions.calculation")} />
            <Shortcut keys="Ctrl+Shift+T" action={t("shortcutActions.table")} />
          </ShortcutGroup>

          <ShortcutGroup title={t("shortcutGroups.navigation")}>
            <Shortcut keys="Escape" action={t("shortcutActions.deselect")} />
            <Shortcut keys="?" action={t("shortcutActions.help")} />
          </ShortcutGroup>
        </div>

        <button
          onClick={onClose}
          className="mt-4 w-full rounded-lg py-2 text-sm font-medium transition-colors"
          style={{
            background: "var(--theme-btn-secondary-bg)",
            color: "var(--theme-btn-secondary-text)",
            border: "1px solid var(--theme-border)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--theme-btn-secondary-hover-bg)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "var(--theme-btn-secondary-bg)";
          }}
        >
          {t("close")}
        </button>
      </div>
    </div>
  );
}
