import { useCallback, useEffect, useState } from 'react';

const KEY = 'ledger-theme';

function readInitial() {
  const fromDom = document.documentElement.dataset.theme;
  if (fromDom === 'light' || fromDom === 'dark') return fromDom;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function useTheme() {
  const [theme, setTheme] = useState(readInitial);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((current) => {
      const next = current === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem(KEY, next);
      } catch {
        // ignore: storage can be unavailable in private mode
      }
      return next;
    });
  }, []);

  return { theme, toggle };
}
