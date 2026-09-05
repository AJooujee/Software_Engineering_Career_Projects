/**
 * Confirmation dialog for destructive Incident actions.
 */

import { Modal } from "./Modal.jsx";


export function IncidentDeleteDialog({
  incident,
  error = null,
  isDeleting = false,
  onCancel,
  onConfirm,
}) {
  return (
    <Modal
      eyebrow="Administrator action"
      title="Delete incident?"
      isBusy={isDeleting}
      onClose={onCancel}
    >
      <div className="confirmation-dialog">
        <p>
          This will permanently delete{" "}
          <strong>{incident.title}</strong>.
          This action cannot be undone.
        </p>

        {error && (
          <div
            className="form-alert form-alert--error"
            role="alert"
          >
            {error}
          </div>
        )}

        <div className="confirmation-dialog__actions">
          <button
            type="button"
            className="button-secondary"
            onClick={onCancel}
            disabled={isDeleting}
          >
            Cancel
          </button>

          <button
            type="button"
            className="button-danger"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? "Deleting..." : "Delete incident"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
