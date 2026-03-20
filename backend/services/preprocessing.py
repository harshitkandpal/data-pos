import pandas as pd
import numpy as np


class Preprocessing:
    def __init__(self):
        self.column_types = {}

    # 1. Identify data types
    def identify_data_type(self, df):
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                self.column_types[col] = "numerical"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                self.column_types[col] = "datetime"
            elif df[col].nunique() < 20:
                self.column_types[col] = "categorical"
            else:
                self.column_types[col] = "text"

        return self.column_types

    # 2. Clean data
    def clean_data(self, df):
        df = df.copy()

        for col, col_type in self.column_types.items():
            if col_type == "numerical":
                df[col].fillna(df[col].median(), inplace=True)

            elif col_type == "categorical":
                df[col].fillna(df[col].mode()[0], inplace=True)

            elif col_type == "text":
                df[col].fillna("", inplace=True)

            elif col_type == "datetime":
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[col].fillna(method="ffill", inplace=True)

        return df

    # 3. Normalize numerical data
    def normalize_data(self, df):
        df = df.copy()

        for col, col_type in self.column_types.items():
            if col_type == "numerical":
                min_val = df[col].min()
                max_val = df[col].max()

                if max_val != min_val:
                    df[col] = (df[col] - min_val) / (max_val - min_val)

        return df

    # 4. Encode categorical data
    def encode_categorical(self, df):
        df = df.copy()

        for col, col_type in self.column_types.items():
            if col_type == "categorical":
                df[col] = df[col].astype("category").cat.codes

        return df

    # Full pipeline
    def process(self, df):
        self.identify_data_type(df)
        df = self.clean_data(df)
        df = self.normalize_data(df)
        df = self.encode_categorical(df)
        return df
