import pandas as pd
import numpy as np
import logging

from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import log_loss


class TabularDataService:
    def __init__(self, data: pd.DataFrame, config: dict):

        self.raw_df = data.copy()
        self.config = config

        self.ml_task = config["ml_task"]
        self.target_col = config["target_variable"]

        self.col_configs = {
            c["col_name"]: c
            for c in config.get("columns", [])
            if c.get("col_name") in data.columns
        }

        self.feature_cols = [
            c["col_name"]
            for c in config.get("columns", [])
            if c.get("is_feature") and c.get("col_name") in data.columns
        ]

        self.flagged_rows = {}

    def _flag_row(self, index, reason):

        idx = int(index) + 2

        if idx not in self.flagged_rows:
            self.flagged_rows[idx] = reason

    def run_pipeline(self):

        logging.info("Starting Tabular Data Pipeline")

        self._run_phase_1_gatekeeper()
        self._run_phase_2_the_detective()
        self._run_phase_3_the_interrogator()

        logging.info(f"Pipeline finished. Flagged rows: {len(self.flagged_rows)}")

        return self.flagged_rows

    # ------------------------------------------------
    # Phase 1
    # ------------------------------------------------

    def _run_phase_1_gatekeeper(self):

        start_count = len(self.flagged_rows)

        for index, row in self.raw_df.iterrows():
            if int(index) in self.flagged_rows:
                continue

            for col_name, cfg in self.col_configs.items():
                if col_name not in row:
                    continue

                value = row[col_name]

                if pd.isna(value):
                    continue

                dtype = cfg.get("data_type")

                if dtype == "Numerical":
                    try:
                        num = float(value)

                        min_val = cfg.get("min_val")
                        max_val = cfg.get("max_val")

                        if min_val is not None and num < min_val:
                            self._flag_row(index, f"Range violation {col_name}")
                            break

                        if max_val is not None and num > max_val:
                            self._flag_row(index, f"Range violation {col_name}")
                            break

                    except Exception:
                        self._flag_row(index, f"Type error {col_name}")
                        break

                elif dtype == "Categorical":
                    valid = cfg.get("valid_categories")

                    if valid and str(value) not in map(str, valid):
                        self._flag_row(index, f"Invalid category {col_name}")
                        break

        logging.info(f"Phase1 flagged {len(self.flagged_rows) - start_count}")

    # ------------------------------------------------
    # Phase 2
    # ------------------------------------------------

    def _run_phase_2_the_detective(self):

        start_count = len(self.flagged_rows)

        flagged = set(self.flagged_rows.keys())

        clean_idx = self.raw_df.index.difference(flagged)

        if len(clean_idx) < 10:
            return

        clean_df = self.raw_df.loc[clean_idx].copy()

        num_features = [
            c
            for c in self.feature_cols
            if self.col_configs[c]["data_type"] == "Numerical"
        ]

        if not num_features:
            return

        num_df = clean_df[num_features].apply(pd.to_numeric, errors="coerce")

        num_df = num_df.fillna(num_df.median()).fillna(0)

        scaler = StandardScaler()

        scaled = scaler.fit_transform(num_df)

        z = np.abs(scaled)

        rows, cols = np.where(z > 4)

        for r, c in zip(rows, cols):
            idx = clean_df.iloc[r].name
            col = num_features[c]

            self._flag_row(idx, f"Z-score outlier {col}")

        if len(num_df) > 10:
            iso = IsolationForest(
                n_estimators=200,
                contamination=min(0.05, max(0.01, 1 / len(num_df))),
                random_state=42,
            )

            preds = iso.fit_predict(num_df)

            outliers = clean_df.index[preds == -1]

            for idx in outliers:
                self._flag_row(idx, "IsolationForest outlier")

        logging.info(f"Phase2 flagged {len(self.flagged_rows) - start_count}")

    # ------------------------------------------------
    # Phase 3
    # ------------------------------------------------

    def _run_phase_3_the_interrogator(self):

        start_count = len(self.flagged_rows)

        flagged = set(self.flagged_rows.keys())

        clean_idx = self.raw_df.index.difference(flagged)

        if len(clean_idx) < 20:
            return

        clean_df = self.raw_df.loc[clean_idx]

        X, y = self._preprocess_for_model(clean_df)

        if X is None:
            return

        model = self._get_canary_model()

        if self.ml_task == "classification":
            min_class = y.value_counts().min()

            if min_class < 2:
                return

            folds = min(5, min_class)

            cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)

            probs = cross_val_predict(model, X, y, cv=cv, method="predict_proba")

            model.fit(X, y)

            probs = np.clip(probs, 1e-15, 1 - 1e-15)

            losses = [
                log_loss([t], [p], labels=model.classes_) for t, p in zip(y, probs)
            ]

            threshold = np.percentile(losses, 95)

            for idx, loss in zip(y.index, losses):
                if loss > threshold:
                    self._flag_row(idx, f"Suspicious label loss={loss:.2f}")

        logging.info(f"Phase3 flagged {len(self.flagged_rows) - start_count}")

    # ------------------------------------------------
    # Helpers
    # ------------------------------------------------

    def _get_canary_model(self):

        if self.ml_task == "regression":
            return LinearRegression()

        return LogisticRegression(
            max_iter=2000, solver="lbfgs", class_weight="balanced", random_state=42
        )

    def _preprocess_for_model(self, df):

        features = [c for c in self.feature_cols if c in df.columns]

        if not features:
            return None, None

        X = df[features].copy()
        y = df[self.target_col]

        X = pd.get_dummies(X, drop_first=False)

        X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

        scaler = StandardScaler()

        X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)

        return X, y
