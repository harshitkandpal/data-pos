# server/data_poisoning_service.py

import os
import numpy as np
import pandas as pd
import joblib

from datasets import load_dataset
from sentence_transformers import SentenceTransformer

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


MODEL_DIR = "model"
os.makedirs(MODEL_DIR, exist_ok=True)


# =====================================================
# TEXT BASED DETECTION
# =====================================================

class TextBasedPoisonDetection:

    def __init__(self):

        self.embedder = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.scaler = StandardScaler()

        self.iso = IsolationForest(
            n_estimators=200,
            contamination=0.05,
            random_state=42
        )

        self.lof = LocalOutlierFactor(
            n_neighbors=20,
            contamination=0.05,
            novelty=True
        )

        self.svm = OneClassSVM(
            kernel="rbf",
            nu=0.05
        )

    # --------------------------------------------------

    def load_data(self, n_samples=3000, poison_fraction=0.05):

        ds = load_dataset("imdb", split="train")

        df = pd.DataFrame(ds)

        df = df.sample(n_samples, random_state=42).reset_index(drop=True)

        n_poison = int(poison_fraction * n_samples)

        rng = np.random.default_rng(42)

        poison_idx = rng.choice(df.index, n_poison, replace=False)

        df.loc[poison_idx, "text"] = df.loc[poison_idx, "text"].apply(
            lambda x: x + " spam inject poison fake review"
        )

        df["is_actual_poisoned"] = 0
        df.loc[poison_idx, "is_actual_poisoned"] = 1

        return df

    # --------------------------------------------------

    def process_data(self, df: pd.DataFrame):

        texts = df["text"].astype(str).tolist()

        embeddings = self.embedder.encode(
            texts,
            batch_size=64,
            show_progress_bar=True
        )

        X = self.scaler.fit_transform(embeddings)

        # Train models
        self.iso.fit(X)
        self.lof.fit(X)
        self.svm.fit(X)

        # Scores
        iso_score = -self.iso.decision_function(X)
        lof_score = -self.lof.decision_function(X)
        svm_score = -self.svm.decision_function(X)

        df_scores = pd.DataFrame({
            "iso": iso_score,
            "lof": lof_score,
            "svm": svm_score
        })

        # Safe normalization
        df_scores = (df_scores - df_scores.min()) / (
            df_scores.max() - df_scores.min() + 1e-8
        )

        df["poison_score"] = df_scores.mean(axis=1)

        threshold = np.percentile(df["poison_score"], 95)

        df["is_predicted_poisoned"] = (
            df["poison_score"] >= threshold
        ).astype(int)

        metrics = self._calculate_metrics(df)

        # Save models
        joblib.dump(self.iso, f"{MODEL_DIR}/isolation_forest.pkl")
        joblib.dump(self.lof, f"{MODEL_DIR}/local_outlier_factor.pkl")
        joblib.dump(self.svm, f"{MODEL_DIR}/one_class_svm.pkl")
        joblib.dump(self.scaler, f"{MODEL_DIR}/scaler.pkl")

        return {
            "data": df[
                ["text", "is_actual_poisoned",
                 "poison_score", "is_predicted_poisoned"]
            ].to_dict(orient="records"),

            "metrics": metrics,

            "actual_poisoned": df[df["is_actual_poisoned"] == 1][
                ["text", "poison_score"]
            ].head(50).to_dict(orient="records"),

            "predicted_poisoned": df[df["is_predicted_poisoned"] == 1][
                ["text", "poison_score"]
            ].head(50).to_dict(orient="records"),

            "true_positives": df[
                (df["is_actual_poisoned"] == 1) &
                (df["is_predicted_poisoned"] == 1)
            ][["text", "poison_score"]].head(50).to_dict(orient="records")
        }

    # --------------------------------------------------

    def _calculate_metrics(self, df):

        y_true = df["is_actual_poisoned"]
        y_pred = df["is_predicted_poisoned"]

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        cm = confusion_matrix(y_true, y_pred)

        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
        else:
            tn = fp = fn = tp = 0

        return {
            "total": len(df),
            "poisoned_true": int(y_true.sum()),
            "poisoned_pred": int(y_pred.sum()),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "tp": int(tp),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
        }


# =====================================================
# TABULAR DETECTION
# =====================================================

class TableBasedPoisonDetection:

    def __init__(self):

        self.scaler = StandardScaler()

        self.iso = IsolationForest(
            n_estimators=200,
            contamination=0.05,
            random_state=42
        )

        self.lof = LocalOutlierFactor(
            n_neighbors=20,
            contamination=0.05,
            novelty=True
        )

        self.svm = OneClassSVM(
            kernel="rbf",
            nu=0.05
        )

    # --------------------------------------------------

    def load_data(self, n_samples=3000, poison_fraction=0.05):

        rng = np.random.default_rng(42)

        df = pd.DataFrame({

            "feature1": rng.normal(size=n_samples),
            "feature2": rng.normal(size=n_samples),
            "feature3": rng.normal(size=n_samples),

        })

        n_poison = int(poison_fraction * n_samples)

        poison_idx = rng.choice(df.index, n_poison, replace=False)

        df.loc[poison_idx, "feature1"] += 10

        df["is_actual_poisoned"] = 0
        df.loc[poison_idx, "is_actual_poisoned"] = 1

        return df

    # --------------------------------------------------

    def process_data(self, df: pd.DataFrame):

        X = df[["feature1", "feature2", "feature3"]].values

        X_scaled = self.scaler.fit_transform(X)

        self.iso.fit(X_scaled)
        self.lof.fit(X_scaled)
        self.svm.fit(X_scaled)

        iso_score = -self.iso.decision_function(X_scaled)
        lof_score = -self.lof.decision_function(X_scaled)
        svm_score = -self.svm.decision_function(X_scaled)

        df_scores = pd.DataFrame({
            "iso": iso_score,
            "lof": lof_score,
            "svm": svm_score
        })

        df_scores = (df_scores - df_scores.min()) / (
            df_scores.max() - df_scores.min() + 1e-8
        )

        df["poison_score"] = df_scores.mean(axis=1)

        threshold = np.percentile(df["poison_score"], 95)

        df["is_predicted_poisoned"] = (
            df["poison_score"] >= threshold
        ).astype(int)

        metrics = self._calculate_metrics(df)

        return {
            "data": df.to_dict(orient="records"),
            "metrics": metrics,
            "actual_poisoned": df[df["is_actual_poisoned"] == 1]
            .head(50).to_dict(orient="records"),
            "predicted_poisoned": df[df["is_predicted_poisoned"] == 1]
            .head(50).to_dict(orient="records"),
            "true_positives": df[
                (df["is_actual_poisoned"] == 1) &
                (df["is_predicted_poisoned"] == 1)
            ].head(50).to_dict(orient="records"),
        }

    # --------------------------------------------------

    def _calculate_metrics(self, df):

        y_true = df["is_actual_poisoned"]
        y_pred = df["is_predicted_poisoned"]

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        cm = confusion_matrix(y_true, y_pred)

        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
        else:
            tn = fp = fn = tp = 0

        return {
            "total": len(df),
            "poisoned_true": int(y_true.sum()),
            "poisoned_pred": int(y_pred.sum()),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "tp": int(tp),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
        }