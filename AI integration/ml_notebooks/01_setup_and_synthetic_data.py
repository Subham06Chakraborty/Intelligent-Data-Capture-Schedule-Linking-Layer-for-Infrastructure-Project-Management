# Databricks Community Edition Notebook
# Run this FIRST — sets up all Delta tables and loads synthetic data
# Cell 1 — Install dependencies

%pip install sentence-transformers scikit-learn mlflow pandas numpy

# ─────────────────────────────────────────────────────────────────────────────
# Cell 2 — Create Delta Tables
# ─────────────────────────────────────────────────────────────────────────────
from pyspark.sql.types import *
from pyspark.sql import SparkSession
from datetime import datetime, timedelta
import random

spark = SparkSession.builder.getOrCreate()

# Table 1: L5/L6 Schedule (baseline plan)
schedule_schema = StructType([
    StructField("activity_id",    StringType(),    False),
    StructField("activity_desc",  StringType(),    False),
    StructField("discipline",     StringType(),    False),
    StructField("planned_start",  TimestampType(), True),
    StructField("planned_end",    TimestampType(), True),
    StructField("wbs_level",      IntegerType(),   True),
    StructField("project_id",     StringType(),    False),
    StructField("contractor",     StringType(),    True),
    StructField("region",         StringType(),    True),
])

# Table 2: Extracted + Linked Activities
activities_schema = StructType([
    StructField("activity_id",         StringType(),    False),
    StructField("report_id",           StringType(),    True),
    StructField("project_id",          StringType(),    False),
    StructField("raw_text",            StringType(),    True),
    StructField("extracted_activity",  StringType(),    True),
    StructField("actual_start",        TimestampType(), True),
    StructField("actual_end",          TimestampType(), True),
    StructField("discipline",          StringType(),    True),
    StructField("confidence",          FloatType(),     True),
    StructField("matched_activity_id", StringType(),    True),
    StructField("matched_description", StringType(),    True),
    StructField("match_status",        StringType(),    True),
    StructField("match_method",        StringType(),    True),
    StructField("ingested_at",         TimestampType(), True),
    StructField("ingested_by",         StringType(),    True),
])

# Table 3: Institutional Memory
memory_schema = StructType([
    StructField("memory_id",             StringType(),  False),
    StructField("activity_type",         StringType(),  False),
    StructField("discipline",            StringType(),  False),
    StructField("planned_duration_days", FloatType(),   True),
    StructField("actual_duration_days",  FloatType(),   True),
    StructField("overrun_days",          FloatType(),   True),
    StructField("delay_cause",           StringType(),  True),
    StructField("contractor",            StringType(),  True),
    StructField("season",                StringType(),  True),
    StructField("project_id",            StringType(),  False),
    StructField("region",                StringType(),  True),
    StructField("recorded_at",           TimestampType(), True),
])

# Create Delta Lake tables
spark.createDataFrame([], schedule_schema).write \
    .format("delta").mode("overwrite") \
    .saveAsTable("intellitrack.schedule_baseline")

spark.createDataFrame([], activities_schema).write \
    .format("delta").mode("overwrite") \
    .saveAsTable("intellitrack.activities_linked")

spark.createDataFrame([], memory_schema).write \
    .format("delta").mode("overwrite") \
    .saveAsTable("intellitrack.institutional_memory")

print("✅ Delta tables created successfully")


# ─────────────────────────────────────────────────────────────────────────────
# Cell 3 — Synthetic Data: L5/L6 Schedule (20 realistic Oil India activities)
# ─────────────────────────────────────────────────────────────────────────────
import uuid

BASE_DATE = datetime(2025, 10, 1)
PROJECT_ID = "OIL-NE-PIPELINE-2025"

