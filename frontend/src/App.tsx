import { useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { useReportStore, STORAGE_KEY } from '@/stores/reportStore';
import { useApiStore } from '@/stores/apiStore';
import exampleData from '../schemas/example_structural.json';
import type { ReportDefinition } from '@/types/report';

export function App() {
  const loadReport = useReportStore((s) => s.loadReport);

  // Restore from localStorage or load example data
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const { report: savedReport, savedAt } = JSON.parse(saved);
        if (savedReport?.template && savedReport?.project) {
          loadReport(savedReport as ReportDefinition);
          useReportStore.setState({ lastSavedAt: savedAt ?? null });
          console.log(`Rapport hersteld van ${savedAt}`);
          return;
        }
      } catch {
        // Corrupte data — negeer
      }
    }
    loadReport(exampleData as ReportDefinition);
  }, [loadReport]);

  // Startup: check backend health, then load templates/brands
  useEffect(() => {
    const init = async () => {
      await useApiStore.getState().checkHealth();
      if (useApiStore.getState().connected) {
        await useApiStore.getState().loadTemplatesAndBrands();
      }
    };
    init();
  }, []);

  // Warn on close if dirty
  useEffect(() => {
    function handleBeforeUnload(e: BeforeUnloadEvent) {
      if (useReportStore.getState().isDirty) {
        e.preventDefault();
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  return <AppShell />;
}
