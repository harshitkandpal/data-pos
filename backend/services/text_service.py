import pandas as pd
import numpy as np
import re
import logging

from textblob import TextBlob
from sentence_transformers import SentenceTransformer

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import log_loss
from sklearn.model_selection import cross_val_predict


class TextDataService:

    CANARY_MODEL = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", max_features=5000)),
        ("clf", LogisticRegression(max_iter=1000, random_state=42))
    ])

    def __init__(self, data: pd.DataFrame, config: dict):

        self.raw_df = data.copy()

        self.config = config

        self.text_col = config["text_column"]
        self.target_col = config["target_column"]

        self.p1_settings = config.get("phase_1_settings", {})

        self.flagged_rows = {}

        logging.info("Loading SentenceTransformer model")

        self.sbert = SentenceTransformer("all-MiniLM-L6-v2")

    def _flag_row(self, index, reason):

        idx = int(index)

        if idx not in self.flagged_rows:
            self.flagged_rows[idx] = reason

    def run_pipeline(self):

        self.raw_df[self.text_col] = self.raw_df[self.text_col].astype(str)

        self._run_phase_1_gatekeeper()
        self._run_phase_2_the_detective()
        self._run_phase_3_the_interrogator()

        return self.flagged_rows

    # -----------------------------------------------
    # Phase 1
    # -----------------------------------------------

    def _run_phase_1_gatekeeper(self):

        min_len = self.p1_settings.get("min_length", 10)
        max_len = self.p1_settings.get("max_length", 5000)

        url_pattern = re.compile(r"https?://")

        for idx, row in self.raw_df.iterrows():

            if idx in self.flagged_rows:
                continue

            text = row[self.text_col]

            if not(min_len <= len(text) <= max_len):

                self._flag_row(idx, "Length violation")
                continue

            if url_pattern.search(text):

                self._flag_row(idx, "Contains URL")
                continue

            try:

                if len(text.split()) > 3 and TextBlob(text).sentiment.subjectivity < 0.01:

                    self._flag_row(idx, "Possible gibberish")

            except Exception:
                pass

    # -----------------------------------------------
    # Phase 2
    # -----------------------------------------------

    def _run_phase_2_the_detective(self):

        clean_idx = self.raw_df.index.difference(self.flagged_rows.keys())

        if len(clean_idx) < 10:
            return

        clean_df = self.raw_df.loc[clean_idx]

        texts = clean_df[self.text_col].tolist()

        embeddings = self.sbert.encode(
            texts,
            batch_size=64,
            show_progress_bar=True
        )

        embeddings = StandardScaler().fit_transform(embeddings)

        iso = IsolationForest(
            n_estimators=200,
            contamination=0.03,
            random_state=42
        )

        preds = iso.fit_predict(embeddings)

        outliers = clean_df.index[preds == -1]

        for idx in outliers:
            self._flag_row(idx, "Semantic outlier")

    # -----------------------------------------------
    # Phase 3
    # -----------------------------------------------

    def _run_phase_3_the_interrogator(self):

        clean_idx = self.raw_df.index.difference(self.flagged_rows.keys())

        if len(clean_idx) < 20:
            return

        clean_df = self.raw_df.loc[clean_idx]

        X = clean_df[self.text_col]
        y = clean_df[self.target_col]

        min_class = y.value_counts().min()

        if min_class < 2:
            return

        folds = min(5, min_class)

        probs = cross_val_predict(
            self.CANARY_MODEL,
            X,
            y,
            cv=folds,
            method="predict_proba"
        )

        self.CANARY_MODEL.fit(X, y)

        probs = np.clip(probs, 1e-15, 1-1e-15)

        losses = [
            log_loss([t], [p], labels=self.CANARY_MODEL.classes_)
            for t, p in zip(y, probs)
        ]

        threshold = np.percentile(losses, 95)

        for idx, loss in zip(y.index, losses):

            if loss > threshold:
                self._flag_row(idx, f"Suspicious label loss={loss:.2f}")