# server/data_poisoning_service.py
import os
import pandas as pd
import numpy as np
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
import joblib


class TextBasedPoisonDetection:
    def __init__(self):
        self.embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        os.makedirs("model", exist_ok=True)

    def load_data(self, n_samples=5000, poison_fraction=0.05):
        from datasets import load_dataset

        ds = load_dataset("imdb")
        df = (
            pd.DataFrame(ds["train"])
            .sample(n_samples, random_state=42)
            .reset_index(drop=True)
        )
        n_poison = int(poison_fraction * n_samples)
        poison_idx = np.random.choice(df.index, n_poison, replace=False)
        df.loc[poison_idx, "text"] = df.loc[poison_idx, "text"].apply(
            lambda x: x + " spam inject poison fake review"
        )
        df["is_actual_poisoned"] = 0
        df.loc[poison_idx, "is_actual_poisoned"] = 1
        return df

    def process_data(self, df: pd.DataFrame):
        # Embedding
        embs = self.embedder.encode(df["text"].tolist(), show_progress_bar=True)
        scaler = StandardScaler()
        X = scaler.fit_transform(embs)

        # Ensemble models
        iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
        lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05)
        svm = OneClassSVM(kernel="rbf", nu=0.05)

        iso.fit(X)
        lof.fit_predict(X)
        svm.fit(X)

        # Scores and fusion
        scores = {
            "iso": -iso.decision_function(X),
            "lof": -lof.negative_outlier_factor_,
            "svm": -svm.decision_function(X),
        }
        df_scores = pd.DataFrame(scores)
        fused_score = (df_scores - df_scores.min()) / (
            df_scores.max() - df_scores.min()
        )
        df["poison_score"] = fused_score.mean(axis=1)

        threshold = np.percentile(df["poison_score"], 95)
        df["is_predicted_poisoned"] = (df["poison_score"] >= threshold).astype(int)

        # Metrics
        y_true = df["is_actual_poisoned"]
        y_pred = df["is_predicted_poisoned"]
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        # Save models
        joblib.dump(iso, "model/isolation_forest.pkl")
        joblib.dump(lof, "model/local_outlier_factor.pkl")
        joblib.dump(svm, "model/one_class_svm.pkl")
        joblib.dump(scaler, "model/scaler.pkl")

        # Return results
        return {
            "data": df[
                ["text", "is_actual_poisoned", "poison_score", "is_predicted_poisoned"]
            ].to_dict(orient="records"),
            "metrics": {
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
            },
            "actual_poisoned": df[df["is_actual_poisoned"] == 1][
                ["text", "poison_score"]
            ]
            .head(50)
            .to_dict(orient="records"),
            "predicted_poisoned": df[df["is_predicted_poisoned"] == 1][
                ["text", "poison_score"]
            ]
            .head(50)
            .to_dict(orient="records"),
            "true_positives": df[
                (df["is_actual_poisoned"] == 1) & (df["is_predicted_poisoned"] == 1)
            ][["text", "poison_score"]]
            .head(50)
            .to_dict(orient="records"),
        }


class TableBasedPoisonDetection:
    def __init__(self):
        os.makedirs("model", exist_ok=True)

    def load_data(self, n_samples=5000, poison_fraction=0.05):
        # Example: generate synthetic tabular data
        df = pd.DataFrame(
            {
                "feature1": np.random.randn(n_samples),
                "feature2": np.random.randn(n_samples),
                "feature3": np.random.randn(n_samples),
            }
        )
        n_poison = int(poison_fraction * n_samples)
        poison_idx = np.random.choice(df.index, n_poison, replace=False)
        df.loc[poison_idx, "feature1"] += 10  # inject anomaly
        df["is_actual_poisoned"] = 0
        df.loc[poison_idx, "is_actual_poisoned"] = 1
        return df

    def process_data(self, df: pd.DataFrame):
        X = df[["feature1", "feature2", "feature3"]].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        iso = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
        lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05)
        svm = OneClassSVM(kernel="rbf", nu=0.05)

        iso.fit(X_scaled)
        lof.fit_predict(X_scaled)
        svm.fit(X_scaled)

        scores = {
            "iso": -iso.decision_function(X_scaled),
            "lof": -lof.negative_outlier_factor_,
            "svm": -svm.decision_function(X_scaled),
        }
        df_scores = pd.DataFrame(scores)
        fused_score = (df_scores - df_scores.min()) / (
            df_scores.max() - df_scores.min()
        )
        df["poison_score"] = fused_score.mean(axis=1)
        threshold = np.percentile(df["poison_score"], 95)
        df["is_predicted_poisoned"] = (df["poison_score"] >= threshold).astype(int)

        y_true = df["is_actual_poisoned"]
        y_pred = df["is_predicted_poisoned"]
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        return {
            "data": df.to_dict(orient="records"),
            "metrics": {
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
            },
            "actual_poisoned": df[df["is_actual_poisoned"] == 1]
            .head(50)
            .to_dict(orient="records"),
            "predicted_poisoned": df[df["is_predicted_poisoned"] == 1]
            .head(50)
            .to_dict(orient="records"),
            "true_positives": df[
                (df["is_actual_poisoned"] == 1) & (df["is_predicted_poisoned"] == 1)
            ]
            .head(50)
            .to_dict(orient="records"),
        }