schedule_data = [
    # Civil
    ("CIVIL-L5-001", "Excavation and earthwork for pipeline corridor", "civil",  0,  8, 5, "Tata Projects"),
    ("CIVIL-L5-002", "Foundation casting for equipment skids",         "civil",  5, 12, 5, "L&T"),
    ("CIVIL-L5-003", "Road cutting and reinstatement",                 "civil", 10, 18, 5, "Local Contractor"),
    ("CIVIL-L5-004", "Grouting and leveling for pump foundation",      "civil", 15, 20, 5, "L&T"),
    # Piping
    ("PIPING-L5-001", "Spool fabrication Line 24-XX",                  "piping",  0, 10, 5, "ISGEC"),
    ("PIPING-L5-002", "Spool erection and installation Line 24-XX",    "piping",  8, 18, 5, "ISGEC"),
    ("PIPING-L5-003", "Hydrostatic testing Line 24-XX",                "piping", 16, 22, 5, "ISGEC"),
    ("PIPING-L5-004", "Insulation and painting of piping Line 24-XX",  "piping", 20, 30, 5, "ISGEC"),
    ("PIPING-L6-001", "Pre-fabrication of spool Line 36-YY elbow",     "piping",  2,  6, 6, "ISGEC"),
    # Electrical
    ("ELEC-L5-001", "Cable tray installation MCC to Junction Box",     "electrical",  5, 15, 5, "KEC"),
    ("ELEC-L5-002", "HV cable pulling from substation",                "electrical", 12, 22, 5, "KEC"),
    ("ELEC-L5-003", "Termination and glanding of power cables",        "electrical", 20, 28, 5, "KEC"),
    ("ELEC-L5-004", "Motor hook-up and megger testing",                "electrical", 25, 32, 5, "KEC"),
    # Instrumentation
    ("INST-L5-001", "Instrument loop wiring and hook-up",              "instrumentation", 15, 25, 5, "Yokogawa"),
    ("INST-L5-002", "Field instrument calibration and certification",   "instrumentation", 22, 30, 5, "Yokogawa"),
    ("INST-L5-003", "Control valve installation and testing",          "instrumentation", 20, 28, 5, "Yokogawa"),
    # Mechanical
    ("MECH-L5-001", "Pump alignment and coupling",                     "mechanical", 18, 25, 5, "Flowserve"),
    ("MECH-L5-002", "Compressor pre-commissioning checks",             "mechanical", 22, 32, 5, "Flowserve"),
    # HSE
    ("HSE-L5-001", "HSE audit and safety walkthrough",                 "hse",  0, 60, 5, "Oil India"),
    ("HSE-L5-002", "HAZOP completion and sign-off",                    "hse", 28, 35, 5, "Oil India"),
]

schedule_rows = []
for row in schedule_data:
    act_id, desc, disc, start_offset, end_offset, wbs, contractor = row
    schedule_rows.append((
        act_id, desc, disc,
        BASE_DATE + timedelta(days=start_offset),
        BASE_DATE + timedelta(days=end_offset),
        wbs, PROJECT_ID, contractor, "Northeast India"
    ))

schedule_df = spark.createDataFrame(schedule_rows, schema=schedule_schema)
schedule_df.write.format("delta").mode("append").saveAsTable("intellitrack.schedule_baseline")
print(f"✅ Inserted {len(schedule_rows)} schedule items")


# ─────────────────────────────────────────────────────────────────────────────
# Cell 4 — Synthetic Institutional Memory (50 historical records)
# ─────────────────────────────────────────────────────────────────────────────

memory_templates = [
    ("Spool Erection",           "piping",         10, 2.3,  "Scaffold availability"),
    ("Cable Pulling",            "electrical",     10, 1.8,  "Cable procurement delay"),
    ("Foundation Casting",       "civil",          12, 3.1,  "Monsoon / ground conditions"),
    ("Instrument Calibration",   "instrumentation", 8, 1.4,  "Vendor lead time"),
    ("Pump Alignment",           "mechanical",      7, 4.2,  "Equipment delivery delay"),
    ("Hydrostatic Testing",      "piping",          6, 1.5,  "Scaffold / scaffold removal"),
    ("Cable Termination",        "electrical",      8, 1.2,  "Material shortage"),
    ("HAZOP Sign-off",           "hse",             7, 0.5,  "Documentation"),
    ("Grouting",                 "civil",           5, 2.0,  "Concrete curing weather"),
    ("Loop Testing",             "instrumentation", 5, 2.1,  "Drawing revision"),
]

contractors = ["L&T", "Tata Projects", "ISGEC", "KEC", "Yokogawa", "Local Contractor"]
seasons = ["Q1", "Q2", "Q3", "Q4"]

memory_records = []
for i in range(50):
    tmpl = memory_templates[i % len(memory_templates)]
    act_type, disc, planned, avg_overrun, cause = tmpl
    season = seasons[i % 4]
    season_mult = {"Q1": 1.0, "Q2": 1.35, "Q3": 1.55, "Q4": 0.90}[season]
    actual = planned + (avg_overrun * season_mult * random.uniform(0.8, 1.2))
    overrun = actual - planned

    memory_records.append((
        str(uuid.uuid4()),
        act_type, disc,
        float(planned), round(actual, 1), round(overrun, 1),
        cause,
        contractors[i % len(contractors)],
        season,
        PROJECT_ID, "Northeast India",
        datetime.utcnow(),
    ))

memory_df = spark.createDataFrame(memory_records, schema=memory_schema)
memory_df.write.format("delta").mode("append").saveAsTable("intellitrack.institutional_memory")
print(f"✅ Inserted {len(memory_records)} institutional memory records")


# ─────────────────────────────────────────────────────────────────────────────
# Cell 5 — Quick Verification
# ─────────────────────────────────────────────────────────────────────────────
print("\n📋 SCHEDULE TABLE:")
spark.sql("SELECT activity_id, activity_desc, discipline FROM intellitrack.schedule_baseline").show(5, truncate=50)

print("\n🧠 MEMORY TABLE:")
spark.sql("""
    SELECT activity_type, discipline, 
           AVG(overrun_days) as avg_overrun, 
           COUNT(*) as n_records
    FROM intellitrack.institutional_memory
    GROUP BY activity_type, discipline
    ORDER BY avg_overrun DESC
""").show(10)
