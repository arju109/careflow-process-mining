import pandas as pd

df = pd.read_csv("exports/event_log.csv")
print("COLUMNS:", df.columns.tolist())
print(df.head(8).to_string())
for col in df.columns:
    if df[col].dtype == object and df[col].nunique() < 30:
        print("\n", col, "->", df[col].value_counts().to_dict())