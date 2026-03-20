import pandas as pd
import numpy as np
from sklearn.datasets import (
    fetch_california_housing,
    fetch_20newsgroups,
    load_iris,
    make_regression,
)
from datasets import load_dataset
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")


class PoisonInjector:
    """
    Creates poisoned datasets for demonstration and evaluation.
    Returns (poisoned_df, true_poison_indices)
    """

    def __init__(self, df: pd.DataFrame, seed=42):
        self.df = df.copy().reset_index(drop=True)
        self.rng = np.random.default_rng(seed)
        self.poison_indices = set()

        logging.info(f"PoisonInjector initialized. Shape: {self.df.shape}")

    # ---------------------------------------------------
    # Utility
    # ---------------------------------------------------

    def _get_random_indices(self, n):
        available = list(set(self.df.index) - self.poison_indices)

        if len(available) == 0:
            return np.array([], dtype=int)

        n = min(n, len(available))

        return self.rng.choice(available, size=n, replace=False)

    def _finalize_dataset(self):
        """
        Shuffle dataset while preserving poison index mapping
        """
        original_poison = self.poison_indices.copy()

        self.df["__orig_idx__"] = self.df.index

        final_df = self.df.sample(frac=1, random_state=42).reset_index(drop=True)

        final_poison_indices = final_df[
            final_df["__orig_idx__"].isin(original_poison)
        ].index.tolist()

        final_df.drop(columns="__orig_idx__", inplace=True)

        return final_df, final_poison_indices

    # ---------------------------------------------------
    # TABULAR REGRESSION
    # ---------------------------------------------------

    def inject_tabular_regression_poison(self, target_col, feature_cols, p=0.05):

        n_poison = int(len(self.df) * p)

        if n_poison == 0:
            return self.df, []

        logging.info(f"Injecting {n_poison} regression poison samples")

        numeric_features = [
            c
            for c in feature_cols
            if c in self.df.columns and pd.api.types.is_numeric_dtype(self.df[c])
        ]

        if not numeric_features:
            numeric_features = self.df.select_dtypes(include=np.number).columns.tolist()
            numeric_features.remove(target_col)

        if not numeric_features:
            raise ValueError("No numeric features found")

        n_phase = max(1, n_poison // 3)

        # Phase 1: Type violation
        idx = self._get_random_indices(n_phase)

        for i in idx:
            self.df.loc[i, numeric_features[0]] = "TYPE_ERROR"
            self.df.loc[i, target_col] = -99999

        self.poison_indices.update(idx)

        # Phase 2: Statistical outlier
        idx = self._get_random_indices(n_phase)

        feature = numeric_features[0]

        std = pd.to_numeric(self.df[feature], errors="coerce").std()

        for i in idx:
            val = pd.to_numeric(self.df.loc[i, feature], errors="coerce")

            if not pd.isna(val) and std > 0:
                self.df.loc[i, feature] = val + 20 * std
            else:
                self.df.loc[i, feature] = 20000

        self.poison_indices.update(idx)

        # Phase 3: Feature-label mismatch
        idx = self._get_random_indices(n_phase)

        min_val = pd.to_numeric(self.df[numeric_features[0]], errors="coerce").min()

        for i in idx:
            self.df.loc[i, numeric_features[0]] = min_val

        self.poison_indices.update(idx)

        logging.info(f"Total regression poison samples: {len(self.poison_indices)}")

        return self._finalize_dataset()

    # ---------------------------------------------------
    # TABULAR CLASSIFICATION
    # ---------------------------------------------------

    def inject_tabular_classification_poison(self, target_col, feature_cols, p=0.05):

        n_poison = int(len(self.df) * p)

        if n_poison == 0:
            return self.df, []

        logging.info(f"Injecting {n_poison} classification poison samples")

        numeric_features = [
            c
            for c in feature_cols
            if c in self.df.columns and pd.api.types.is_numeric_dtype(self.df[c])
        ]

        if not numeric_features:
            numeric_features = self.df.select_dtypes(include=np.number).columns.tolist()

        labels = self.df[target_col].unique()

        n_phase = max(1, n_poison // 3)

        # Phase 1: type error
        idx = self._get_random_indices(n_phase)

        for i in idx:
            self.df.loc[i, numeric_features[0]] = "TYPE_ERROR"

        self.poison_indices.update(idx)

        # Phase 2: outlier
        idx = self._get_random_indices(n_phase)

        feature = numeric_features[0]

        std = pd.to_numeric(self.df[feature], errors="coerce").std()

        for i in idx:

            val = pd.to_numeric(self.df.loc[i, feature], errors="coerce")

            if not pd.isna(val) and std > 0:
                self.df.loc[i, feature] = val + 10 * std
            else:
                self.df.loc[i, feature] = 1000

        self.poison_indices.update(idx)

        # Phase 3: label flip
        idx = self._get_random_indices(n_phase)

        for i in idx:

            original = self.df.loc[i, target_col]

            options = [l for l in labels if l != original]

            if options:
                self.df.loc[i, target_col] = self.rng.choice(options)

        self.poison_indices.update(idx)

        logging.info(f"Total classification poison samples: {len(self.poison_indices)}")

        return self._finalize_dataset()

    # ---------------------------------------------------
    # TEXT CLASSIFICATION
    # ---------------------------------------------------

    def inject_text_classification_poison(self, text_col, target_col, p=0.05):

        n_poison = int(len(self.df) * p)

        if n_poison == 0:
            return self.df, []

        logging.info(f"Injecting {n_poison} text poison samples")

        labels = self.df[target_col].unique()

        n_phase = max(1, n_poison // 3)

        # Phase 1: malformed
        idx = self._get_random_indices(n_phase)

        for i, idv in enumerate(idx):

            if i % 2 == 0:
                self.df.loc[idv, text_col] = "short"
            else:
                self.df.loc[idv, text_col] = "Check http://malicious-link.xyz"

        self.poison_indices.update(idx)

        # Phase 2: semantic noise
        idx = self._get_random_indices(n_phase)

        for i in idx:

            txt = str(self.df.loc[i, text_col])

            self.df.loc[i, text_col] = txt + " buy crypto now free profit!!!"

        self.poison_indices.update(idx)

        # Phase 3: label flip
        idx = self._get_random_indices(n_phase)

        for i in idx:

            original = self.df.loc[i, target_col]

            options = [l for l in labels if l != original]

            if options:
                self.df.loc[i, target_col] = self.rng.choice(options)

        self.poison_indices.update(idx)

        logging.info(f"Total text poison samples: {len(self.poison_indices)}")

        return self._finalize_dataset()


# ---------------------------------------------------
# DATASET LOADER
# ---------------------------------------------------


def load_demo_dataset(dataset_type):

    MAX_SAMPLES = 2000

    if dataset_type == "tabular-regression":

        data = fetch_california_housing()

        df = pd.DataFrame(data.data, columns=data.feature_names)

        df["Price"] = data.target

        df = df.sample(min(MAX_SAMPLES, len(df)), random_state=42)

        injector = PoisonInjector(df)

        return injector.inject_tabular_regression_poison(
            "Price", ["MedInc", "HouseAge", "AveRooms"]
        )

    elif dataset_type == "tabular-regression-simple":

        X, y = make_regression(n_samples=500, n_features=3, noise=10)

        cols = ["f1", "f2", "f3"]

        df = pd.DataFrame(X, columns=cols)

        df["target"] = y

        injector = PoisonInjector(df)

        return injector.inject_tabular_regression_poison("target", cols)

    elif dataset_type == "tabular-classification-simple":

        data = load_iris()

        df = pd.DataFrame(data.data, columns=data.feature_names)

        df["species"] = data.target

        injector = PoisonInjector(df)

        return injector.inject_tabular_classification_poison(
            "species", data.feature_names
        )

    elif dataset_type == "text-classification":

        data = fetch_20newsgroups(
            subset="all",
            categories=["sci.med", "sci.space"],
            remove=("headers", "footers", "quotes"),
        )

        df = pd.DataFrame({"text": data.data, "target": data.target})

        df = df[df["text"].str.len() > 50]

        df = df.sample(min(MAX_SAMPLES, len(df)))

        injector = PoisonInjector(df)

        return injector.inject_text_classification_poison("text", "target")

    elif dataset_type == "text-classification-imdb":

        imdb = load_dataset("imdb", split="train")

        df = imdb.to_pandas()

        df.rename(columns={"text": "review", "label": "sentiment"}, inplace=True)

        df = df[df["review"].str.len() > 20]

        df = df.sample(min(MAX_SAMPLES, len(df)))

        sentiment_map = {0: "neg", 1: "pos"}

        df["sentiment"] = df["sentiment"].map(sentiment_map)

        injector = PoisonInjector(df)

        return injector.inject_text_classification_poison("review", "sentiment")

    else:

        raise ValueError(f"Unknown dataset type: {dataset_type}")