/**
 * Shared heading used by authenticated application pages.
 */

export function PageHeader({
  eyebrow,
  title,
  description,
  children,
}) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="page-header__description">
          {description}
        </p>
      </div>

      {children && (
        <div className="page-header__actions">
          {children}
        </div>
      )}
    </header>
  );
}
