"""Error types shared by the autonomous-player command line."""


class AgentError(RuntimeError):
    """A safety, environment, or runtime contract was not satisfied."""


class UnsafeCleanupError(AgentError):
    """A launched process may still be alive; protected postflight is forbidden."""
