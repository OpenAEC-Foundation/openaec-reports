import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { injectBrandStyles } from './config/injectBrandStyles';
import { App } from './App';
import './index.css';

injectBrandStyles();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
