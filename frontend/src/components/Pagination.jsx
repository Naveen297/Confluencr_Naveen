import { Icon } from './Icon';

const PAGE_SIZES = [10, 20, 50];

function pageItems(page, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const items = [1];
  const start = Math.max(2, page - 1);
  const end = Math.min(total - 1, page + 1);
  if (start > 2) items.push('gap-start');
  for (let p = start; p <= end; p++) items.push(p);
  if (end < total - 1) items.push('gap-end');
  items.push(total);
  return items;
}

export function Pagination({ pagination, onPage, onLimit }) {
  const { page, limit, total_records: total, total_pages: pages, has_next, has_previous } = pagination;
  const from = total === 0 ? 0 : (page - 1) * limit + 1;
  const to = Math.min(page * limit, total);

  return (
    <footer className="pager">
      <p className="pager__summary">
        {total === 0 ? (
          'No entries'
        ) : (
          <>
            Showing <strong className="num">{from}–{to}</strong> of <strong className="num">{total}</strong>
          </>
        )}
      </p>

      <div className="pager__controls">
        <label className="pager__size">
          <span>Rows</span>
          <select className="select" value={limit} onChange={(e) => onLimit(Number(e.target.value))}>
            {PAGE_SIZES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>

        <nav className="pager__pages" aria-label="Pagination">
          <button
            className="icon-btn"
            onClick={() => onPage(page - 1)}
            disabled={!has_previous}
            aria-label="Previous page"
          >
            <Icon name="chevronLeft" size={16} />
          </button>
          {pages > 0 &&
            pageItems(page, pages).map((item) =>
              typeof item === 'number' ? (
                <button
                  key={item}
                  className={`pager__page num ${item === page ? 'is-active' : ''}`}
                  onClick={() => onPage(item)}
                  aria-current={item === page ? 'page' : undefined}
                  aria-label={`Page ${item}`}
                >
                  {item}
                </button>
              ) : (
                <span key={item} className="pager__gap" aria-hidden="true">
                  …
                </span>
              ),
            )}
          <button className="icon-btn" onClick={() => onPage(page + 1)} disabled={!has_next} aria-label="Next page">
            <Icon name="chevronRight" size={16} />
          </button>
        </nav>
      </div>
    </footer>
  );
}
