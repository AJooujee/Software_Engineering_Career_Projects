/**
 * Accessible overlay used by Incident forms and confirmations.
 */

import {
  useEffect,
  useId,
  useRef,
} from "react";


export function Modal({
  eyebrow,
  title,
  isBusy = false,
  onClose,
  children,
}) {
  const titleId = useId();
  const closeButtonRef = useRef(null);

  useEffect(() => {
    closeButtonRef.current?.focus();

    function handleKeyDown(event) {
      if (event.key === "Escape" && !isBusy) {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isBusy, onClose]);

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget && !isBusy) {
      onClose();
    }
  }

  return (
    <div
      className="modal-backdrop"
      onMouseDown={handleBackdropClick}
    >
      <section
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <header className="modal-panel__header">
          <div>
            {eyebrow && (
              <p className="eyebrow">{eyebrow}</p>
            )}

            <h2 id={titleId}>{title}</h2>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            className="modal-panel__close"
            aria-label="Close"
            onClick={onClose}
            disabled={isBusy}
          >
            ×
          </button>
        </header>

        <div className="modal-panel__content">
          {children}
        </div>
      </section>
    </div>
  );
}
