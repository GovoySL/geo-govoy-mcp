"""Tipos de las peticiones y respuestas (subconjunto de https://geo.govoy.es/openapi.json).

Son ``TypedDict``: en tiempo de ejecución, diccionarios normales.
"""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Union

if sys.version_info >= (3, 11):
    from typing import NotRequired, TypedDict
else:  # pragma: no cover
    from typing_extensions import NotRequired, TypedDict


# ---------- Entrada ----------

class AddressInput(TypedDict, total=False):
    external_id: str
    raw_address: str
    street: str
    house_number: str
    unit: str
    postcode: str
    municipality: str
    province: str
    country: str
    query_type: str
    types: List[str]


Address = Union[str, AddressInput]


class Point(TypedDict):
    lat: float
    lon: float
    external_id: NotRequired[str]


class Stop(TypedDict):
    lat: float
    lon: float
    id: NotRequired[str]
    time: NotRequired[str]  # "HH:MM", hora local


class Route(TypedDict):
    stops: List[Stop]
    id: NotRequired[str]
    date: NotRequired[str]  # AAAA-MM-DD


# ---------- Geocodificación ----------

class Candidate(TypedDict, total=False):
    rank: int
    entity_id: str
    feature_type: str
    formatted_address: str
    street: Optional[str]
    house_number: Optional[str]
    postcode: Optional[str]
    municipality: Optional[str]
    lat: float
    lon: float
    source: str
    coordinate_accuracy: str
    confidence_score: float
    score: float
    match_scope: str
    components: Dict[str, Any]
    warnings: List[str]


class GeocodeResult(TypedDict, total=False):
    input: Dict[str, Any]
    external_id: Optional[str]
    query_type: str
    input_granularity: str
    input_quality_class: str
    status: str
    next_action: str  # accept | confirm | fix
    warnings: List[str]
    candidates: List[Candidate]


class GeocodeResponse(TypedDict):
    request_ids: List[str]
    total: int
    results: List[GeocodeResult]


class ReverseCandidate(TypedDict, total=False):
    lat: float
    lon: float
    distance_m: float
    confidence: float
    precision: str
    address_quality: str
    formatted_address: Optional[str]
    street: Optional[str]
    house_number: Optional[str]
    postcode: Optional[str]
    municipality: Optional[str]
    province_code: Optional[str]
    source: str
    warnings: List[str]


class ReverseResult(TypedDict, total=False):
    input: Point
    external_id: Optional[str]
    status: str
    candidates: List[ReverseCandidate]


class ReverseResponse(TypedDict):
    request_ids: List[str]
    total: int
    results: List[ReverseResult]


# ---------- Matriz ----------

class MatrixResponse(TypedDict, total=False):
    durations: List[List[Optional[float]]]  # segundos
    distances: List[List[Optional[float]]]  # metros
    sources: List[int]
    destinations: List[int]
    model: Dict[str, Any]
    departure_time_used: Optional[str]
    elements: int
    unreachable: int
    elapsed_ms: int


# ---------- Cuenta ----------

class Quota(TypedDict, total=False):
    """Cabeceras ``X-Govoy-Quota-*`` de la última respuesta."""

    limit: int
    remaining: int
    unit: str


Account = Dict[str, Any]
Usage = Dict[str, Any]
JSON = Dict[str, Any]
