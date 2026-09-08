"""Application-specific exceptions."""


class AdvisoryError(Exception):
    """Base exception for advisory failures."""


class CropNotFoundError(AdvisoryError):
    """Raised when the requested crop profile is unavailable."""


class KnowledgeValidationError(AdvisoryError):
    """Raised when knowledge files violate the shared contract."""


class ProviderUnavailableError(AdvisoryError):
    """Raised by external provider adapters when data cannot be obtained."""


class RecommendationNotFoundError(AdvisoryError):
    """Raised when a recommendation identifier cannot be resolved."""

