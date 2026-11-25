"""Errores de la API de Geo Govoy."""
from __future__ import annotations

from typing import Any, Optional


class GeoGovoyError(Exception):
    """Error base. Lleva el estado HTTP, el código de error de la API y el cuerpo."""

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        retry_after: Optional[float] = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.request_id = request_id
        self.retry_after = retry_after
        self.body = body

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}(status={self.status!r}, code={self.code!r}, message={self.message!r})"


class AuthenticationError(GeoGovoyError):
    """401: clave ausente o no válida (`invalid_api_key`)."""


class PermissionDeniedError(GeoGovoyError):
    """403: cuenta bloqueada (`account_blocked`) u operación no permitida."""


class QuotaExceededError(GeoGovoyError):
    """402: cuota del mes o saldo agotados (`quota_exceeded`). No se reintenta."""


class PayloadTooLargeError(GeoGovoyError):
    """413: la petición es demasiado grande. Usa lotes más pequeños."""


class ValidationError(GeoGovoyError):
    """422: el cuerpo no cumple el esquema (p. ej. más de 1.000 direcciones)."""


class RateLimitError(GeoGovoyError):
    """429: límite por minuto o de concurrencia. `retry_after` indica los segundos de espera."""


class APIError(GeoGovoyError):
    """5xx u otra respuesta inesperada del servidor."""


class ConnectionError(GeoGovoyError):  # noqa: A001 - nombre público intencionado
    """No se pudo conectar con geo.govoy.es (red, DNS, TLS o timeout)."""


_BY_STATUS = {
    401: AuthenticationError,
    402: QuotaExceededError,
    403: PermissionDeniedError,
    413: PayloadTooLargeError,
    422: ValidationError,
    429: RateLimitError,
}


def error_for(status: int) -> type:
    if status in _BY_STATUS:
        return _BY_STATUS[status]
    return APIError
