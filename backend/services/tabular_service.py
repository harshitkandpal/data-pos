import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import (
    cross_val_predict,
    StratifiedKFold,
)  # Import StratifiedKFold
from sklearn.metrics import log_loss, mean_squared_error
import numpy as np
import logging

# Setup basic logging if not already configured elsewhere
# logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')


class TabularDataService:
    """
    This service class holds the data and configuration,
    and runs the full sanitization pipeline for tabular data.
    """

    def __init__(self, data: pd.DataFrame, config: dict):
        self.raw_df = data.copy()
        self.config = config
        self.ml_task = config["ml_task"]
        self.target_col = config["target_variable"]
        # Ensure col_configs uses the actual column names from the data if they exist in config
        # Also handle potential missing keys like 'is_feature' gracefully
        self.col_configs = {
            c["col_name"]: c
            for c in config.get("columns", [])  # Use .get for safety
            if c.get("col_name") in data.columns  # Check existence
        }
        self.feature_cols = [
            c["col_name"]
            for c in config.get("columns", [])
            if c.get("is_feature")
            and c.get("col_name") in data.columns  # Check existence and feature flag
        ]
        self.flagged_rows = {}
        logging.info("TabularDataService initialized.")

    def _flag_row(self, index, reason):
        # Ensure index is standard Python int for JSON
        index_int = int(index)
        if index_int not in self.flagged_rows:
            self.flagged_rows[index_int] = reason

    def run_pipeline(self):
        logging.info("Starting tabular data pipeline...")
        self._run_phase_1_gatekeeper()
        self._run_phase_2_the_detective()
        self._run_phase_3_the_interrogator()
        logging.info(f"Pipeline finished. Total rows flagged: {len(self.flagged_rows)}")
        return self.flagged_rows

    def _run_phase_1_gatekeeper(self):
        print("Running Phase 1: Gatekeeper...")
        count = 0
        initial_flag_count = len(self.flagged_rows)  # Count before this phase
        for index, row in self.raw_df.iterrows():
            if int(index) in self.flagged_rows:
                continue  # Check using int

            # Iterate through columns defined in the config received from frontend
            for col_name, config in self.col_configs.items():
                # Check if the column actually exists in the DataFrame row
                if col_name not in row:
                    # This shouldn't happen if col_configs is built correctly, but good safety check
                    continue

                value = row[col_name]
                if pd.isna(value):
                    continue

                # Use data_type from the config for checks
                data_type = config.get("data_type")  # Use .get for safety

                if data_type == "Numerical":
                    try:
                        num_value = float(value)
                        min_val = config.get("min_val")
                        max_val = config.get("max_val")

                        if min_val is not None and num_value < min_val:
                            self._flag_row(
                                index,
                                f"Phase 1: Range Violation on '{col_name}'. Value {num_value:.2f} < {min_val}",
                            )
                            count += 1
                            break  # Move to next row once flagged
                        if max_val is not None and num_value > max_val:
                            self._flag_row(
                                index,
                                f"Phase 1: Range Violation on '{col_name}'. Value {num_value:.2f} > {max_val}",
                            )
                            count += 1
                            break  # Move to next row once flagged
                    except (ValueError, TypeError):
                        self._flag_row(
                            index,
                            f"Phase 1: Type Error on '{col_name}'. Value '{value}' is not numeric.",
                        )
                        count += 1
                        break  # Move to next row once flagged

                elif data_type == "Categorical":
                    valid_categories = config.get("valid_categories")
                    if valid_categories:
                        # Ensure comparison is done with strings
                        if str(value) not in map(str, valid_categories):
                            self._flag_row(
                                index,
                                f"Phase 1: Invalid Category on '{col_name}'. Value '{value}' not in valid list.",
                            )
                            count += 1
                            break  # Move to next row once flagged

        # Recalculate count based on flags added *in this phase*
        count = len(self.flagged_rows) - initial_flag_count
        logging.info(f"Phase 1 finished. Flagged {count} new rows.")

    def _run_phase_2_the_detective(self):
        print("Running Phase 2: The Detective...")
        start_flag_count = len(self.flagged_rows)
        # Convert flagged keys to int for consistent comparison
        flagged_keys_int = {int(k) for k in self.flagged_rows.keys()}
        clean_indices = self.raw_df.index.difference(flagged_keys_int)

        if len(clean_indices) < 10:
            logging.warning(
                "Skipping Phase 2: Fewer than 10 rows remaining after Phase 1."
            )
            return
        # Use .loc to avoid potential SettingWithCopyWarning
        clean_df = self.raw_df.loc[clean_indices].copy()

        # --- Filter features based *ONLY* on config type ---
        num_features = [
            col
            for col in self.feature_cols
            if col in self.col_configs
            and self.col_configs[col].get("data_type") == "Numerical"
        ]
        cat_features = [
            col
            for col in self.feature_cols
            if col in self.col_configs
            and self.col_configs[col].get("data_type") == "Categorical"
        ]
        # --- End Filter ---

        if num_features:
            logging.info(f"Phase 2: Analyzing numerical features: {num_features}")
            # Select only existing columns and handle types
            # Use .loc here as well
            num_df_raw = clean_df.loc[:, num_features].apply(
                pd.to_numeric, errors="coerce"
            )
            # Impute NaNs using the mean of each column *before* scaling
            means = num_df_raw.mean(numeric_only=True)
            # Fill NaNs using calculated means, fill remaining NaNs (if mean was NaN) with 0
            num_df = num_df_raw.fillna(means).fillna(0)

            # Z-Score
            if not num_df.empty:
                try:
                    scaler = StandardScaler()
                    scaled_data = scaler.fit_transform(num_df)
                    z_scores_abs = np.abs(scaled_data)
                    z_threshold = 4  # Keep stricter threshold
                    outlier_rows, outlier_cols = np.where(z_scores_abs > z_threshold)
                    logging.info(
                        f"Phase 2: Found {len(set(outlier_rows))} rows potentially exceeding Z-score > {z_threshold}."
                    )
                    unique_flagged_indices = (
                        set()
                    )  # Track indices flagged by Z-score in this run
                    for r_idx, c_idx in zip(outlier_rows, outlier_cols):
                        # Check index bounds carefully
                        if r_idx < len(clean_indices) and c_idx < len(num_features):
                            # Use iloc to get index based on integer position
                            original_index = clean_df.iloc[r_idx].name
                            if (
                                original_index not in unique_flagged_indices
                            ):  # Flag only once per row via Z-score
                                col_name = num_features[c_idx]
                                z_score_val = z_scores_abs[r_idx, c_idx]
                                self._flag_row(
                                    original_index,
                                    f"Phase 2: Z-Score Outlier on '{col_name}' (Z={z_score_val:.2f})",
                                )
                                unique_flagged_indices.add(original_index)
                except Exception as e:
                    logging.error(f"Phase 2 Z-Score failed: {e}", exc_info=True)

            # Isolation Forest
            if len(clean_indices) > 10 and not num_df.empty:
                try:
                    iso_contamination = 0.05  # Keep stricter contamination (e.g., 5%)
                    iso_forest = IsolationForest(
                        contamination=iso_contamination, random_state=42
                    )
                    preds = iso_forest.fit_predict(num_df)
                    # Get original indices corresponding to outlier predictions
                    # Ensure index alignment - get indices from clean_df where preds is -1
                    outlier_original_indices = clean_df.index[preds == -1]
                    logging.info(
                        f"Phase 2: Isolation Forest flagged {len(outlier_original_indices)} outliers (contamination={iso_contamination})."
                    )
                    for index in outlier_original_indices:
                        self._flag_row(
                            index, "Phase 2: Multivariate Outlier (Isolation Forest)"
                        )
                except Exception as e:
                    logging.error(
                        f"Phase 2 Isolation Forest failed: {e}", exc_info=True
                    )
        else:
            logging.info(
                "Phase 2: No numerical features configured for Z-Score/Isolation Forest."
            )

        # --- RARE CATEGORY LOGIC - STRICT CONFIG CHECK ---
        if cat_features:
            logging.info(
                f"Phase 2: Checking rare categories for configured features: {cat_features}"
            )
            # Iterate ONLY over features explicitly configured as Categorical
            for col in cat_features:  # This list *already* filters based on config['data_type'] == 'Categorical'
                if col in clean_df.columns:
                    # Convert to string *before* counting to handle mixed types safely
                    try:
                        counts = clean_df[col].astype(str).value_counts(normalize=True)
                        rare_threshold = 0.01  # Keep 1% threshold
                        rare_categories = counts[counts < rare_threshold].index
                        if len(rare_categories) > 0:
                            # Filter rows matching the rare categories (as strings)
                            rare_mask = clean_df[col].astype(str).isin(rare_categories)
                            # Ensure rare_indices uses the original DataFrame index
                            rare_indices = clean_df.index[
                                rare_mask
                            ]  # Use index attribute

                            logging.info(
                                f"Phase 2: Found {len(rare_indices)} rows with rare categories (<{rare_threshold * 100}%) in '{col}'."
                            )
                            for index in rare_indices:
                                value = clean_df.loc[index, col]
                                self._flag_row(
                                    index,
                                    f"Phase 2: Rare Category '{value}' in '{col}'",
                                )
                    except Exception as e:
                        logging.error(
                            f"Phase 2 Rare Category check failed for column '{col}': {e}",
                            exc_info=True,
                        )
                else:
                    logging.warning(
                        f"Phase 2 Rare Category: Column '{col}' not found in DataFrame."
                    )
        else:
            logging.info(
                "Phase 2: No categorical features configured for rare category check."
            )

        # --- END REFINED RARE CATEGORY LOGIC ---

        new_flags = len(self.flagged_rows) - start_flag_count
        logging.info(f"Phase 2 finished. Flagged {new_flags} new rows.")

    def _run_phase_3_the_interrogator(self):
        print("Running Phase 3: The Interrogator...")
        start_flag_count = len(self.flagged_rows)
        # Convert flagged keys to int for consistent comparison
        flagged_keys_int = {int(k) for k in self.flagged_rows.keys()}
        clean_indices = self.raw_df.index.difference(flagged_keys_int)

        if len(clean_indices) < 20:
            logging.warning("Skipping Phase 3: Fewer than 20 rows remaining.")
            return
        clean_df = self.raw_df.loc[clean_indices].copy()  # Use copy to avoid warnings

        canary_model = self._get_canary_model()
        X, y = self._preprocess_for_model(clean_df)
        if X is None or y is None or X.empty or y.empty:
            logging.warning(
                "Skipping phase 3: Not enough valid data after preprocessing."
            )
            return

        try:
            percentile_threshold = 98  # Keep stricter threshold (flag top 2%)

            # Determine CV folds based on task and class counts
            if self.ml_task == "classification":
                min_class_count = y.value_counts().min()
                # Use StratifiedKFold, ensure min 2 splits, max 5 or min_class_count
                cv_folds = min(5, max(2, min_class_count))
                if y.nunique() < 2 or cv_folds < 2:
                    logging.warning(
                        f"Skipping Phase 3 Classification CV: Need >= 2 classes with >= {cv_folds} samples each. Found {y.nunique()} classes, min count {min_class_count}."
                    )
                    return
                cv_strategy = StratifiedKFold(
                    n_splits=cv_folds, shuffle=True, random_state=42
                )
            else:  # Regression
                # Simple KFold is usually fine for regression unless data is ordered
                cv_folds = min(
                    5, max(2, len(y) // 5)
                )  # Ensure at least 5 samples per fold approx.
                if cv_folds < 2:
                    logging.warning(
                        f"Skipping Phase 3 Regression CV: Not enough samples ({len(y)}) for {cv_folds} folds."
                    )
                    return
                # KFold could be imported and used, or rely on cross_val_predict default
                cv_strategy = cv_folds  # cross_val_predict handles integer cv

            logging.info(
                f"Phase 3: Using {cv_folds}-fold CV {'(Stratified)' if self.ml_task == 'classification' else ''}."
            )

            if self.ml_task == "regression":
                preds = cross_val_predict(canary_model, X, y, cv=cv_strategy)
                # Align predictions with y's index for safe calculation
                preds_s = pd.Series(preds, index=y.index)
                valid_idx = y.index.intersection(
                    preds_s.dropna().index
                )  # Get indices where both are valid

                if len(valid_idx) < len(y):
                    logging.warning(
                        f"Phase 3 Regression: Mismatched indices/NaNs after predict. Using {len(valid_idx)} pairs."
                    )
                y_val, preds_val = y.loc[valid_idx], preds_s.loc[valid_idx]

                if len(y_val) > 0:
                    errors = (y_val - preds_val) ** 2
                    # Handle case where all errors might be the same
                    if len(errors) > 1 and errors.nunique() == 1:
                        threshold = errors.iloc[
                            0
                        ]  # Use the single error value if all are same
                        logging.warning("Phase 3 Regression: All errors are identical.")
                    elif len(errors) > 1:
                        threshold = np.percentile(errors, percentile_threshold)
                    elif len(errors) == 1:
                        threshold = errors.iloc[0]  # Single error value
                    else:
                        threshold = np.inf  # Avoid error if errors is empty

                    logging.info(
                        f"Phase 3 Regression: Error threshold ({percentile_threshold}th percentile) = {threshold:.2f}"
                    )
                    count = 0
                    for index, error in zip(y_val.index, errors):
                        # Ensure error is not NaN before comparison
                        if pd.notna(error) and error > threshold:
                            # Add a small tolerance for floating point comparison if needed
                            if not np.isclose(error, threshold):
                                self._flag_row(
                                    index,
                                    f"Phase 3: Suspicious Label (Error: {error:.2f})",
                                )
                                count += 1
                    logging.info(
                        f"Phase 3 Regression: Flagged {count} rows based on error."
                    )
                else:
                    logging.warning("Phase 3 Regression: No valid error values.")

            elif self.ml_task == "classification":
                probs = cross_val_predict(
                    canary_model, X, y, cv=cv_strategy, method="predict_proba"
                )
                canary_model.fit(X, y)  # Fit to get classes_
                trained_classes = canary_model.classes_

                # Align y with classes and calculate losses safely
                y_aligned_indices = y.isin(trained_classes)
                y_aligned = y[y_aligned_indices]

                # Ensure probabilities align if some y values were dropped
                # Use boolean indexing directly if lengths match
                probs_aligned = (
                    probs[y_aligned_indices.to_numpy(dtype=bool)]
                    if len(probs) == len(y)
                    else probs
                )

                if len(y_aligned) > 0 and len(y_aligned) == len(probs_aligned):
                    # Clip probabilities AFTER alignment
                    clipped_probs = [
                        np.clip(p, 1e-15, 1 - 1e-15) for p in probs_aligned
                    ]

                    losses = [
                        log_loss([t], [p_clipped], labels=trained_classes)
                        for t, p_clipped in zip(y_aligned, clipped_probs)
                    ]

                    # Handle case where all losses might be the same
                    if len(losses) > 1 and np.allclose(losses, losses[0]):
                        threshold = losses[0]
                        logging.warning(
                            "Phase 3 Classification: All losses are identical."
                        )
                    elif len(losses) > 1:
                        threshold = np.percentile(losses, percentile_threshold)
                    elif len(losses) == 1:
                        threshold = losses[0]
                    else:
                        threshold = np.inf

                    logging.info(
                        f"Phase 3 Classification: Loss threshold ({percentile_threshold}th percentile) = {threshold:.2f}"
                    )
                    count = 0
                    for index, loss in zip(y_aligned.index, losses):
                        # Ensure loss is not NaN
                        if pd.notna(loss) and loss > threshold:
                            # Add tolerance
                            if not np.isclose(loss, threshold):
                                self._flag_row(
                                    index,
                                    f"Phase 3: Suspicious Label (Loss: {loss:.2f})",
                                )
                                count += 1
                    logging.info(
                        f"Phase 3 Classification: Flagged {count} rows based on loss."
                    )
                else:
                    logging.warning(
                        f"Phase 3 Classification: Mismatch between valid y ({len(y_aligned)}) and probabilities ({len(probs_aligned)}) or no valid values."
                    )

        except ValueError as ve:
            # Catch specific ValueError often related to CV splits
            logging.error(
                f"ValueError in Phase 3 cross_val_predict, possibly due to class imbalance/few samples: {ve}. Skipping Phase 3.",
                exc_info=False,
            )  # Reduce noise
        except Exception as e:
            logging.error(
                f"Unexpected error in Phase 3 processing: {e}. Skipping.", exc_info=True
            )

        new_flags = len(self.flagged_rows) - start_flag_count
        logging.info(f"Phase 3 finished. Flagged {new_flags} new rows.")

    def _get_canary_model(self):
        if self.ml_task == "regression":
            return LinearRegression()
        if self.ml_task == "classification":
            # Add class_weight='balanced' for potentially imbalanced classes
            return LogisticRegression(
                max_iter=1000, random_state=42, class_weight="balanced"
            )
        raise ValueError(f"Unknown ML task: {self.ml_task}")

    def _preprocess_for_model(self, df: pd.DataFrame):
        current_feature_cols = [col for col in self.feature_cols if col in df.columns]
        if not current_feature_cols:
            logging.warning("No specified feature columns found for preprocessing.")
            return None, None

        X = df.loc[:, current_feature_cols].copy()  # Use .loc

        if self.target_col not in df.columns:
            logging.error(f"Target column '{self.target_col}' not found.")
            return None, None
        y = df.loc[:, self.target_col].copy()  # Use .loc

        valid_indices = y.notna()
        X, y = X.loc[valid_indices], y.loc[valid_indices]  # Use .loc for safety
        if len(y) < 20:
            logging.warning(
                f"Not enough valid target values ({len(y)}) for preprocessing."
            )
            return None, None

        # Preprocess features
        num_cols = X.select_dtypes(include=np.number).columns
        cat_cols = X.select_dtypes(exclude=np.number).columns

        # Fill numeric NaNs more robustly
        for col in num_cols:
            col_numeric = pd.to_numeric(X[col], errors="coerce")
            mean_val = col_numeric.mean()
            # If mean_val calculation resulted in NaN (e.g., all values were NaN), fill with 0
            X.loc[:, col] = col_numeric.fillna(mean_val if pd.notna(mean_val) else 0)

        # One-hot encode categorical features
        if not cat_cols.empty:
            for col in cat_cols:
                X.loc[:, col] = X[col].astype(str)  # Ensure string type
            # Convert columns to string type BEFORE get_dummies
            cat_cols_str = X.select_dtypes(exclude=np.number).columns
            X = pd.get_dummies(
                X, columns=cat_cols_str, dummy_na=False, drop_first=False
            )
            logging.info(f"One-hot encoded columns: {cat_cols_str.tolist()}")

        # Ensure target column is numeric for classification model
        if self.ml_task == "classification":
            # Check if target is already numeric-like (int/float) but might represent categories
            is_numeric_target = pd.api.types.is_numeric_dtype(y)

            # Factorize if not numeric OR if numeric but high cardinality suggests labels
            if not is_numeric_target or (is_numeric_target and y.nunique() > 20):
                logging.info("Factorizing target variable for classification.")
                y_factored, unique_classes = pd.factorize(y, sort=True)
                y = pd.Series(y_factored, index=y.index, name=y.name)  # Use y.index

                if -1 in y.values:  # Check if factorize introduced NaNs (-1)
                    logging.warning(
                        "NaNs (-1) detected in target after factorize. Dropping affected rows."
                    )
                    valid_target_indices = y[y != -1].index
                    X = X.loc[valid_target_indices]
                    y = y.loc[valid_target_indices]
                    if len(y) < 20:
                        logging.warning(
                            "Not enough rows left after dropping factorized NaNs."
                        )
                        return None, None  # Check size again

            elif y.isnull().any():  # Handle remaining NaNs if target was numeric
                logging.warning(
                    "NaNs detected in numeric target column. Dropping rows."
                )
                valid_indices = y.notna()
                X, y = X.loc[valid_indices], y.loc[valid_indices]
                if len(y) < 20:
                    logging.warning("Not enough rows left after dropping target NaNs.")
                    return None, None

        # Drop columns with zero variance after potential dummy encoding
        cols_before = X.shape[1]
        # Ensure X is numeric before checking nunique, handle potential strings if dummy encoding missed something
        # Convert only object columns, keep numbers as they are
        for col in X.select_dtypes(include=["object"]).columns:
            # Use .loc for assignment
            try:
                X.loc[:, col] = pd.to_numeric(X[col], errors="coerce")
            except Exception as e:
                logging.warning(
                    f"Could not convert column {col} to numeric after dummy: {e}"
                )
                # Decide whether to drop or fill based on your strategy
                # Option 1: Drop the column
                X = X.drop(columns=[col])
                logging.warning(
                    f"Dropped non-numeric column {col} after dummy encoding attempt."
                )
                # Option 2: Fill with 0 (or another value)
                # X.loc[:, col] = X.loc[:, col].fillna(0)

        # Recalculate cols_to_keep based on current columns in X
        numeric_cols_in_X = X.select_dtypes(include=np.number).columns
        cols_to_keep = [
            col
            for col in numeric_cols_in_X  # Use current numeric columns
            if X[col].nunique() > 1  # Check variance on numeric columns only
        ]
        # Only keep columns that are in X and meet the criteria
        X = X.loc[:, cols_to_keep]

        if X.shape[1] < cols_before:
            logging.warning(
                f"Dropped {cols_before - X.shape[1]} columns with low variance or non-numeric after dummy encoding."
            )

        if not X.empty:
            scaler = StandardScaler()
            try:
                X_scaled = scaler.fit_transform(X)
                # Ensure column names are strings for DataFrame creation
                X.columns = X.columns.astype(str)
                X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
                return X, y
            except ValueError as e:
                # Check explicitly for non-finite values BEFORE scaling
                if not np.all(np.isfinite(X.values)):
                    logging.warning(
                        f"Non-finite values (NaN/inf) detected before scaling. Attempting fillna(0)."
                    )
                    # Replace inf/-inf with NaN first, then fill NaNs
                    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
                    # Recheck finiteness
                    if not np.all(np.isfinite(X.values)):
                        logging.error(
                            "Non-finite values remain even after fillna(0). Cannot scale."
                        )
                        return None, None

                    # Retry scaling
                    try:
                        X_scaled = scaler.fit_transform(X)
                        X.columns = X.columns.astype(str)
                        X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
                        return X, y
                    except Exception as e2:
                        logging.error(
                            f"StandardScaler failed even after fillna: {e2}. Check data.",
                            exc_info=True,
                        )
                        return None, None
                else:
                    # If error is not due to non-finite, log the original error
                    logging.error(
                        f"StandardScaler failed: {e}. Check data.", exc_info=True
                    )
                    return None, None  # Return None if scaling fails definitively

        else:
            logging.warning("DataFrame X became empty after preprocessing.")
            return None, None
