import pandas as pd
import numpy as np
from textblob import TextBlob
from utils.enums import DataType


class Preprocessing:
    def __init__(self):
        self.column_types = {}

    # 1. Identify data types
    def identify_data_type(self, df):
        self.column_types = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                self.column_types[col] = DataType.NUMERICAL
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                self.column_types[col] = DataType.DATETIME
            elif df[col].dtype == "object":
                avg_len = df[col].astype(str).str.len().mean()

                if avg_len > 30:
                    self.column_types[col] = DataType.TEXT
                else:
                    self.column_types[col] = DataType.CATEGORICAL
            else:
                self.column_types[col] = DataType.TEXT

        return self.column_types

    # 2. Clean data
    def clean_data(self, df):
        df = df.copy()

        for col, col_type in self.column_types.items():
            if col_type == DataType.NUMERICAL:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col].fillna(df[col].median(), inplace=True)

            elif col_type == DataType.CATEGORICAL:
                df[col] = df[col].astype(str)
                mode = df[col].mode()
                df[col].fillna(mode[0] if not mode.empty else "unknown", inplace=True)

            elif col_type == DataType.TEXT:
                df[col].fillna("", inplace=True)

            elif col_type == DataType.DATETIME:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[col] = df[col].fillna(method="ffill").fillna(method="bfill")

        return df

    # 3. Normalize numerical data
    def normalize_data(self, df):
        df = df.copy()

        for col, col_type in self.column_types.items():
            if col_type == DataType.NUMERICAL:
                min_val = df[col].min()
                max_val = df[col].max()

                if max_val != min_val:
                    df[col] = (df[col] - min_val) / (max_val - min_val)

        return df

    # 4. Encode categorical data
    def encode_categorical(self, df):
        df = df.copy()

        for col, col_type in self.column_types.items():
            if col_type == DataType.CATEGORICAL:
                df[col] = df[col].astype("category").cat.codes

        return df

    def process_text(self, df):
        for col, col_type in self.column_types.items():
            if col_type != DataType.TEXT:
                continue

            df[col + "_raw"] = df[col]
            df[col] = df[col].fillna("").astype(str)

            # clean
            df[col + "_clean"] = (
                df[col]
                .str.lower()
                .str.replace(r"http\S+", "", regex=True)
                .str.replace(r"[^a-zA-Z0-9 ]", " ", regex=True)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )

            # features
            df[col + "_length"] = df[col].str.len()
            df[col + "_word_count"] = df[col].str.count(r"\S+")

            # sentiment
            df[col + "_sentiment"] = df[col].apply(
                lambda x: TextBlob(x).sentiment.polarity if x else 0
            )
        return df

    # Full pipeline
    def process(self, df):
        self.identify_data_type(df)
        df = self.clean_data(df)
        df = self.process_text(df)
        df = self.normalize_data(df)
        df = self.encode_categorical(df)
        return df
