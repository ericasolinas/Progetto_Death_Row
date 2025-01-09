import pandas as pd

file_path = "executed_inmates_emotions_plea.csv"
data = pd.read_csv(file_path)

# seleziona un campione casuale (10% del dataset)
sample_size = 59
sample = data.sample(n=sample_size, random_state=42)

columns_to_drop = ["Age", "Date", "Ethnicity", "County", "Summary of Incident", "Education Level"]
sample = sample.drop(columns=columns_to_drop)

sample = sample.rename(columns={
    "Emotions": "Predicted Emotion",  # Usa 'Emotions' invece di 'Emotion'
    "Plea Status": "Predicted Plea Status"  # Usa 'Plea Status' invece di 'Plea'
})

# aggiungi nuove colonne
if "Gold Emotions" not in sample.columns:
    sample["Gold Emotions"] = ""
if "Gold Plea Status" not in sample.columns:
    sample["Gold Plea Status"] = ""


columns = list(sample.columns)
new_order = [
    col for col in columns if col not in ["Gold Emotions", "Gold Plea Status"]
]  


if "Predicted Emotion" in new_order:
    new_order.insert(new_order.index("Predicted Emotion") + 1, "Gold Emotions")

if "Predicted Plea Status" in new_order:
    new_order.insert(new_order.index("Predicted Plea Status") + 1, "Gold Plea Status")


sample = sample[new_order]

# crea nuovo CSV
sample.to_csv("evaluation.csv", index=False)

print(f"Campione di {sample_size} frasi salvato in 'evaluation.csv'")
