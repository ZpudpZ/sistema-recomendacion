import io
import os
import time
import zipfile
import numpy as np
import pandas as pd
import requests
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split


def cargar_o_descargar_movielens(data_dir="data"):
    os.makedirs(data_dir, exist_ok=True)
    movies_path = os.path.join(data_dir, "movies.csv")
    ratings_path = os.path.join(data_dir, "ratings.csv")

    if not (os.path.exists(movies_path) and os.path.exists(ratings_path)):
        url = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                with z.open("ml-latest-small/movies.csv") as source, open(movies_path, "wb") as target:
                    target.write(source.read())
                with z.open("ml-latest-small/ratings.csv") as source, open(ratings_path, "wb") as target:
                    target.write(source.read())
        except Exception as e:
            raise RuntimeError(f"Error al descargar el dataset MovieLens: {e}")

    movies_df = pd.read_csv(movies_path)
    ratings_df = pd.read_csv(ratings_path)

    movies_df["title"] = movies_df["title"].fillna("")
    movies_df["genres_clean"] = (
        movies_df["genres"]
        .fillna("")
        .str.replace("|", " ", regex=False)
        .str.replace("(no genres listed)", "", regex=False)
    )

    return movies_df, ratings_df


def crear_mapeos_ids(movies_df, ratings_df):
    user_ids = np.sort(ratings_df["userId"].unique())
    movie_ids = movies_df["movieId"].unique()

    user2idx = {int(u_id): idx for idx, u_id in enumerate(user_ids)}
    idx2user = {idx: int(u_id) for idx, u_id in enumerate(user_ids)}

    movie2idx = {int(m_id): idx for idx, m_id in enumerate(movie_ids)}
    idx2movie = {idx: int(m_id) for idx, m_id in enumerate(movie_ids)}

    return user2idx, idx2user, movie2idx, idx2movie


def normalizar_min_max(scores, epsilon=1e-8):
    if scores.size == 0:
        return scores

    s_min = float(np.min(scores))
    s_max = float(np.max(scores))

    if np.isclose(s_max, s_min):
        return np.zeros_like(scores, dtype=np.float64)

    numerador = np.subtract(scores, s_min)
    denominador = np.subtract(s_max, s_min) + epsilon
    return np.divide(numerador, denominador)


class ContentRecommender:
    def __init__(self, movies_df, ratings_df, movie2idx=None, idx2movie=None):
        self.movies_df = movies_df.reset_index(drop=True)
        self.ratings_df = ratings_df

        if movie2idx is None or idx2movie is None:
            _, _, self.movie2idx, self.idx2movie = crear_mapeos_ids(self.movies_df, self.ratings_df)
        else:
            self.movie2idx = movie2idx
            self.idx2movie = idx2movie

        corpus = (self.movies_df["title"] + " " + self.movies_df["genres_clean"]).values

        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.n_movies = self.tfidf_matrix.shape[0]

        self.cold_start_scores = self._construir_scores_cold_start()

    def _construir_scores_cold_start(self):
        stats = (
            self.ratings_df.groupby("movieId")["rating"]
            .agg(["count", "mean"])
            .reset_index()
        )
        stats = stats[stats["movieId"].isin(self.movie2idx)]
        if stats.empty:
            return np.zeros(self.n_movies, dtype=np.float64)

        c = float(stats["mean"].mean())
        m = float(stats["count"].quantile(0.80))
        v = stats["count"].values.astype(np.float64)
        r = stats["mean"].values.astype(np.float64)

        term1 = np.multiply(np.divide(v, v + m), r)
        term2 = np.multiply(np.divide(m, v + m), c)
        stats["weighted_rating"] = term1 + term2

        top_acclaimed = stats.nlargest(100, "weighted_rating")
        indices = [self.movie2idx[int(m_id)] for m_id in top_acclaimed["movieId"]]
        weights = top_acclaimed["weighted_rating"].values.astype(np.float64)

        seed_vec = self.tfidf_matrix[indices].T.dot(weights)
        seed_profile = np.asarray(seed_vec).reshape(1, -1) / np.sum(weights)
        content_sim = cosine_similarity(seed_profile, self.tfidf_matrix).flatten()

        pop_vector = np.zeros(self.n_movies, dtype=np.float64)
        for m_id, w_rating in zip(stats["movieId"], stats["weighted_rating"]):
            pop_vector[self.movie2idx[int(m_id)]] = w_rating

        pop_norm = normalizar_min_max(pop_vector)
        sim_norm = normalizar_min_max(content_sim)

        return np.multiply(0.5, sim_norm) + np.multiply(0.5, pop_norm)

    def construir_perfil_usuario(self, user_id, min_rating=3.0):
        user_ratings = self.ratings_df[self.ratings_df["userId"] == user_id]
        if user_ratings.empty:
            return None

        positivas = user_ratings[user_ratings["rating"] >= min_rating]
        if positivas.empty:
            positivas = user_ratings

        valid_mask = positivas["movieId"].isin(self.movie2idx)
        positivas = positivas[valid_mask]
        if positivas.empty:
            return None

        movie_indices = [self.movie2idx[int(m_id)] for m_id in positivas["movieId"]]
        weights = positivas["rating"].values.astype(np.float64)

        user_tfidf = self.tfidf_matrix[movie_indices]
        weighted_sum = user_tfidf.T.dot(weights)
        user_profile = np.asarray(weighted_sum).reshape(1, -1) / np.sum(weights)

        return user_profile

    def predecir_scores(self, user_id, min_rating=3.0):
        user_profile = self.construir_perfil_usuario(user_id, min_rating=min_rating)
        if user_profile is None:
            return self.cold_start_scores.copy()

        sim_scores = cosine_similarity(user_profile, self.tfidf_matrix).flatten()
        return sim_scores

    def recomendar(self, user_id, top_n=10, excluir_vistos=True):
        scores = self.predecir_scores(user_id).copy()

        if excluir_vistos:
            vistos_ids = self.ratings_df.loc[
                self.ratings_df["userId"] == user_id, "movieId"
            ].values
            vistos_idx = [
                self.movie2idx[int(m_id)]
                for m_id in vistos_ids
                if int(m_id) in self.movie2idx
            ]
            scores[vistos_idx] = -1.0

        top_indices = np.argsort(scores)[::-1][:top_n]

        resultados = self.movies_df.iloc[top_indices][["movieId", "title", "genres"]].copy()
        resultados["score_contenido"] = scores[top_indices]
        return resultados.reset_index(drop=True)


