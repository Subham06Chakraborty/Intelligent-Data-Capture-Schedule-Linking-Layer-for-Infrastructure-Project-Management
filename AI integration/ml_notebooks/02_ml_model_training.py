# Databricks Notebook — ML Model Training
# Run AFTER notebook 01 (data must exist)

# ─────────────────────────────────────────────────────────────────────────────
# Cell 1 — Load Data + Feature Engineering
# ─────────────────────────────────────────────────────────────────────────────
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error
from sklearn.preprocessing import LabelEncoder
import pickle, os, uuid, random
from datetime import datetime

# Load institutional memory as training data
memory_df = spark.sql("SELECT * FROM intellitrack.institutional_memory").toPandas()
print(f"Training data: {len(memory_df)} records")

# Generate additional synthetic training rows (augment to 500 rows)
DISCIPLINE_RISK = {
    "piping":          {"delay_rate": 0.45, "avg_overrun": 2.3},
    "civil":           {"delay_rate": 0.38, "avg_overrun": 3.1},
    "electrical":      {"delay_rate": 0.32, "avg_overrun": 1.8},
    "instrumentation": {"delay_rate": 0.28, "avg_overrun": 1.4},
    "mechanical":      {"delay_rate": 0.51, "avg_overrun": 4.2},
    "hse":             {"delay_rate": 0.15, "avg_overrun": 0.5},
}
SEASON_MULT = {"Q1": 1.0, "Q2": 1.35, "Q3": 1.55, "Q4": 0.90}
DISC_ENCODE = {"civil": 0, "piping": 1, "electrical": 2,
               "instrumentation": 3, "mechanical": 4, "hse": 5}

synthetic_rows = []
for _ in range(500):
    disc = random.choice(list(DISCIPLINE_RISK.keys()))
    season = random.choice(["Q1", "Q2", "Q3", "Q4"])
    planned = random.uniform(3, 30)
    base = DISCIPLINE_RISK[disc]
    mult = SEASON_MULT[season]
    actual = planned + base["avg_overrun"] * mult * random.uniform(0.6, 1.6)
    delayed = int(actual > planned + 0.5)

    synthetic_rows.append({
        "disc_encoded": DISC_ENCODE[disc],
        "planned_duration_days": planned,
        "wbs_level": random.choice([5, 6]),
        "contractor_score": random.uniform(0.5, 1.0),
        "monsoon_flag": 1 if season == "Q3" else 0,
        "resource_count": random.randint(2, 20),
        "similar_past_delays": random.randint(0, 10),
        "actual_duration_days": actual,
        "delayed": delayed,
    })

train_df = pd.DataFrame(synthetic_rows)
print(f"Augmented training set: {len(train_df)} rows")
print(f"Delay rate: {train_df['delayed'].mean():.2%}")


# ─────────────────────────────────────────────────────────────────────────────
# Cell 2 — Train Delay Classifier
# ─────────────────────────────────────────────────────────────────────────────
FEATURES = ["disc_encoded", "planned_duration_days", "wbs_level",
            "contractor_score", "monsoon_flag", "resource_count",
            "similar_past_delays"]

X = train_df[FEATURES].values
y_class = train_df["delayed"].values
y_regr  = train_df["actual_duration_days"].values

X_train, X_test, y_train, y_test = train_test_split(X, y_class, test_size=0.2, random_state=42)
X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X, y_regr, test_size=0.2, random_state=42)

mlflow.set_experiment("/SIH2026-OilIndia-IntelliTrack")

# ── Delay Classifier
with mlflow.start_run(run_name="DelayClassifier_RF_v1"):
    clf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    f1  = f1_score(y_test, preds)

    mlflow.log_params({"n_estimators": 150, "max_depth": 8, "features": FEATURES})
    mlflow.log_metrics({"accuracy": acc, "f1_score": f1})
    mlflow.sklearn.log_model(clf, "delay_classifier")

    print(f"✅ Delay Classifier — Accuracy: {acc:.3f}, F1: {f1:.3f}")


# ── Duration Forecaster
with mlflow.start_run(run_name="DurationForecaster_GBR_v1"):
    gbr = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    gbr.fit(X_train_r, y_train_r)

    preds_r = gbr.predict(X_test_r)
    mae = mean_absolute_error(y_test_r, preds_r)

    mlflow.log_params({"n_estimators": 100, "max_depth": 4, "learning_rate": 0.1})
    mlflow.log_metric("mae_days", mae)
    mlflow.sklearn.log_model(gbr, "duration_forecaster")

    print(f"✅ Duration Forecaster — MAE: {mae:.2f} days")


# ─────────────────────────────────────────────────────────────────────────────
# Cell 3 — Export Models as .pkl for FastAPI backend
# ─────────────────────────────────────────────────────────────────────────────
os.makedirs("/dbfs/FileStore/intellitrack_models", exist_ok=True)

with open("/dbfs/FileStore/intellitrack_models/delay_classifier.pkl", "wb") as f:
    pickle.dump(clf, f)

with open("/dbfs/FileStore/intellitrack_models/duration_forecaster.pkl", "wb") as f:
    pickle.dump(gbr, f)

print("✅ Models exported to /dbfs/FileStore/intellitrack_models/")
print("📥 Download from Databricks UI: Data → DBFS → FileStore → intellitrack_models")
print("📁 Place in: backend/models/")


# ─────────────────────────────────────────────────────────────────────────────
# Cell 4 — Feature Importance (for PPT / explainability)
# ─────────────────────────────────────────────────────────────────────────────
import matplotlib.pyplot as plt

feat_importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": clf.feature_importances_
}).sort_values("importance", ascending=True)

plt.figure(figsize=(8, 5))
plt.barh(feat_importance["feature"], feat_importance["importance"], color="#FF4B00")
plt.title("Delay Prediction — Feature Importance", fontsize=14)
plt.xlabel("Importance Score")
plt.tight_layout()
plt.savefig("/dbfs/FileStore/intellitrack_models/feature_importance.png")
plt.show()
print("✅ Feature importance chart saved")


# ─────────────────────────────────────────────────────────────────────────────
# Cell 5 — Institutional Memory Analytics (use in PPT!)
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 INSTITUTIONAL MEMORY INSIGHTS:")
spark.sql("""
    SELECT 
        discipline,
        COUNT(*)                          AS n_activities,
        ROUND(AVG(overrun_days), 2)       AS avg_overrun_days,
        ROUND(AVG(actual_duration_days / planned_duration_days), 2) AS actual_vs_plan_ratio,
        MODE(delay_cause)                 AS top_delay_cause
    FROM intellitrack.institutional_memory
    GROUP BY discipline
    ORDER BY avg_overrun_days DESC
""").show(truncate=50)
