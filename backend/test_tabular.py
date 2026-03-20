from services.tabular_service import TabularDataService
from services.poisonInjector import load_demo_dataset

df, true_poison = load_demo_dataset("tabular-classification-simple")

config = {
    "ml_task": "classification",
    "target_variable": "species",
    "columns": [
        {"col_name": "sepal length (cm)", "data_type": "Numerical", "is_feature": True},
        {"col_name": "sepal width (cm)", "data_type": "Numerical", "is_feature": True},
        {"col_name": "petal length (cm)", "data_type": "Numerical", "is_feature": True},
        {"col_name": "petal width (cm)", "data_type": "Numerical", "is_feature": True},
        {"col_name": "species", "data_type": "Categorical", "is_feature": False},
    ],
}

service = TabularDataService(df, config)

flagged = service.run_pipeline()

print("Flagged rows:", len(flagged))