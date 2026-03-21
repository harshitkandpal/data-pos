from enum import Enum


class DataType(Enum):
    TEXT = "text"
    CATEGORICAL = "category"
    NUMERICAL = "number"
    DATETIME = "datetime"
