import pandas as pd
import numpy as np
import re
from textblob import TextBlob

# Corrected import
from sentence_transformers import SentenceTransformer
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import log_loss
from sklearn.model_selection import cross_val_predict
import logging  # Import logging


# Renamed class to match import
class TextDataService:
    CANARY_MODEL = Pipeline(
        [
            ("tfidf", TfidfVectorizer(stop_words="english", max_features=5000)),
            ("clf", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )

    def __init__(self, data: pd.DataFrame, config: dict):
        self.raw_df = data.copy()
        self.config = config
        self.text_col = config["text_column"]
        self.target_col = config["target_column"]
        self.p1_settings = config.get("phase_1_settings", {})
        self.flagged_rows = {}
        logging.info("Loading Sentence-BERT model...")
        # A fast and effective model
        self.sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
        logging.info("Sentence-BERT model loaded.")

    def run_pipeline(self):
        logging.info("Starting text data pipeline...")
        self.raw_df[self.text_col] = self.raw_df[self.text_col].astype(str).fillna("")
        self._run_phase_1_gatekeeper()
        self._run_phase_2_the_detective()
        self._run_phase_3_the_interrogator()
        logging.info(
            f"Text pipeline finished. Total rows flagged: {len(self.flagged_rows)}"
        )
        return self.flagged_rows

    def _flag_row(self, index, reason):
        if index not in self.flagged_rows:
            # Ensure index is a standard Python int for JSON later
            self.flagged_rows[int(index)] = reason

    def _run_phase_1_gatekeeper(self):
        logging.info("Running Phase 1: Gatekeeper...")
        start_flag_count = len(self.flagged_rows)
        min_len = self.p1_settings.get("min_length", 10)
        max_len = self.p1_settings.get("max_length", 5000)
        url_pattern = re.compile(r"https|http?://\S+")
        html_pattern = re.compile(r"<.*?>")

        for index, row in self.raw_df.iterrows():
            if int(index) in self.flagged_rows:  # Check int
                continue

            text = row[self.text_col]
            if not (min_len <= len(text) <= max_len):
                self._flag_row(index, f"Phase 1: Length Violation ({len(text)} chars)")
                continue
            if self.p1_settings.get("flag_urls", True) and url_pattern.search(text):
                self._flag_row(index, "Phase 1: Contains URL")
                continue
            if self.p1_settings.get("flag_html", True) and html_pattern.search(text):
                self._flag_row(index, "Phase 1: Contains HTML Tags")
                continue

            # Simplified gibberish check: very low subjectivity
            try:
                if (
                    len(text.split()) > 3
                    and TextBlob(text).sentiment.subjectivity < 0.01
                ):
                    self._flag_row(
                        index, "Phase 1: Gibberish Detected (low subjectivity)"
                    )
            except Exception as e:
                logging.warning(f"TextBlob analysis failed for row {index}: {e}")

        new_flags = len(self.flagged_rows) - start_flag_count
        logging.info(f"Phase 1 finished. Flagged {new_flags} new rows.")

    def _run_phase_2_the_detective(self):
        logging.info("Running Phase 2: The Detective...")
        start_flag_count = len(self.flagged_rows)
        # Convert flagged keys to int for consistent comparison
        flagged_keys_int = {int(k) for k in self.flagged_rows.keys()}
        clean_indices = self.raw_df.index.difference(flagged_keys_int)

        if len(clean_indices) < 10:
            logging.warning("Skipping Phase 2: Fewer than 10 rows remaining.")
            return

        clean_df = self.raw_df.loc[clean_indices]

        try:
            embeddings = self.sbert_model.encode(
                clean_df[self.text_col].tolist(), show_progress_bar=True
            )
            embeddings_scaled = StandardScaler().fit_transform(embeddings)

            for label in clean_df[self.target_col].unique():
                class_indices = clean_df[clean_df[self.target_col] == label].index
                # Corrected indexing
                class_embedding_indices = clean_df.index.get_indexer(class_indices)

                if len(class_embedding_indices) < 10:
                    logging.warning(
                        f"Skipping Phase 2 for class '{label}': < 10 samples."
                    )
                    continue

                class_embeddings = embeddings_scaled[class_embedding_indices]
                # Explicitly set contamination lower for embeddings
                iso_forest = IsolationForest(
                    contamination=0.03, random_state=42
                )  # Try 3%
                preds = iso_forest.fit_predict(class_embeddings)

                # Map predictions back to original indices
                outlier_mask = preds == -1
                outlier_indices = class_indices[
                    outlier_mask
                ]  # Use boolean mask on original class_indices

                for index in outlier_indices:
                    self._flag_row(
                        index, f"Phase 2: Semantic Outlier (vs. class '{label}')"
                    )
        except Exception as e:
            logging.error(
                f"Error in Phase 2 (embeddings or IsoForest): {e}", exc_info=True
            )

        new_flags = len(self.flagged_rows) - start_flag_count
        logging.info(f"Phase 2 finished. Flagged {new_flags} new rows.")

    def _run_phase_3_the_interrogator(self):
        logging.info("Running Phase 3: The Interrogator...")
        start_flag_count = len(self.flagged_rows)
        # Convert flagged keys to int for consistent comparison
        flagged_keys_int = {int(k) for k in self.flagged_rows.keys()}
        clean_indices = self.raw_df.index.difference(flagged_keys_int)

        if len(clean_indices) < 20:
            logging.warning("Skipping Phase 3: Fewer than 20 rows remaining.")
            return

        clean_df = self.raw_df.loc[clean_indices]
        X, y = clean_df[self.text_col], clean_df[self.target_col]

        # Check for sufficient class diversity for cross-validation
        min_class_count = y.value_counts().min()
        cv_folds = min(5, max(2, min_class_count if min_class_count >= 2 else 0))

        if cv_folds < 2:
            logging.warning(
                f"Skipping Phase 3 CV: Not enough class diversity ({min_class_count} min count)."
            )
            return

        try:
            logging.info(f"Phase 3: Using {cv_folds}-fold CV.")
            probs = cross_val_predict(
                self.CANARY_MODEL, X, y, cv=cv_folds, method="predict_proba"
            )
            self.CANARY_MODEL.fit(X, y)  # Fit to get .classes_

            # --- NEW FIX: Clip probabilities to avoid log(0) ---
            clipped_probs = [np.clip(p, 1e-15, 1 - 1e-15) for p in probs]

            losses = [
                log_loss([t], [p_clipped], labels=self.CANARY_MODEL.classes_)
                for t, p_clipped in zip(y, clipped_probs)
            ]
            # --- END FIX ---

            percentile_threshold = 97
            # Handle case where all losses might be the same
            if len(losses) > 0 and np.allclose(losses, losses[0]):
                threshold = losses[0]
            elif len(losses) > 1:
                threshold = np.percentile(losses, percentile_threshold)
            else:
                threshold = np.inf  # No losses to compare

            logging.info(
                f"Phase 3 Classification: Loss threshold ({percentile_threshold}th percentile) = {threshold:.2f}"
            )

            count = 0
            for index, loss in zip(y.index, losses):
                if pd.notna(loss) and loss > threshold:
                    self._flag_row(
                        index, f"Phase 3: Suspicious Label (Loss: {loss:.2f})"
                    )
                    count += 1
            logging.info(f"Phase 3 finished. Flagged {count} new rows.")

        except Exception as e:
            logging.error(f"Error in Phase 3 processing: {e}. Skipping.", exc_info=True)

        new_flags = len(self.flagged_rows) - start_flag_count
        logging.info(f"Phase 3 (Text) finished. Flagged {new_flags} new rows.")
