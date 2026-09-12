"""Domain errors returned as typed MCP failures."""

from __future__ import annotations


class WorkshopError(RuntimeError):
    """Base error with a stable machine-readable code."""

    code = "WORKSHOP_ERROR"

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": str(self)}


class PlanValidationError(WorkshopError):
    code = "INVALID_PUBLICATION_PLAN"


class OperationNotFoundError(WorkshopError):
    code = "OPERATION_NOT_FOUND"


class StateConflictError(WorkshopError):
    code = "OPERATION_STATE_CONFLICT"


class GateError(WorkshopError):
    """A preflight gate failed; ``gate_code`` identifies the stop reason."""

    code = "PREFLIGHT_BLOCKED"

    def __init__(self, gate_code: str, message: str) -> None:
        super().__init__(message)
        self.gate_code = gate_code

    def as_dict(self) -> dict[str, str]:
        payload = super().as_dict()
        payload["gate_code"] = self.gate_code
        return payload


class ProviderUnavailableError(WorkshopError):
    code = "PROVIDER_MUTATION_UNAVAILABLE"


class ProviderResultUnknownError(WorkshopError):
    """The provider may have committed an irreversible call."""

    code = "PROVIDER_RESULT_UNKNOWN"


class UnsafeRetryError(WorkshopError):
    code = "UNSAFE_AUTOMATIC_RETRY_FORBIDDEN"


class AuthorizationError(WorkshopError):
    code = "SUBMIT_AUTHORIZATION_REJECTED"
