import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { LoginPage } from '@/components/auth/LoginPage';
import { RegisterPage } from '@/components/auth/RegisterPage';
import { OidcCallback } from '@/components/auth/OidcCallback';
import { useReportStore, STORAGE_KEY } from '@/stores/reportStore';
import { useApiStore } from '@/stores/apiStore';
import { useAuthStore } from '@/stores/authStore';
import exampleData from '../schemas/example_structural.json';
import type { ReportDefinition } from '@/types/report';

function LoadingSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <svg
          className="mx-auto h-8 w-8 animate-spin text-gray-400"
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
        <p className="mt-3 text-sm text-gray-500">Laden...</p>
      </div>
    </div>
  );
}

type AuthView = 'login' | 'register';

export function App() {
  const user = useAuthStore((s) => s.user);
  const isAuthLoading = useAuthStore((s) => s.isLoading);
  const checkSession = useAuthStore((s) => s.checkSession);
  const registrationEnabled = useAuthStore((s) => s.registrationEnabled);
  const checkRegistrationEnabled = useAuthStore((s) => s.checkRegistrationEnabled);
  const loadReport = useReportStore((s) => s.loadReport);
  const [authView, setAuthView] = useState<AuthView>('login');

  // Check bestaande sessie en registratie status bij startup
  useEffect(() => {
    checkSession();
    checkRegistrationEnabled();
  }, [checkSession, checkRegistrationEnabled]);

  // Restore from localStorage or load example data (alleen als ingelogd)
  useEffect(() => {
    if (!user) return;

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

  // OIDC callback route
  if (window.location.pathname === '/auth/callback') {
    return <OidcCallback />;
  }

  // Auth loading state
  if (isAuthLoading) {
    return <LoadingSpinner />;
  }

  // Niet ingelogd → login of registratie pagina
  if (!user) {
    if (authView === 'register' && registrationEnabled) {
      return <RegisterPage onSwitchToLogin={() => setAuthView('login')} />;
    }
    return (
      <LoginPage
        onSwitchToRegister={
          registrationEnabled ? () => setAuthView('register') : undefined
        }
      />
    );
  }

  // Ingelogd → editor
  return <AppShell />;
}
