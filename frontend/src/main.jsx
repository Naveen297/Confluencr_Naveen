import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import '@fontsource/public-sans/400.css';
import '@fontsource/public-sans/500.css';
import '@fontsource/public-sans/600.css';
import '@fontsource/public-sans/700.css';
import '@fontsource/spectral/500.css';
import '@fontsource/spectral/600.css';

import './styles/tokens.css';
import './styles/base.css';
import './styles/layout.css';
import './styles/account.css';
import './styles/ledger.css';
import './styles/overlays.css';

import App from './App';
import { ToastProvider } from './components/Toasts';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ToastProvider>
      <App />
    </ToastProvider>
  </StrictMode>,
);