class CollaborativeRecommender:
    def __init__(
        self,
        movies_df,
        ratings_df,
        k=10,
        user2idx=None,
        idx2user=None,
        movie2idx=None,
        idx2movie=None,
    ):
        self.movies_df = movies_df.reset_index(drop=True)
        self.ratings_df = ratings_df
        self.k = k

        if any(m is None for m in (user2idx, idx2user, movie2idx, idx2movie)):
            self.user2idx, self.idx2user, self.movie2idx, self.idx2movie = crear_mapeos_ids(
                self.movies_df, self.ratings_df
            )
        else:
            self.user2idx = user2idx
            self.idx2user = idx2user
            self.movie2idx = movie2idx
            self.idx2movie = idx2movie

        self.n_users = len(self.user2idx)
        self.n_movies = len(self.movie2idx)

        valid_ratings = self.ratings_df[
            self.ratings_df["movieId"].isin(self.movie2idx)
            & self.ratings_df["userId"].isin(self.user2idx)
        ]

        row_indices = [self.user2idx[int(u_id)] for u_id in valid_ratings["userId"]]
        col_indices = [self.movie2idx[int(m_id)] for m_id in valid_ratings["movieId"]]
        rating_values = valid_ratings["rating"].values.astype(np.float64)

        self.user_item_matrix = csr_matrix(
            (rating_values, (row_indices, col_indices)),
            shape=(self.n_users, self.n_movies),
            dtype=np.float64,
        )

        self.user_sim_matrix = cosine_similarity(self.user_item_matrix, dense_output=True)
        np.fill_diagonal(self.user_sim_matrix, 0.0)

    def predecir_scores(self, user_id, k=None):
        if user_id not in self.user2idx:
            return np.zeros(self.n_movies, dtype=np.float64)

        k_vecinos = k if k is not None else self.k
        u_idx = self.user2idx[user_id]
        sim_vector = self.user_sim_matrix[u_idx]

        top_k_indices = np.argsort(sim_vector)[::-1][:k_vecinos]
        top_k_indices = [idx for idx in top_k_indices if sim_vector[idx] > 0.0]

        if not top_k_indices:
            return np.zeros(self.n_movies, dtype=np.float64)

        sim_k = sim_vector[top_k_indices]
        ratings_k = self.user_item_matrix[top_k_indices]

        numerador = np.asarray(sim_k @ ratings_k).flatten()
        denominador = np.sum(np.abs(sim_k)) + 1e-8

        predicted_scores = np.divide(numerador, denominador)
        return predicted_scores

    def recomendar(self, user_id, top_n=10, k=None, excluir_vistos=True):
        scores = self.predecir_scores(user_id, k=k).copy()

        if excluir_vistos and user_id in self.user2idx:
            u_idx = self.user2idx[user_id]
            vistos_idx = self.user_item_matrix[u_idx].indices
            scores[vistos_idx] = -1.0

        top_indices = np.argsort(scores)[::-1][:top_n]

        resultados = self.movies_df.iloc[top_indices][["movieId", "title", "genres"]].copy()
        resultados["score_colaborativo"] = scores[top_indices]
        return resultados.reset_index(drop=True)


