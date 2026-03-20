import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { injectBrandStyles } from './config/injectBrandStyles';
import { applyTheme } from './components/chrome/settings/SettingsDialog';
import { getSetting } from './utils/settingsStore';
import './themes.css';
import './i18n/config';
import { App } from './App';
import './index.css';

injectBrandStyles();
applyTheme(getSetting("theme", "light"));

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
