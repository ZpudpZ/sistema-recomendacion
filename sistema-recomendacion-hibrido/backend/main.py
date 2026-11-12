from collections import Counter
from contextlib import asynccontextmanager
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from recommender import HybridRecommender
from recommender import cargar_o_descargar_movielens
from schemas import CatalogMetricsResponse
from schemas import EvaluateRequest
from schemas import EvaluateResponse
from schemas import GenreCount
from schemas import HealthResponse
from schemas import HistorialItem
from schemas import MetadataResponse
from schemas import RecommendationItem
from schemas import RecommendRequest
from schemas import RecommendResponse
from schemas import UserProfileResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    movies_df, ratings_df = cargar_o_descargar_movielens(data_dir="data")
    app.state.motor = HybridRecommender(movies_df, ratings_df, k=10)
    yield


app = FastAPI(
    title="API Sistema de Recomendación Híbrido - EPIS UNA Puno",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok")


@router.get("/metadata", response_model=MetadataResponse)
def get_metadata(request: Request):
    motor: HybridRecommender = request.app.state.motor
    user_ids = sorted([int(uid) for uid in motor.user2idx.keys()])
    metricas = motor.obtener_metricas_catalogo()
    return MetadataResponse(
        user_ids=user_ids,
        metricas_catalogo=CatalogMetricsResponse(**metricas),
    )


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(user_id: int, request: Request):
    motor: HybridRecommender = request.app.state.motor
    es_frio = bool(motor.es_usuario_frio(user_id))

    if es_frio:
        return UserProfileResponse(
            user_id=user_id,
            es_frio=True,
            total_valoraciones=0,
            promedio_rating=0.0,
            calificaciones_altas=0,
            porcentaje_altas=0.0,
            historial=[],
            generos_favoritos=[],
        )

    df_user = motor.ratings_df[motor.ratings_df["userId"] == user_id]
    total_val = int(len(df_user))
    promedio = round(float(df_user["rating"].mean()), 2) if total_val > 0 else 0.0
    altas = int((df_user["rating"] >= 3.0).sum())
    pct_altas = round((float(altas) / float(total_val)) * 100.0, 2) if total_val > 0 else 0.0

    df_hist = motor.obtener_historial_usuario(user_id=user_id, top_n=10)
    historial_items = [
        HistorialItem(
            movieId=int(row["movieId"]),
            title=str(row["title"]),
            genres=str(row["genres"]),
            rating=float(row["rating"]),
        )
        for _, row in df_hist.iterrows()
    ]

    df_merged = df_user.merge(
        motor.movies_df[["movieId", "genres"]],
        on="movieId",
        how="inner",
    )

    contador_generos: Counter = Counter()
    for genres_str in df_merged["genres"].dropna():
        for g in str(genres_str).split("|"):
            g_clean = g.strip()
            if g_clean and g_clean != "(no genres listed)":
                contador_generos[g_clean] += 1

    generos_fav = [
        GenreCount(genero=gen, cantidad=int(cant))
        for gen, cant in contador_generos.most_common(8)
    ]

    return UserProfileResponse(
        user_id=user_id,
        es_frio=False,
        total_valoraciones=total_val,
        promedio_rating=promedio,
        calificaciones_altas=altas,
        porcentaje_altas=pct_altas,
        historial=historial_items,
        generos_favoritos=generos_fav,
    )


@router.post("/recommend", response_model=RecommendResponse)
def post_recommend(req: RecommendRequest, request: Request):
    motor: HybridRecommender = request.app.state.motor
    es_frio = bool(motor.es_usuario_frio(req.user_id))
    alpha_efectivo = 0.0 if es_frio else round(float(req.alpha), 4)
    peso_contenido = round(1.0 - alpha_efectivo, 4)

    df_rec = motor.recomendar(
        user_id=req.user_id,
        top_n=req.top_n,
        alpha=req.alpha,
        k=req.k,
        excluir_vistos=True,
    )

    items = [
        RecommendationItem(
            movieId=int(row["movieId"]),
            title=str(row["title"]),
            genres=str(row["genres"]),
            score_hibrido=float(row["score_hibrido"]),
            score_colaborativo=float(row["score_colaborativo"]),
            score_contenido=float(row["score_contenido"]),
        )
        for _, row in df_rec.iterrows()
    ]

    return RecommendResponse(
        user_id=req.user_id,
        es_frio=es_frio,
        alpha_solicitado=round(float(req.alpha), 4),
        alpha_efectivo=alpha_efectivo,
        peso_contenido=peso_contenido,
        top_n=req.top_n,
        k=req.k,
        recomendaciones=items,
    )


@router.post("/evaluate", response_model=EvaluateResponse)
def post_evaluate(req: EvaluateRequest, request: Request):
    motor: HybridRecommender = request.app.state.motor
    metricas = motor.evaluar_predicciones(test_size=req.test_size)
    return EvaluateResponse(**metricas)


app.include_router(router)