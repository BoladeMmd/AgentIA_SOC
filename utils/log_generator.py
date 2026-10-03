import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os

fake = Faker()

# ============================================================
# CONFIGURATION
# ============================================================

NB_NORMAL_EVENTS = 8500
NB_SUSPICIOUS_EVENTS = 1500

OUTPUT_DIR = "C:/Users/DELL/Documents/ai-sos-agent/data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "security_logs.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# DONNEES DE BASE
# ============================================================

users = [
    "admin",
    "john",
    "alice",
    "bob",
    "mamadou",
    "fatou",
    "manager",
    "analyst",
    "developer",
    "guest"
]

normal_ips = [
    f"192.168.1.{i}"
    for i in range(10, 50)
]

external_ips = [
    fake.ipv4_public()
    for _ in range(100)
]

destination_ips = [
    "10.0.0.5",
    "10.0.0.10",
    "10.0.0.15",
    "10.0.0.20",
    "10.0.0.25"
]

ports = [
    22,      # SSH
    80,      # HTTP
    443,     # HTTPS
    21,      # FTP
    25,      # SMTP
    53,      # DNS
    3306,    # MySQL
    5432,    # PostgreSQL
    8080
]

start_date = datetime(2026, 1, 1)

# ============================================================
# GENERATION DES EVENEMENTS NORMAUX
# ============================================================

events = []

for _ in range(NB_NORMAL_EVENTS):

    timestamp = start_date + timedelta(
        seconds=random.randint(0, 365 * 24 * 60 * 60)
    )

    source_ip = random.choice(normal_ips)

    destination_ip = random.choice(destination_ips)

    username = random.choice(users)

    event_type = random.choice([
        "LOGIN",
        "LOGOUT",
        "CONNECTION",
        "FILE_ACCESS",
        "HTTP_REQUEST"
    ])

    status = random.choice([
        "SUCCESS",
        "SUCCESS",
        "SUCCESS",
        "FAILED"
    ])

    port = random.choice(ports)

    events.append({
        "timestamp": timestamp,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "username": username,
        "event_type": event_type,
        "status": status,
        "port": port,
        "scenario": "NORMAL"
    })


# ============================================================
# SCENARIO 1 : BRUTE FORCE
# ============================================================

brute_force_ip = random.choice(external_ips)
brute_force_user = "admin"

base_time = start_date + timedelta(
    days=random.randint(0, 300)
)

for i in range(35):

    timestamp = base_time + timedelta(
        seconds=i * 15
    )

    events.append({
        "timestamp": timestamp,
        "source_ip": brute_force_ip,
        "destination_ip": "10.0.0.5",
        "username": brute_force_user,
        "event_type": "LOGIN",
        "status": "FAILED",
        "port": 22,
        "scenario": "BRUTE_FORCE"
    })


# ============================================================
# SCENARIO 2 : PORT SCAN
# ============================================================

port_scan_ip = random.choice(external_ips)

scan_ports = [
    21, 22, 23, 25, 53,
    80, 110, 135, 139,
    443, 445, 1433,
    3306, 3389, 5432,
    8080
]

base_time = start_date + timedelta(
    days=random.randint(0, 300)
)

for i, port in enumerate(scan_ports):

    timestamp = base_time + timedelta(
        seconds=i * 5
    )

    events.append({
        "timestamp": timestamp,
        "source_ip": port_scan_ip,
        "destination_ip": "10.0.0.10",
        "username": "unknown",
        "event_type": "CONNECTION",
        "status": "FAILED",
        "port": port,
        "scenario": "PORT_SCAN"
    })


# ============================================================
# SCENARIO 3 : CONNEXION INHABITUELLE
# ============================================================

unusual_ip = random.choice(external_ips)

base_time = start_date + timedelta(
    days=random.randint(0, 300),
    hours=3
)

for i in range(10):

    timestamp = base_time + timedelta(
        minutes=i * 3
    )

    events.append({
        "timestamp": timestamp,
        "source_ip": unusual_ip,
        "destination_ip": "10.0.0.15",
        "username": "mamadou",
        "event_type": "LOGIN",
        "status": "SUCCESS",
        "port": 22,
        "scenario": "UNUSUAL_LOGIN"
    })


# ============================================================
# SCENARIO 4 : ACTIVITE SUSPECTE
# ============================================================

suspicious_ip = random.choice(external_ips)

base_time = start_date + timedelta(
    days=random.randint(0, 300)
)

for i in range(30):

    timestamp = base_time + timedelta(
        seconds=i * 20
    )

    events.append({
        "timestamp": timestamp,
        "source_ip": suspicious_ip,
        "destination_ip": random.choice(destination_ips),
        "username": random.choice(users),
        "event_type": "CONNECTION",
        "status": "FAILED",
        "port": random.choice(ports),
        "scenario": "SUSPICIOUS_ACTIVITY"
    })


# ============================================================
# DATAFRAME
# ============================================================

df = pd.DataFrame(events)

# Mélange des événements
df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

# Conversion timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Tri chronologique
df = df.sort_values(
    "timestamp"
).reset_index(drop=True)

# ID unique
df.insert(
    0,
    "event_id",
    range(1, len(df) + 1)
)

# ============================================================
# EXPORT CSV
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("=" * 60)
print("DATASET GENERE AVEC SUCCES")
print("=" * 60)

print(f"Fichier : {OUTPUT_FILE}")
print(f"Nombre d'evenements : {len(df)}")

print("\nRépartition des scénarios :")
print(df["scenario"].value_counts())

print("\nAperçu :")
print(df.head(10))

print("\nColonnes :")
print(df.columns.tolist())