import pandas as pd
import numpy as np
from sklearn.datasets import (
    fetch_california_housing,
    fetch_20newsgroups,
    load_iris,
    make_regression,
    fetch_openml,  # Keep for tabular if needed
)

# --- NEW: Import Hugging Face datasets library ---
from datasets import load_dataset

# --- END NEW ---
import logging

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s:%(message)s"
)  # Basic logging


class PoisonInjector:
    """
    Creates poisoned datasets for demonstration and evaluation.
    Returns (poisoned_df, true_poison_indices)
    """

    def __init__(self, df: pd.DataFrame, seed=42):
        self.df = df.copy().reset_index(drop=True)
        self.poison_indices = set()
        self.rng = np.random.default_rng(seed)
        logging.info(
            f"PoisonInjector initialized with DataFrame shape: {self.df.shape}"
        )

    def _get_random_indices(self, n, existing_indices):
        all_indices = set(self.df.index)
        available_indices = list(all_indices - existing_indices)
        # Ensure n is not larger than available indices *before* checking safe indices
        if n > len(available_indices):
            logging.warning(
                f"Requested {n} indices, but only {len(available_indices)} available."
            )
            n = len(available_indices)

        if n == 0:
            return np.array([], dtype=int)

        # Ensure indices are within bounds of the current DataFrame length
        safe_indices = [idx for idx in available_indices if idx < len(self.df)]

        # Ensure n is not larger than the *safe* available indices
        if n > len(safe_indices):
            logging.warning(
                f"Adjusted sample size {n} to available safe indices {len(safe_indices)}."
            )
            n = len(safe_indices)

        if n <= 0:
            logging.warning("No safe indices available for sampling.")
            return np.array([], dtype=int)

        try:
            return self.rng.choice(safe_indices, size=n, replace=False)
        except ValueError as e:
            # Catch potential errors if safe_indices became empty unexpectedly
            logging.error(
                f"Error during rng.choice: {e}. n={n}, len(safe_indices)={len(safe_indices)}",
                exc_info=True,
            )
            return np.array([], dtype=int)

    def inject_tabular_regression_poison(self, target_col, feature_cols, p=0.05):
        n_poison = int(len(self.df) * p)
        if n_poison == 0:
            return self.df, []
        # Distribute poison somewhat evenly, ensuring at least 1 per phase if possible
        n_phases = 3
        n_per_phase = max(1, n_poison // n_phases)
        n_remainder = n_poison % n_phases
        n_phase1 = n_per_phase + (1 if n_remainder > 0 else 0)
        n_phase2 = n_per_phase + (1 if n_remainder > 1 else 0)
        n_phase3 = n_per_phase

        logging.info(
            f"Injecting approx {n_poison} total poison samples (Regression: P1={n_phase1}, P2={n_phase2}, P3={n_phase3})."
        )

        # Prioritize specified numeric features, fallback if none work
        num_features = [
            f
            for f in feature_cols
            if f in self.df.columns and pd.api.types.is_numeric_dtype(self.df[f])
        ]
        if not num_features:
            num_features = self.df.select_dtypes(include=np.number).columns.tolist()
            if target_col in num_features:
                num_features.remove(target_col)  # Don't use target as feature here
            if not num_features:
                raise ValueError("No numeric features found to poison.")
            logging.warning(f"Using fallback numeric features: {num_features}")

        # Calculate min *before* adding string poison
        try:
            # Convert to numeric first to handle potential strings already present
            numeric_col = pd.to_numeric(self.df[num_features[0]], errors="coerce")
            numeric_min_val = numeric_col.min()
            if pd.isna(numeric_min_val):
                numeric_min_val = (
                    0  # Fallback if min calculation fails (e.g., all NaNs)
                )
        except IndexError:
            raise ValueError("Not enough numeric features to perform poisoning.")
        except KeyError:
            raise ValueError(
                f"Feature '{num_features[0]}' not found in DataFrame columns."
            )

        # Phase 1: Constraint/Type Violation
        p1_indices = self._get_random_indices(n_phase1, self.poison_indices)
        if len(p1_indices) > 0:
            logging.info(f"Injecting {len(p1_indices)} Phase 1 poison (Regression).")
            for idx in p1_indices:
                if idx < len(self.df):  # Boundary check
                    # Ensure num_features is not empty
                    if num_features:
                        # Ensure the column exists before trying to modify it
                        if num_features[0] in self.df.columns:
                            self.df.loc[idx, num_features[0]] = (
                                "TYPE_ERROR"  # Use distinct string
                            )
                            # Ensure target column exists
                            if target_col in self.df.columns:
                                self.df.loc[idx, target_col] = -99999
                            else:
                                logging.warning(
                                    f"Target column '{target_col}' not found for Phase 1."
                                )

                        else:
                            logging.warning(
                                f"Feature column '{num_features[0]}' not found for Phase 1."
                            )
                    else:
                        logging.warning(
                            "No numeric features available for Phase 1 poisoning."
                        )
            self.poison_indices.update(p1_indices)

        # Phase 2: Statistical Outlier
        p2_indices = self._get_random_indices(n_phase2, self.poison_indices)
        if len(p2_indices) > 0:
            logging.info(f"Injecting {len(p2_indices)} Phase 2 poison (Regression).")
            # Ensure num_features is not empty
            if num_features:
                feature_to_outlie = (
                    num_features[1] if len(num_features) > 1 else num_features[0]
                )
                # Ensure the selected feature exists
                if feature_to_outlie in self.df.columns:
                    for idx in p2_indices:
                        if idx < len(self.df):  # Boundary check
                            current_val = pd.to_numeric(
                                self.df.loc[idx, feature_to_outlie], errors="coerce"
                            )
                            # Make outlier significant relative to column's scale
                            multiplier = 20
                            scale = pd.to_numeric(
                                self.df[feature_to_outlie], errors="coerce"
                            ).std()  # Ensure numeric before std
                            if (
                                not pd.isna(current_val)
                                and not pd.isna(scale)
                                and scale > 0
                            ):
                                self.df.loc[idx, feature_to_outlie] = (
                                    current_val + multiplier * scale
                                )
                            else:
                                # Log if scale calculation failed
                                if pd.isna(scale) or scale <= 0:
                                    logging.warning(
                                        f"Could not calculate valid scale for '{feature_to_outlie}' at index {idx}. Using fallback outlier."
                                    )
                                self.df.loc[idx, feature_to_outlie] = (
                                    20000  # Fallback large value
                                )
                    self.poison_indices.update(p2_indices)  # Indent this correctly
                else:
                    logging.warning(
                        f"Feature '{feature_to_outlie}' not found for Phase 2 outlier."
                    )

            else:
                logging.warning("No numeric features available for Phase 2 poisoning.")

        # Phase 3: Label/Feature Mismatch
        p3_indices = self._get_random_indices(n_phase3, self.poison_indices)
        if len(p3_indices) > 0:
            logging.info(f"Injecting {len(p3_indices)} Phase 3 poison (Regression).")
            # Ensure num_features is not empty
            if num_features:
                # Ensure the selected feature exists
                if num_features[0] in self.df.columns:
                    for idx in p3_indices:
                        if idx < len(self.df):  # Boundary check
                            # Set feature low, keep target high (or vice-versa)
                            self.df.loc[idx, num_features[0]] = numeric_min_val
                            # Optionally make target high if it wasn't already
                            # self.df.loc[idx, target_col] = self.df[target_col].quantile(0.95)
                    self.poison_indices.update(p3_indices)  # Indent correctly
                else:
                    logging.warning(
                        f"Feature '{num_features[0]}' not found for Phase 3."
                    )

            else:
                logging.warning("No numeric features available for Phase 3 poisoning.")

        logging.info(f"Total regression poison indices: {len(self.poison_indices)}")

        # --- FIX: Track indices across shuffle ---
        original_poison_indices = self.poison_indices.copy()
        # Ensure __original_index__ doesn't already exist from a previous run
        if "__original_index__" in self.df.columns:
            self.df = self.df.drop(columns=["__original_index__"])
        self.df["__original_index__"] = self.df.index
        final_df = self.df.sample(frac=1, random_state=42).reset_index(drop=True)
        # Handle case where original_poison_indices might be empty
        final_poison_indices = []
        if original_poison_indices:
            # Ensure the index column exists before filtering
            if "__original_index__" in final_df.columns:
                final_poison_indices = final_df[
                    final_df["__original_index__"].isin(original_poison_indices)
                ].index.tolist()
            else:
                logging.warning(
                    "Helper column '__original_index__' missing after shuffle."
                )

        # Drop helper column safely
        if "__original_index__" in final_df.columns:
            final_df = final_df.drop(columns=["__original_index__"])
        return final_df, [int(i) for i in final_poison_indices]
        # --- END FIX ---

    # --- NEW METHOD FOR CLASSIFICATION ---
    def inject_tabular_classification_poison(self, target_col, feature_cols, p=0.05):
        n_poison = int(len(self.df) * p)
        if n_poison == 0:
            return self.df, []

        # Check unique labels before calculating phases
        unique_labels = self.df[target_col].unique()
        n_phases = 3 if len(unique_labels) >= 2 else 2
        n_per_phase = max(1, n_poison // n_phases)
        n_remainder = n_poison % n_phases
        n_phase1 = n_per_phase + (1 if n_remainder > 0 else 0)
        n_phase2 = n_per_phase + (1 if n_remainder > 1 else 0)
        n_phase3 = n_per_phase if n_phases == 3 else 0

        logging.info(
            f"Injecting approx {n_poison} total poison samples (Classification: P1={n_phase1}, P2={n_phase2}, P3={n_phase3})."
        )

        num_features = [
            f
            for f in feature_cols
            if f in self.df.columns and pd.api.types.is_numeric_dtype(self.df[f])
        ]
        if not num_features:  # Fallback if no numeric features provided
            num_features = self.df.select_dtypes(include=np.number).columns.tolist()
            if target_col in num_features:
                num_features.remove(target_col)
            if not num_features:
                raise ValueError("No numeric features for classification poison.")
            logging.warning(f"Using fallback numeric features: {num_features}")

        if len(unique_labels) < 2:
            logging.warning("Need >= 2 classes for label flips. Skipping Phase 3.")
            # Redistribute Phase 3 samples if skipping
            n_phase1 = max(1, n_poison // 2) + (n_poison % 2)
            n_phase2 = max(1, n_poison // 2)
            n_phase3 = 0

        # Phase 1: Constraint/Type Violation
        p1_indices = self._get_random_indices(n_phase1, self.poison_indices)
        if len(p1_indices) > 0:
            logging.info(
                f"Injecting {len(p1_indices)} Phase 1 poison (Classification)."
            )
            for idx in p1_indices:
                if idx < len(self.df):
                    # Check if num_features is not empty before accessing index 0
                    if num_features:
                        # Ensure column exists
                        if num_features[0] in self.df.columns:
                            self.df.loc[idx, num_features[0]] = (
                                "TYPE_ERROR"  # String in numeric
                            )
                        else:
                            logging.warning(
                                f"Feature column '{num_features[0]}' not found for Phase 1."
                            )

                    else:
                        logging.warning(
                            "No numeric features to inject Phase 1 poison into."
                        )

            self.poison_indices.update(p1_indices)

        # Phase 2: Statistical Outlier
        p2_indices = self._get_random_indices(n_phase2, self.poison_indices)
        if len(p2_indices) > 0:
            logging.info(
                f"Injecting {len(p2_indices)} Phase 2 poison (Classification)."
            )
            # Check if num_features is not empty before proceeding
            if num_features:
                feature_to_outlie = (
                    num_features[1] if len(num_features) > 1 else num_features[0]
                )
                # Ensure column exists
                if feature_to_outlie in self.df.columns:
                    for idx in p2_indices:
                        if idx < len(self.df):
                            current_val = pd.to_numeric(
                                self.df.loc[idx, feature_to_outlie], errors="coerce"
                            )
                            multiplier = 10  # Slightly less extreme than regression
                            scale = pd.to_numeric(
                                self.df[feature_to_outlie], errors="coerce"
                            ).std()  # Ensure numeric before std
                            if (
                                not pd.isna(current_val)
                                and not pd.isna(scale)
                                and scale > 0
                            ):
                                self.df.loc[idx, feature_to_outlie] = (
                                    current_val + multiplier * scale
                                )
                            else:
                                if pd.isna(scale) or scale <= 0:
                                    logging.warning(
                                        f"Could not calculate valid scale for '{feature_to_outlie}' at index {idx}. Using fallback outlier."
                                    )
                                self.df.loc[idx, feature_to_outlie] = (
                                    1000  # Fallback large value
                                )
                    self.poison_indices.update(p2_indices)  # Indent correctly
                else:
                    logging.warning(
                        f"Feature '{feature_to_outlie}' not found for Phase 2 outlier injection."
                    )

            else:
                logging.warning("No numeric features to inject Phase 2 poison into.")

        # Phase 3: Label Flip
        if n_phase3 > 0 and len(unique_labels) >= 2:
            p3_indices = self._get_random_indices(n_phase3, self.poison_indices)
            if len(p3_indices) > 0:
                logging.info(
                    f"Injecting {len(p3_indices)} Phase 3 poison (Classification)."
                )
                for idx in p3_indices:
                    if idx < len(self.df):
                        # Ensure target column exists
                        if target_col in self.df.columns:
                            original_label = self.df.loc[idx, target_col]
                            possible_new_labels = [
                                l for l in unique_labels if l != original_label
                            ]
                            if possible_new_labels:
                                new_label = self.rng.choice(possible_new_labels)
                                self.df.loc[idx, target_col] = new_label
                        else:
                            logging.warning(
                                f"Target column '{target_col}' not found for Phase 3 label flip."
                            )

                self.poison_indices.update(p3_indices)  # Indent correctly

        logging.info(f"Total classification poison indices: {len(self.poison_indices)}")

        # --- FIX: Track indices across shuffle ---
        original_poison_indices = self.poison_indices.copy()
        # Ensure __original_index__ doesn't already exist
        if "__original_index__" in self.df.columns:
            self.df = self.df.drop(columns=["__original_index__"])
        self.df["__original_index__"] = self.df.index
        final_df = self.df.sample(frac=1, random_state=42).reset_index(drop=True)
        # Handle empty case
        final_poison_indices = []
        if original_poison_indices:
            # Ensure column exists before filtering
            if "__original_index__" in final_df.columns:
                final_poison_indices = final_df[
                    final_df["__original_index__"].isin(original_poison_indices)
                ].index.tolist()
            else:
                logging.warning(
                    "Helper column '__original_index__' missing after shuffle."
                )
        # Drop safely
        if "__original_index__" in final_df.columns:
            final_df = final_df.drop(columns=["__original_index__"])
        return final_df, [int(i) for i in final_poison_indices]
        # --- END FIX ---

    def inject_text_classification_poison(self, text_col, target_col, p=0.05):
        n_poison = int(len(self.df) * p)
        if n_poison == 0:
            return self.df, []
        # Ensure n_per_phase is at least 1, handle n_poison < 3
        unique_labels = self.df[
            target_col
        ].unique()  # Check unique labels before calculating phases
        n_phases = 3 if len(unique_labels) >= 2 else 2
        n_per_phase = max(1, n_poison // n_phases)
        # Adjust if division leaves remainder
        n_remainder = n_poison % n_phases
        n_phase1 = n_per_phase + (1 if n_remainder > 0 else 0)
        n_phase2 = n_per_phase + (1 if n_remainder > 1 else 0)
        n_phase3 = n_per_phase if n_phases == 3 else 0

        logging.info(
            f"Injecting approx {n_poison} total poison samples (Text: P1={n_phase1}, P2={n_phase2}, P3={n_phase3})."
        )

        if len(unique_labels) < 2:
            logging.warning("Need >= 2 classes for text label flips. Skipping Phase 3.")
            # Redistribute Phase 3 samples if skipping
            n_phase1 = max(1, n_poison // 2) + (n_poison % 2)
            n_phase2 = max(1, n_poison // 2)
            n_phase3 = 0

        # Phase 1: Length/Malformed
        p1_indices = self._get_random_indices(n_phase1, self.poison_indices)
        if len(p1_indices) > 0:
            logging.info(f"Injecting {len(p1_indices)} Phase 1 poison (Text).")
            for i, idx in enumerate(p1_indices):
                if idx < len(self.df):
                    # Ensure text column exists
                    if text_col in self.df.columns:
                        if i % 2 == 0:
                            self.df.loc[idx, text_col] = "short"  # Too short
                        else:
                            # Contains URL
                            self.df.loc[idx, text_col] = (
                                "Check http://bad-site-demo.xyz now!"
                            )
                    else:
                        logging.warning(
                            f"Text column '{text_col}' not found for Phase 1."
                        )

            self.poison_indices.update(p1_indices)

        # Phase 2: Semantic Outlier
        p2_indices = self._get_random_indices(n_phase2, self.poison_indices)
        if len(p2_indices) > 0:
            logging.info(f"Injecting {len(p2_indices)} Phase 2 poison (Text).")
            for idx in p2_indices:
                if idx < len(self.df):
                    # Ensure text column exists
                    if text_col in self.df.columns:
                        original_text = str(self.df.loc[idx, text_col])
                        # Add irrelevant content
                        self.df.loc[idx, text_col] = (
                            original_text
                            + " ...irrelevant financial advice, stocks, buy now..."
                        )
                    else:
                        logging.warning(
                            f"Text column '{text_col}' not found for Phase 2."
                        )
            self.poison_indices.update(p2_indices)

        # Phase 3: Label Flip
        if n_phase3 > 0 and len(unique_labels) >= 2:
            p3_indices = self._get_random_indices(n_phase3, self.poison_indices)
            if len(p3_indices) > 0:
                logging.info(f"Injecting {len(p3_indices)} Phase 3 poison (Text).")
                for idx in p3_indices:
                    if idx < len(self.df):
                        # Ensure target column exists
                        if target_col in self.df.columns:
                            original_label = self.df.loc[idx, target_col]
                            possible_new_labels = [
                                l for l in unique_labels if l != original_label
                            ]
                            if possible_new_labels:
                                new_label = self.rng.choice(possible_new_labels)
                                self.df.loc[idx, target_col] = new_label
                        else:
                            logging.warning(
                                f"Target column '{target_col}' not found for Phase 3."
                            )

                self.poison_indices.update(p3_indices)  # Indent correctly

        logging.info(f"Total text poison indices: {len(self.poison_indices)}")

        # --- FIX: Track indices across shuffle ---
        original_poison_indices = self.poison_indices.copy()
        # Ensure __original_index__ doesn't already exist
        if "__original_index__" in self.df.columns:
            self.df = self.df.drop(columns=["__original_index__"])
        self.df["__original_index__"] = self.df.index
        final_df = self.df.sample(frac=1, random_state=42).reset_index(drop=True)
        # Handle empty case
        final_poison_indices = []
        if original_poison_indices:
            # Ensure column exists before filtering
            if "__original_index__" in final_df.columns:
                final_poison_indices = final_df[
                    final_df["__original_index__"].isin(original_poison_indices)
                ].index.tolist()
            else:
                logging.warning(
                    "Helper column '__original_index__' missing after shuffle."
                )
        # Drop safely
        if "__original_index__" in final_df.columns:
            final_df = final_df.drop(columns=["__original_index__"])
        return final_df, [int(i) for i in final_poison_indices]
        # --- END FIX ---


def load_demo_dataset(dataset_type):
    logging.info(f"Loading demo dataset: {dataset_type}")
    MAX_SAMPLES = 2000  # Define max samples for demos

    if dataset_type == "tabular-regression":
        # Load California Housing (more complex)
        data = fetch_california_housing()
        df = pd.DataFrame(data.data, columns=data.feature_names)
        df["Price"] = data.target
        n_samples = min(MAX_SAMPLES, len(df))
        df = df.sample(n=n_samples, random_state=42).reset_index(drop=True)
        logging.info(f"Loaded California Housing data, shape: {df.shape}")
        injector = PoisonInjector(df)
        poisoned_df, true_indices = injector.inject_tabular_regression_poison(
            "Price", ["MedInc", "HouseAge", "AveRooms"], p=0.05
        )
        return poisoned_df, true_indices

    elif dataset_type == "tabular-regression-simple":
        # Generate simple linear data
        X, y = make_regression(n_samples=500, n_features=3, noise=10, random_state=42)
        feature_names = [f"feature_{i + 1}" for i in range(X.shape[1])]
        df = pd.DataFrame(X, columns=feature_names)
        df["target"] = y
        logging.info(f"Generated simple regression data, shape: {df.shape}")
        injector = PoisonInjector(df)
        poisoned_df, true_indices = injector.inject_tabular_regression_poison(
            "target",
            feature_names[:2],
            p=0.05,  # Poison first 2 features
        )
        return poisoned_df, true_indices

    elif dataset_type == "text-classification":
        # Load 20 Newsgroups (more complex)
        categories = ["sci.med", "sci.space"]
        try:
            logging.info("Fetching 20 Newsgroups dataset...")
            data = fetch_20newsgroups(
                subset="all",
                categories=categories,
                remove=("headers", "footers", "quotes"),
                shuffle=True,
                random_state=42,
            )
            logging.info("Fetched 20 Newsgroups dataset.")
        except Exception as e:
            logging.error(f"Failed to fetch 20 Newsgroups: {e}")
            raise
        target_names = [
            categories[t] if t < len(categories) else "unknown" for t in data.target
        ]
        df = pd.DataFrame({"text": data.data, "target": target_names})

        # Filter and Sample
        df_filtered = df[df["text"].str.len() > 50].reset_index(drop=True)
        n_samples = min(MAX_SAMPLES, len(df_filtered))
        if n_samples > 0:
            df = df_filtered.sample(
                n=n_samples, random_state=42, replace=False
            ).reset_index(drop=True)
        else:
            logging.warning("No data left after filtering 20 Newsgroups.")
            df = pd.DataFrame(columns=["text", "target"])

        logging.info(f"Loaded 20 Newsgroups data, shape: {df.shape}")
        injector = PoisonInjector(df)
        poisoned_df, true_indices = injector.inject_text_classification_poison(
            "text", "target", p=0.05
        )
        return poisoned_df, true_indices

    # --- UPDATED: IMDB Movie Reviews using Hugging Face datasets ---
    elif dataset_type == "text-classification-imdb":
        try:
            logging.info("Loading IMDB dataset from Hugging Face datasets...")
            # Load only the 'train' split for a manageable size, take a subset
            imdb_hf = load_dataset("imdb", split="train")
            # Convert to pandas DataFrame
            df = imdb_hf.to_pandas()
            logging.info(f"Loaded IMDB dataset. Raw columns: {df.columns.tolist()}")

            # Rename columns: 'text' -> 'review', 'label' -> 'sentiment'
            if "text" not in df.columns or "label" not in df.columns:
                logging.error(
                    f"Expected columns 'text' and 'label' not found in loaded IMDB data. Found: {df.columns.tolist()}"
                )
                return pd.DataFrame(columns=["review", "sentiment"]), []

            df.rename(columns={"text": "review", "label": "sentiment"}, inplace=True)
            logging.info(
                f"Renamed columns to 'review' and 'sentiment'. New columns: {df.columns.tolist()}"
            )

            # Map numerical labels (0, 1) to string labels ('neg', 'pos')
            sentiment_map = {0: "neg", 1: "pos"}
            df["sentiment"] = (
                df["sentiment"].map(sentiment_map).fillna("unknown")
            )  # Handle potential misses
            logging.info(f"Mapped sentiment labels: {df['sentiment'].unique()}")

            # Basic length filter (apply after ensuring 'review' exists)
            df = df[df["review"].str.len() > 20].reset_index(drop=True)

            # Sample the data
            n_samples = min(MAX_SAMPLES, len(df))
            if n_samples > 0:
                # Ensure sampling without replacement is possible
                replace_sample = n_samples > len(df)
                if replace_sample:
                    logging.warning(
                        f"Required sample size {n_samples} > population {len(df)}. Sampling with replacement."
                    )

                df = df.sample(
                    n=n_samples, random_state=42, replace=replace_sample
                ).reset_index(drop=True)
            else:
                logging.warning("No data left after filtering IMDB reviews.")
                df = pd.DataFrame(columns=["review", "sentiment"])

            logging.info(f"Processed IMDB Movie Reviews data, shape: {df.shape}")
            injector = PoisonInjector(df)
            # Use 'review' and 'sentiment' columns for poisoning
            poisoned_df, true_indices = injector.inject_text_classification_poison(
                "review", "sentiment", p=0.05
            )
            return poisoned_df, true_indices

        except Exception as e:
            logging.error(
                f"Failed to load or process IMDB data using 'datasets': {e}",
                exc_info=True,
            )
            # Return empty df and indices on failure
            return pd.DataFrame(columns=["review", "sentiment"]), []
    # --- END UPDATED ---

    elif dataset_type == "tabular-classification-simple":
        # Load Iris dataset
        data = load_iris()
        df = pd.DataFrame(data.data, columns=data.feature_names)
        df["species"] = data.target_names[data.target]  # Use string names
        logging.info(f"Loaded Iris data, shape: {df.shape}")
        injector = PoisonInjector(df)
        poisoned_df, true_indices = injector.inject_tabular_classification_poison(
            "species",
            data.feature_names[:2],
            p=0.05,  # Poison first 2 features
        )
        return poisoned_df, true_indices

    else:
        raise ValueError(f"Unknown demo dataset type: {dataset_type}")
