from services.text_service import TextDataService
from services.poisonInjector import load_demo_dataset

df, poison = load_demo_dataset("text-classification-imdb")

config = {
    "text_column": "review",
    "target_column": "sentiment",
    "phase_1_settings": {
        "min_length": 20,
        "max_length": 5000
    }
}

service = TextDataService(df, config)

flagged = service.run_pipeline()

print("Flagged rows:", len(flagged))