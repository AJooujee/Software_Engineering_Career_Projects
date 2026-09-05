/**
 * Full-page feedback displayed while authentication is being resolved.
 */

export function AuthenticationLoading() {
  return (
    <main className="route-status">
      <div
        className="route-status__card"
        role="status"
        aria-live="polite"
      >
        <span className="route-status__spinner" aria-hidden="true" />
        <p className="eyebrow">Cloud Operations</p>
        <h1>Checking your session</h1>
        <p>Please wait while we verify your access.</p>
      </div>
    </main>
  );
}


/**
 * Allow recovery when a stored session cannot be verified.
 */
export function SessionError({
  message,
  onRetry,
  onLogout,
}) {
  return (
    <main className="route-status">
      <div className="route-status__card" role="alert">
        <p className="eyebrow">Connection problem</p>
        <h1>Unable to verify your session</h1>
        <p>{message}</p>

        <div className="route-status__actions">
          <button type="button" onClick={onRetry}>
            Try again
          </button>

          <button
            type="button"
            className="button-secondary"
            onClick={onLogout}
          >
            Sign out
          </button>
        </div>
      </div>
    </main>
  );
}
