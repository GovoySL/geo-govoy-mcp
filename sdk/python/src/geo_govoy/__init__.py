"""Geo Govoy: cliente Python de la API de datos de calle y carretera para rutas en España.

Docs: https://geo.govoy.es/docs
"""
__version__ = "0.1.0"

from .client import DEFAULT_BASE_URL, ENV_KEY, GeoGovoy  # noqa: E402
from .errors import (  # noqa: E402
    APIError,
    AuthenticationError,
    ConnectionError,
    GeoGovoyError,
    PayloadTooLargeError,
    PermissionDeniedError,
    QuotaExceededError,
    RateLimitError,
    ValidationError,
)

__all__ = [
    "GeoGovoy",
    "DEFAULT_BASE_URL",
    "ENV_KEY",
    "GeoGovoyError",
    "AuthenticationError",
    "PermissionDeniedError",
    "QuotaExceededError",
    "PayloadTooLargeError",
    "ValidationError",
    "RateLimitError",
    "APIError",
    "ConnectionError",
    "__version__",
]