class HybridRecommender:
    def __init__(
        self,
        movies_df,
        ratings_df,
        k=10,
        content_recommender=None,
        collab_recommender=None,
    ):
        self.movies_df = movies_df.reset_index(drop=True)
        self.ratings_df = ratings_df
        self.user2idx, self.idx2user, self.movie2idx, self.idx2movie = crear_mapeos_ids(
            self.movies_df, self.ratings_df
        )

        if content_recommender is not None:
            self.content_rec = content_recommender
        else:
            self.content_rec = ContentRecommender(
                self.movies_df, self.ratings_df, self.movie2idx, self.idx2movie
            )

        if collab_recommender is not None:
            self.collab_rec = collab_recommender
        else:
            self.collab_rec = CollaborativeRecommender(
                self.movies_df,
                self.ratings_df,
                k=k,
                user2idx=self.user2idx,
                idx2user=self.idx2user,
                movie2idx=self.movie2idx,
                idx2movie=self.idx2movie,
            )

    def es_usuario_frio(self, user_id):
        return user_id not in self.user2idx

    def predecir_scores(self, user_id, alpha=0.5, k=None):
        alpha_clamped = float(np.clip(alpha, 0.0, 1.0))

        if self.es_usuario_frio(user_id):
            alpha_efectivo = 0.0
        else:
            alpha_efectivo = alpha_clamped

        raw_cont = self.content_rec.predecir_scores(user_id)
        raw_colab = self.collab_rec.predecir_scores(user_id, k=k)

        cont_norm = normalizar_min_max(raw_cont)
        colab_norm = normalizar_min_max(raw_colab)

        peso_contenido = np.subtract(1.0, alpha_efectivo)
        comp_colab = np.multiply(alpha_efectivo, colab_norm)
        comp_cont = np.multiply(peso_contenido, cont_norm)
        hybrid_scores = comp_colab + comp_cont

        return hybrid_scores, colab_norm, cont_norm, alpha_efectivo

    def recomendar(self, user_id, top_n=10, alpha=0.5, k=None, excluir_vistos=True):
        hybrid_scores, colab_norm, cont_norm, _ = self.predecir_scores(
            user_id=user_id, alpha=alpha, k=k
        )

        scores_ranking = hybrid_scores.copy()

        if excluir_vistos and not self.es_usuario_frio(user_id):
            u_idx = self.user2idx[user_id]
            vistos_idx = self.collab_rec.user_item_matrix[u_idx].indices
            scores_ranking[vistos_idx] = -1.0

        top_indices = np.argsort(scores_ranking)[::-1][:top_n]

        resultados = self.movies_df.iloc[top_indices][["movieId", "title", "genres"]].copy()
        resultados["score_hibrido"] = np.round(hybrid_scores[top_indices], 4)
        resultados["score_colaborativo"] = np.round(colab_norm[top_indices], 4)
        resultados["score_contenido"] = np.round(cont_norm[top_indices], 4)

        return resultados.reset_index(drop=True)

    def obtener_historial_usuario(self, user_id, top_n=10):
        if self.es_usuario_frio(user_id):
            return pd.DataFrame(columns=["movieId", "title", "genres", "rating"])

        historial = self.ratings_df[self.ratings_df["userId"] == user_id].merge(
            self.movies_df[["movieId", "title", "genres"]], on="movieId", how="inner"
        )
        historial = historial.sort_values(by=["rating", "movieId"], ascending=[False, True])
        return historial[["movieId", "title", "genres", "rating"]].head(top_n).reset_index(drop=True)

    def obtener_metricas_catalogo(self):
        n_users = len(self.user2idx)
        n_movies = len(self.movie2idx)
        n_ratings = self.collab_rec.user_item_matrix.nnz
        total_celdas = np.multiply(float(n_users), float(n_movies))
        densidad = np.divide(float(n_ratings), total_celdas)
        dispersion = np.subtract(1.0, densidad)

        return {
            "total_usuarios": int(n_users),
            "total_peliculas": int(n_movies),
            "total_valoraciones": int(n_ratings),
            "densidad_pct": round(float(np.multiply(densidad, 100.0)), 4),
            "dispersion_pct": round(float(np.multiply(dispersion, 100.0)), 4),
        }

    def evaluar_predicciones(self, test_size=0.2, random_state=42):
        inicio = time.time()

        valid_df = self.ratings_df[
            self.ratings_df["userId"].isin(self.user2idx)
            & self.ratings_df["movieId"].isin(self.movie2idx)
        ].copy()

        train_df, test_df = train_test_split(
            valid_df, test_size=test_size, random_state=random_state
        )

        n_users = len(self.user2idx)
        n_movies = len(self.movie2idx)

        u_train = [self.user2idx[int(u)] for u in train_df["userId"]]
        m_train = [self.movie2idx[int(m)] for m in train_df["movieId"]]
        r_train = train_df["rating"].values.astype(np.float64)

        train_matrix = csr_matrix(
            (r_train, (u_train, m_train)),
            shape=(n_users, n_movies),
            dtype=np.float64,
        )
        bin_matrix = csr_matrix(
            (np.ones_like(r_train), (u_train, m_train)),
            shape=(n_users, n_movies),
            dtype=np.float64,
        )

        global_mean = float(np.mean(r_train))

        user_counts = np.asarray(bin_matrix.sum(axis=1)).flatten()
        user_sums = np.asarray(train_matrix.sum(axis=1)).flatten()
        user_means = np.full(n_users, global_mean, dtype=np.float64)
        mask_u = user_counts > 0
        user_means[mask_u] = np.divide(user_sums[mask_u], user_counts[mask_u])

        item_counts = np.asarray(bin_matrix.sum(axis=0)).flatten()
        item_sums = np.asarray(train_matrix.sum(axis=0)).flatten()
        item_means = np.full(n_movies, global_mean, dtype=np.float64)
        mask_m = item_counts > 0
        item_means[mask_m] = np.divide(item_sums[mask_m], item_counts[mask_m])
        item_bias = np.subtract(item_means, global_mean)

        r_dev = np.subtract(r_train, user_means[u_train])
        dev_matrix = csr_matrix(
            (r_dev, (u_train, m_train)),
            shape=(n_users, n_movies),
            dtype=np.float64,
        )

        sim_matrix = cosine_similarity(train_matrix, dense_output=True)
        np.fill_diagonal(sim_matrix, 0.0)
        sim_pos = np.maximum(sim_matrix, 0.0)

        numerador_mat = sim_pos @ dev_matrix
        denominador_mat = sim_pos @ bin_matrix

        u_test = np.array([self.user2idx[int(u)] for u in test_df["userId"]], dtype=np.int64)
        m_test = np.array([self.movie2idx[int(m)] for m in test_df["movieId"]], dtype=np.int64)
        y_true = test_df["rating"].values.astype(np.float64)

        num_vals = np.asarray(numerador_mat[u_test, m_test]).flatten()
        den_vals = np.asarray(denominador_mat[u_test, m_test]).flatten()

        y_pred = user_means[u_test].copy()
        has_neighbors = den_vals > 1e-8
        y_pred[has_neighbors] = y_pred[has_neighbors] + np.divide(
            num_vals[has_neighbors], den_vals[has_neighbors]
        )

        no_neighbors = ~has_neighbors
        y_pred[no_neighbors] = y_pred[no_neighbors] + item_bias[m_test[no_neighbors]]

        y_pred = np.clip(y_pred, 0.5, 5.0)

        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mae = float(mean_absolute_error(y_true, y_pred))
        tiempo_seg = round(time.time() - inicio, 3)

        metricas_cat = self.obtener_metricas_catalogo()

        return {
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "train_samples": int(len(train_df)),
            "test_samples": int(len(test_df)),
            "test_size_ratio": float(test_size),
            "tiempo_segundos": tiempo_seg,
            "total_usuarios": metricas_cat["total_usuarios"],
            "total_peliculas": metricas_cat["total_peliculas"],
            "total_valoraciones": metricas_cat["total_valoraciones"],
            "densidad_pct": metricas_cat["densidad_pct"],
            "dispersion_pct": metricas_cat["dispersion_pct"],
        }