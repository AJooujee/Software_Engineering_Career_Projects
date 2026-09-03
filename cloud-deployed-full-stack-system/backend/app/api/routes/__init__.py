"""API route modules exposed by the Cloud Operations application."""

from app.api.routes.incidents import router as incidents_router


__all__ = ["incidents_router"]
