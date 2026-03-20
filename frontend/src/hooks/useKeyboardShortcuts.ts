import { useEffect, useCallback } from "react";
import { useReportStore } from "@/stores/reportStore";
import { useApiStore } from "@/stores/apiStore";

interface ShortcutHandlers {
  onSave: () => void;
  onNew: () => void;
  onToggleShortcuts: () => void;
}

export function useKeyboardShortcuts({ onSave, onNew, onToggleShortcuts }: ShortcutHandlers) {
  const addBlockToActiveSection = useCallback((blockType: "paragraph" | "calculation" | "table") => {
    const state = useReportStore.getState();
    if (state.activeSection) {
      state.addNewBlock(state.activeSection, blockType);
    } else if (state.activeAppendix) {
      state.addNewAppendixBlock(state.activeAppendix, blockType);
    }
  }, []);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const target = e.target as HTMLElement;
      const isTyping = target.tagName === "TEXTAREA" || target.tagName === "INPUT" || target.isContentEditable;

      const mod = e.metaKey || e.ctrlKey;
      const shift = e.shiftKey;

      let key = "";
      if (mod) key += "ctrl+";
      if (shift) key += "shift+";
      key += e.key.toLowerCase();

      // Shortcuts that always work (even when typing)
      const alwaysActive: Record<string, () => void> = {
        "ctrl+s": () => onSave(),
        "ctrl+n": () => onNew(),
        "ctrl+z": () => useReportStore.getState().undo(),
        "ctrl+y": () => useReportStore.getState().redo(),
        "ctrl+shift+z": () => useReportStore.getState().redo(),
        "ctrl+enter": () => useApiStore.getState().generatePdf(),
      };

      const alwaysHandler = alwaysActive[key];
      if (alwaysHandler) {
        e.preventDefault();
        alwaysHandler();
        return;
      }

      // Shortcuts that only work when NOT typing
      if (!isTyping) {
        const contextual: Record<string, () => void> = {
          "ctrl+1": () => useReportStore.getState().setViewMode("editor"),
          "ctrl+2": () => useReportStore.getState().setViewMode("split"),
          "ctrl+3": () => useReportStore.getState().setViewMode("json"),
          "ctrl+4": () => useReportStore.getState().setViewMode("preview"),
          "ctrl+shift+p": () => addBlockToActiveSection("paragraph"),
          "ctrl+shift+k": () => addBlockToActiveSection("calculation"),
          "ctrl+shift+t": () => addBlockToActiveSection("table"),
          "escape": () => useReportStore.getState().setActiveBlock(null),
        };

        const contextHandler = contextual[key];
        if (contextHandler) {
          e.preventDefault();
          contextHandler();
          return;
        }

        // ? key for help (no modifier)
        if (e.key === "?" && !mod && !e.altKey) {
          e.preventDefault();
          onToggleShortcuts();
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onSave, onToggleShortcuts, addBlockToActiveSection]);
}
