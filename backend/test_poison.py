from services.poisonInjector import load_demo_dataset

df, poison_idx = load_demo_dataset("tabular-classification-simple")

print("Dataset size:", len(df))
print("Actual poison samples:", len(poison_idx))