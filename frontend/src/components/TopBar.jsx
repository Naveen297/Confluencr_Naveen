import { BrandMark, Icon } from './Icon';

export function TopBar({ theme, onToggleTheme, onOpenMenu }) {
  const next = theme === 'dark' ? 'light' : 'dark';

  return (
    <header className="topbar">
      <div className="topbar__left">
        <button className="icon-btn topbar__menu" onClick={onOpenMenu} aria-label="Show accounts">
          <Icon name="menu" />
        </button>
        <a className="brand" href="/" aria-label="Ledger home">
          <BrandMark />
          <span className="brand__name">Ledger</span>
        </a>
      </div>

      <nav className="topbar__right" aria-label="Utilities">
        <a
          className="topbar__link"
          href="/api/docs"
          target="_blank"
          rel="noreferrer"
          aria-label="API docs (opens in a new tab)"
          title="Interactive API documentation"
        >
          <Icon name="book" size={16} />
          <span>API docs</span>
        </a>
        <button
          className="theme-toggle"
          onClick={onToggleTheme}
          aria-label={`Switch to ${next} theme`}
          title={`Switch to ${next} theme`}
        >
          <span className={`theme-toggle__thumb theme-toggle__thumb--${theme}`}>
            <Icon name={theme === 'dark' ? 'moon' : 'sun'} size={14} strokeWidth={2} />
          </span>
        </button>
      </nav>
    </header>
  );
}
