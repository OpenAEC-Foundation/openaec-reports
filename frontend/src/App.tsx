import { useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { LoginPage } from '@/components/auth/LoginPage';
import { useReportStore, STORAGE_KEY } from '@/stores/reportStore';
import { useApiStore } from '@/stores/apiStore';
import { useAuthStore } from '@/stores/authStore';
import exampleData from '../schemas/example_structural.json';
import type { ReportDefinition } from '@/types/report';

function LoadingSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center" style={{ background: 'var(--oaec-bg)' }}>
      <div className="text-center">
        <svg
          className="mx-auto h-8 w-8 animate-spin" style={{ color: 'var(--oaec-accent)' }}
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        <p className="mt-3 text-sm" style={{ color: 'var(--oaec-text-secondary)' }}>Laden...</p>
      </div>
    </div>
  );
}

export function App() {
  const user = useAuthStore((s) => s.user);
  const isAuthLoading = useAuthStore((s) => s.isLoading);
  const checkSession = useAuthStore((s) => s.checkSession);
  const loadReport = useReportStore((s) => s.loadReport);

  // Check huidige sessie via /api/auth/me — Caddy + Authentik forward_auth
  // levert de juiste headers aan de backend voor browser-traffic.
  useEffect(() => {
    checkSession();
  }, [checkSession]);

  // Restore from localStorage or load example data (alleen als ingelogd)
  useEffect(() => {
    if (!user) return;

    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const { report: savedReport, savedAt, serverReportId, serverProjectId, userId } = JSON.parse(saved);
        if (savedReport?.template && savedReport?.project) {
          loadReport(savedReport as ReportDefinition);
          // Alleen server IDs herstellen als ze van dezelfde user zijn
          const sameUser = userId === user.id;
          useReportStore.setState({
            lastSavedAt: savedAt ?? null,
            serverReportId: sameUser ? (serverReportId ?? null) : null,
            serverProjectId: sameUser ? (serverProjectId ?? null) : null,
          });
          if (!sameUser && (serverReportId || serverProjectId)) {
            console.log("Server IDs genegeerd — andere gebruiker");
          }
          console.log(`Rapport hersteld van ${savedAt}`);
          return;
        }
      } catch {
        // Corrupte data — negeer
      }
    }
    loadReport(exampleData as ReportDefinition);
  }, [user, loadReport]);

  // Startup: check backend health, then load templates/brands (alleen als ingelogd)
  useEffect(() => {
    if (!user) return;

    const init = async () => {
      await useApiStore.getState().checkHealth();
      if (useApiStore.getState().connected) {
        await useApiStore.getState().loadTemplatesAndBrands();
      }
    };
    init();
  }, [user]);

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

  // Auth loading state
  if (isAuthLoading) {
    return <LoadingSpinner />;
  }

  // Niet ingelogd → SSO splash (auto-redirect naar Authentik)
  if (!user) {
    return <LoginPage />;
  }

  // Ingelogd → editor
  return <AppShell />;
}
