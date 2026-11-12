from pydantic import BaseModel
from pydantic import Field


class RecommendRequest(BaseModel):
    user_id: int
    alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    top_n: int = Field(default=10, ge=1, le=50)
    k: int = Field(default=10, ge=1, le=100)


class EvaluateRequest(BaseModel):
    test_size: float = Field(default=0.20, ge=0.05, le=0.50)


class HealthResponse(BaseModel):
    status: str


class CatalogMetricsResponse(BaseModel):
    total_usuarios: int
    total_peliculas: int
    total_valoraciones: int
    densidad_pct: float
    dispersion_pct: float


class MetadataResponse(BaseModel):
    user_ids: list[int]
    metricas_catalogo: CatalogMetricsResponse


class HistorialItem(BaseModel):
    movieId: int
    title: str
    genres: str
    rating: float


class GenreCount(BaseModel):
    genero: str
    cantidad: int


class UserProfileResponse(BaseModel):
    user_id: int
    es_frio: bool
    total_valoraciones: int
    promedio_rating: float
    calificaciones_altas: int
    porcentaje_altas: float
    historial: list[HistorialItem]
    generos_favoritos: list[GenreCount]


class RecommendationItem(BaseModel):
    movieId: int
    title: str
    genres: str
    score_hibrido: float
    score_colaborativo: float
    score_contenido: float


class RecommendResponse(BaseModel):
    user_id: int
    es_frio: bool
    alpha_solicitado: float
    alpha_efectivo: float
    peso_contenido: float
    top_n: int
    k: int
    recomendaciones: list[RecommendationItem]


class EvaluateResponse(BaseModel):
    rmse: float
    mae: float
    train_samples: int
    test_samples: int
    test_size_ratio: float
    tiempo_segundos: float
    total_usuarios: int
    total_peliculas: int
    total_valoraciones: int
    densidad_pct: float
    dispersion_pct: float