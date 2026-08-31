"""Public, user-actionable toolchain failures."""


class PromoToolchainError(RuntimeError):
    """Base class for an actionable project or artifact error."""


class ManifestError(PromoToolchainError):
    """The manifest does not satisfy its declared contract."""


class ArtifactError(PromoToolchainError):
    """An artifact could not be preserved or verified."""


class SignoffError(PromoToolchainError):
    """A human sign-off could not be recorded."""
