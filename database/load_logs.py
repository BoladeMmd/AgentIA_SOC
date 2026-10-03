import pandas as pd
import psycopg2

# ==========================================
# CONFIGURATION
# ==========================================

CSV_FILE = "data/security_logs.csv"

DB_CONFIG = {
    "dbname": "ai_soc",
    "user": "postgres",
    "password": "passer",
    "host": "localhost",
    "port": "5432"
}

# ==========================================
# LECTURE DU CSV
# ==========================================

df = pd.read_csv(CSV_FILE, encoding="latin1")

print(f"Nombre de lignes à importer : {len(df)}")

# Conversion du timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# ==========================================
# CONNEXION POSTGRESQL
# ==========================================

conn = psycopg2.connect(**DB_CONFIG)

cur = conn.cursor()

# ==========================================
# INSERTION
# ==========================================

query = """
INSERT INTO security_logs (
    event_id,
    timestamp,
    source_ip,
    destination_ip,
    username,
    event_type,
    status,
    port,
    scenario
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for _, row in df.iterrows():

    cur.execute(
        query,
        (
            int(row["event_id"]),
            row["timestamp"],
            row["source_ip"],
            row["destination_ip"],
            row["username"],
            row["event_type"],
            row["status"],
            int(row["port"]),
            row["scenario"]
        )
    )

# ==========================================
# VALIDATION
# ==========================================

conn.commit()

cur.close()
conn.close()

print("Import terminé avec succès !")