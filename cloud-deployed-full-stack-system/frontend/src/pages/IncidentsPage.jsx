/**
 * Complete role-aware workflow for operational Incident management.
 */

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { ApiError } from "../api/client.js";
import {
  createIncident,
  deleteIncident,
  listIncidents,
  updateIncident,
} from "../api/incidents.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { IncidentDeleteDialog } from "../components/IncidentDeleteDialog.jsx";
import { IncidentDetails } from "../components/IncidentDetails.jsx";
import { IncidentFilters } from "../components/IncidentFilters.jsx";
import { IncidentForm } from "../components/IncidentForm.jsx";
import { IncidentList } from "../components/IncidentList.jsx";
import { Modal } from "../components/Modal.jsx";
import { PageHeader } from "../components/PageHeader.jsx";


const PAGE_SIZE = 10;

const EMPTY_FILTERS = {
  search: "",
  status: "",
  severity: "",
  serviceName: "",
};


/**
 * Trim free-text filters before sending them to the API.
 */
function normalizeFilters(filters) {
  return {
    search: filters.search.trim(),
    status: filters.status,
    severity: filters.severity,
    serviceName: filters.serviceName.trim(),
  };
}


export function IncidentsPage() {
  const {
    accessToken,
    user,
    logout,
  } = useAuth();

  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [offset, setOffset] = useState(0);
  const [reloadVersion, setReloadVersion] = useState(0);

  // Draft changes do not request data until the user applies them.
  const [draftFilters, setDraftFilters] = useState({
    ...EMPTY_FILTERS,
  });
  const [appliedFilters, setAppliedFilters] = useState({
    ...EMPTY_FILTERS,
  });

  const [loadStatus, setLoadStatus] = useState("loading");
  const [loadError, setLoadError] = useState(null);
  const [notice, setNotice] = useState(null);

  const [editorMode, setEditorMode] = useState(null);
  const [formError, setFormError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const [incidentToDelete, setIncidentToDelete] = useState(null);
  const [deleteError, setDeleteError] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const canModifyIncidents = ["operator", "admin"].includes(
    user?.role,
  );
  const canDeleteIncidents = user?.role === "admin";
  const hasActiveFilters = Object.values(
    appliedFilters,
  ).some(Boolean);

  const pageNumber = Math.floor(offset / PAGE_SIZE) + 1;
  const hasPreviousPage = offset > 0;
  const hasNextPage = incidents.length === PAGE_SIZE;

  const loadIncidentPage = useCallback(
    async ({ signal } = {}) => {
      setLoadStatus("loading");
      setLoadError(null);

      try {
        const loadedIncidents = await listIncidents(
          accessToken,
          {
            offset,
            limit: PAGE_SIZE,
            search: appliedFilters.search,
            status: appliedFilters.status,
            severity: appliedFilters.severity,
            serviceName: appliedFilters.serviceName,
            signal,
          },
        );

        // Return to the previous page if deletion emptied this page.
        if (loadedIncidents.length === 0 && offset > 0) {
          setOffset((currentOffset) => (
            Math.max(0, currentOffset - PAGE_SIZE)
          ));
          return;
        }

        setIncidents(loadedIncidents);
        setSelectedIncident((currentIncident) => {
          if (!loadedIncidents.length) {
            return null;
          }

          return (
            loadedIncidents.find(
              (incident) => incident.id === currentIncident?.id,
            )
            ?? loadedIncidents[0]
          );
        });
        setLoadStatus("ready");
      } catch (requestError) {
        if (requestError.name === "AbortError") {
          return;
        }

        if (
          requestError instanceof ApiError
          && (
            requestError.status === 401
            || requestError.status === 403
          )
        ) {
          logout();
          return;
        }

        setIncidents([]);
        setSelectedIncident(null);
        setLoadError(
          requestError.message
          ?? "Unable to load operational incidents.",
        );
        setLoadStatus("error");
      }
    },
    [
      accessToken,
      appliedFilters,
      logout,
      offset,
    ],
  );

  useEffect(() => {
    const controller = new AbortController();

    loadIncidentPage({
      signal: controller.signal,
    });

    return () => controller.abort();
  }, [loadIncidentPage, reloadVersion]);

  function applyIncidentFilters() {
    const normalizedFilters = normalizeFilters(
      draftFilters,
    );

    setNotice(null);
    setDraftFilters(normalizedFilters);
    setAppliedFilters(normalizedFilters);
    setOffset(0);
  }

  function clearIncidentFilters() {
    const clearedFilters = {
      ...EMPTY_FILTERS,
    };

    setNotice(null);
    setDraftFilters(clearedFilters);
    setAppliedFilters(clearedFilters);
    setOffset(0);
  }

  function refreshIncidentPage() {
    setNotice(null);
    setReloadVersion((currentVersion) => currentVersion + 1);
  }

  function openCreateForm() {
    setNotice(null);
    setFormError(null);
    setEditorMode("create");
  }

  function openEditForm() {
    if (!selectedIncident) {
      return;
    }

    setNotice(null);
    setFormError(null);
    setEditorMode("edit");
  }

  function closeEditor() {
    if (isSaving) {
      return;
    }

    setEditorMode(null);
    setFormError(null);
  }

  async function handleIncidentSubmit(incidentData) {
    setFormError(null);
    setIsSaving(true);

    try {
      if (editorMode === "edit" && selectedIncident) {
        const updatedIncident = await updateIncident(
          accessToken,
          selectedIncident.id,
          incidentData,
        );

        setIncidents((currentIncidents) => (
          currentIncidents.map((incident) => (
            incident.id === updatedIncident.id
              ? updatedIncident
              : incident
          ))
        ));
        setSelectedIncident(updatedIncident);
        setNotice(`Updated "${updatedIncident.title}".`);
      } else {
        const createdIncident = await createIncident(
          accessToken,
          incidentData,
        );

        setSelectedIncident(createdIncident);
        setNotice(`Created "${createdIncident.title}".`);

        if (offset === 0) {
          setReloadVersion(
            (currentVersion) => currentVersion + 1,
          );
        } else {
          setOffset(0);
        }
      }

      setEditorMode(null);
    } catch (requestError) {
      setFormError(
        requestError.message
        ?? "Unable to save the Incident.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  function openDeleteDialog() {
    if (!selectedIncident) {
      return;
    }

    setNotice(null);
    setDeleteError(null);
    setIncidentToDelete(selectedIncident);
  }

  function closeDeleteDialog() {
    if (isDeleting) {
      return;
    }

    setIncidentToDelete(null);
    setDeleteError(null);
  }

  async function handleDeleteIncident() {
    if (!incidentToDelete) {
      return;
    }

    setDeleteError(null);
    setIsDeleting(true);

    try {
      await deleteIncident(
        accessToken,
        incidentToDelete.id,
      );

      setNotice(`Deleted "${incidentToDelete.title}".`);
      setIncidentToDelete(null);
      setSelectedIncident(null);
      setReloadVersion(
        (currentVersion) => currentVersion + 1,
      );
    } catch (requestError) {
      setDeleteError(
        requestError.message
        ?? "Unable to delete the Incident.",
      );
    } finally {
      setIsDeleting(false);
    }
  }

  function goToPreviousPage() {
    setNotice(null);
    setOffset((currentOffset) => (
      Math.max(0, currentOffset - PAGE_SIZE)
    ));
  }

  function goToNextPage() {
    setNotice(null);
    setOffset((currentOffset) => (
      currentOffset + PAGE_SIZE
    ));
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Incident management"
        title="Operational incidents"
        description={
          "Review, create, update, and resolve service events "
          + "according to your assigned role."
        }
      >
        <button
          type="button"
          className="button-secondary"
          onClick={refreshIncidentPage}
          disabled={loadStatus === "loading"}
        >
          Refresh
        </button>

        {canModifyIncidents && (
          <button
            type="button"
            className="button-primary"
            onClick={openCreateForm}
          >
            Create incident
          </button>
        )}
      </PageHeader>

      <IncidentFilters
        value={draftFilters}
        hasActiveFilters={hasActiveFilters}
        isLoading={loadStatus === "loading"}
        onChange={setDraftFilters}
        onApply={applyIncidentFilters}
        onClear={clearIncidentFilters}
      />

      {notice && (
        <div
          className="form-alert form-alert--success"
          role="status"
        >
          {notice}
        </div>
      )}

      {loadStatus === "loading" && (
        <section
          className="content-panel incident-feedback"
          role="status"
          aria-live="polite"
        >
          <span
            className="route-status__spinner"
            aria-hidden="true"
          />
          <div>
            <h2>Loading incidents</h2>
            <p>Retrieving the latest operational records.</p>
          </div>
        </section>
      )}

      {loadStatus === "error" && (
        <section
          className="content-panel incident-feedback"
          role="alert"
        >
          <div>
            <p className="eyebrow">Connection problem</p>
            <h2>Unable to load incidents</h2>
            <p>{loadError}</p>
          </div>

          <button
            type="button"
            className="button-primary"
            onClick={refreshIncidentPage}
          >
            Try again
          </button>
        </section>
      )}

      {loadStatus === "ready"
        && incidents.length === 0
        && hasActiveFilters && (
        <section className="content-panel empty-state">
          <p className="eyebrow">Filtered results</p>
          <h2>No incidents match the current filters</h2>
          <p>
            Adjust or clear the filters to return to the complete
            operational Incident queue.
          </p>
        </section>
      )}

      {loadStatus === "ready"
        && incidents.length === 0
        && !hasActiveFilters && (
        <section className="content-panel empty-state">
          <p className="eyebrow">Incident workspace</p>
          <h2>No incidents have been reported</h2>
          <p>
            The workspace is clear. New operational events will
            appear here when they are created.
          </p>

          {canModifyIncidents && (
            <button
              type="button"
              className="button-primary"
              onClick={openCreateForm}
            >
              Create the first incident
            </button>
          )}
        </section>
      )}

      {loadStatus === "ready" && incidents.length > 0 && (
        <section className="incident-workspace">
          <div className="incident-browser">
            <header className="incident-browser__header">
              <div>
                <p className="eyebrow">Incident queue</p>
                <h2>Recent reports</h2>
              </div>

              <span className="status-pill">
                Page {pageNumber}
              </span>
            </header>

            <IncidentList
              incidents={incidents}
              selectedIncidentId={selectedIncident?.id}
              onSelect={setSelectedIncident}
            />

            <footer className="incident-pagination">
              <p>
                Showing {offset + 1}–
                {offset + incidents.length}
              </p>

              <div>
                <button
                  type="button"
                  className="button-secondary"
                  onClick={goToPreviousPage}
                  disabled={!hasPreviousPage}
                >
                  Previous
                </button>

                <button
                  type="button"
                  className="button-secondary"
                  onClick={goToNextPage}
                  disabled={!hasNextPage}
                >
                  Next
                </button>
              </div>
            </footer>
          </div>

          <div className="incident-detail-panel">
            {selectedIncident && (
              <IncidentDetails
                incident={selectedIncident}
                canEdit={canModifyIncidents}
                canDelete={canDeleteIncidents}
                onEdit={openEditForm}
                onDelete={openDeleteDialog}
              />
            )}
          </div>
        </section>
      )}

      {editorMode && (
        <Modal
          eyebrow={
            editorMode === "edit"
              ? "Update operational record"
              : "Report operational event"
          }
          title={
            editorMode === "edit"
              ? "Edit incident"
              : "Create incident"
          }
          isBusy={isSaving}
          onClose={closeEditor}
        >
          <IncidentForm
            incident={
              editorMode === "edit"
                ? selectedIncident
                : null
            }
            error={formError}
            isSubmitting={isSaving}
            onSubmit={handleIncidentSubmit}
            onCancel={closeEditor}
          />
        </Modal>
      )}

      {incidentToDelete && (
        <IncidentDeleteDialog
          incident={incidentToDelete}
          error={deleteError}
          isDeleting={isDeleting}
          onCancel={closeDeleteDialog}
          onConfirm={handleDeleteIncident}
        />
      )}
    </div>
  );
}
