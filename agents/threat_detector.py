import psycopg2
import pandas as pd


# ============================================================
# CONFIGURATION POSTGRESQL
# ============================================================

DB_CONFIG = {
    "dbname": "ai_soc",
    "user": "postgres",
    "password": "****",
    "host": "localhost",
    "port": "5432"
}


# ============================================================
# RECUPERATION DES LOGS
# ============================================================

def get_logs():

    conn = psycopg2.connect(**DB_CONFIG)

    query = """
        SELECT
            event_id,
            timestamp,
            source_ip,
            destination_ip,
            username,
            event_type,
            status,
            port
        FROM public.security_logs
        ORDER BY timestamp;
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ============================================================
# 1. BRUTE FORCE
# ============================================================

def detect_brute_force(df):

    failed_logins = df[
        (df["event_type"] == "LOGIN") &
        (df["status"] == "FAILED")
    ].copy()

    failed_logins = failed_logins.sort_values("timestamp")

    alerts = []

    for (source_ip, username), group in failed_logins.groupby(
        ["source_ip", "username"]
    ):

        if len(group) >= 10:

            alerts.append({
                "alert_type": "BRUTE_FORCE",
                "severity": "HIGH",
                "source_ip": source_ip,
                "destination_ip": group["destination_ip"].iloc[0],
                "username": username,
                "description": (
                    f"{len(group)} tentatives de connexion échouées "
                    f"pour l'utilisateur {username}"
                ),
                "failed_attempts": len(group),
                "unique_ports": group["port"].nunique(),
                "unique_destinations": group["destination_ip"].nunique(),
                "first_seen": group["timestamp"].min(),
                "last_seen": group["timestamp"].max(),
                "risk_score": 80
            })

    return alerts


# ============================================================
# 2. PORT SCAN
# ============================================================

def detect_port_scan(df):

    connections = df[
        df["event_type"] == "CONNECTION"
    ].copy()

    connections = connections.sort_values("timestamp")

    alerts = []

    for (source_ip, destination_ip), group in connections.groupby(
        ["source_ip", "destination_ip"]
    ):

        unique_ports = group["port"].nunique()
        total_attempts = len(group)

        if unique_ports >= 10:

            alerts.append({
                "alert_type": "PORT_SCAN",
                "severity": "MEDIUM",
                "source_ip": source_ip,
                "destination_ip": destination_ip,
                "username": None,
                "description": (
                    f"Scan détecté depuis {source_ip} vers "
                    f"{destination_ip} sur {unique_ports} ports"
                ),
                "failed_attempts": None,
                "unique_ports": unique_ports,
                "unique_destinations": 1,
                "first_seen": group["timestamp"].min(),
                "last_seen": group["timestamp"].max(),
                "risk_score": 60
            })

    return alerts


# ============================================================
# 3. CONNEXION INHABITUELLE
# ============================================================

def detect_unusual_login(df):

    logins = df[
        (df["event_type"] == "LOGIN") &
        (df["status"] == "SUCCESS")
    ].copy()

    logins["hour"] = logins["timestamp"].dt.hour

    unusual_logins = logins[
        (logins["hour"] >= 0) &
        (logins["hour"] < 5)
    ]

    alerts = []

    for _, row in unusual_logins.iterrows():

        alerts.append({
            "alert_type": "UNUSUAL_LOGIN",
            "severity": "MEDIUM",
            "source_ip": row["source_ip"],
            "destination_ip": row["destination_ip"],
            "username": row["username"],
            "description": (
                f"Connexion réussie à {row['timestamp'].strftime('%H:%M:%S')}"
            ),
            "failed_attempts": None,
            "unique_ports": 1,
            "unique_destinations": 1,
            "first_seen": row["timestamp"],
            "last_seen": row["timestamp"],
            "risk_score": 50
        })

    return alerts


# ============================================================
# 4. ACTIVITE SUSPECTE
# ============================================================

def detect_suspicious_activity(df):

    connections = df[
        df["status"] == "FAILED"
    ].copy()

    connections = connections.sort_values("timestamp")

    alerts = []

    for source_ip, group in connections.groupby("source_ip"):

        failed_attempts = len(group)
        unique_destinations = group["destination_ip"].nunique()
        unique_ports = group["port"].nunique()

        if (
            failed_attempts >= 20
            and (
                unique_destinations >= 3
                or unique_ports >= 5
            )
        ):

            alerts.append({
                "alert_type": "SUSPICIOUS_ACTIVITY",
                "severity": "HIGH",
                "source_ip": source_ip,
                "destination_ip": None,
                "username": None,
                "description": (
                    f"Activité suspecte : {failed_attempts} échecs, "
                    f"{unique_destinations} destinations et "
                    f"{unique_ports} ports"
                ),
                "failed_attempts": failed_attempts,
                "unique_ports": unique_ports,
                "unique_destinations": unique_destinations,
                "first_seen": group["timestamp"].min(),
                "last_seen": group["timestamp"].max(),
                "risk_score": 75
            })

    return alerts


# ============================================================
# INSERTION DES ALERTES DANS POSTGRESQL
# ============================================================

def save_alerts(alerts):

    if not alerts:
        print("Aucune alerte à enregistrer.")
        return

    conn = psycopg2.connect(**DB_CONFIG)

    cur = conn.cursor()

    query = """
        INSERT INTO public.alerts (
            alert_type,
            severity,
            source_ip,
            destination_ip,
            username,
            description,
            failed_attempts,
            unique_ports,
            unique_destinations,
            first_seen,
            last_seen,
            risk_score
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """

    for alert in alerts:

        cur.execute(
            query,
            (
                alert["alert_type"],
                alert["severity"],
                alert["source_ip"],
                alert["destination_ip"],
                alert["username"],
                alert["description"],
                alert["failed_attempts"],
                alert["unique_ports"],
                alert["unique_destinations"],
                alert["first_seen"],
                alert["last_seen"],
                alert["risk_score"]
            )
        )

    conn.commit()

    cur.close()
    conn.close()

    print(f"{len(alerts)} alertes enregistrées dans PostgreSQL.")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AI SOC - THREAT DETECTION ENGINE")
    print("=" * 60)

    logs = get_logs()

    print(f"\nLogs analysés : {len(logs)}")

    # Détection
    brute_force_alerts = detect_brute_force(logs)

    port_scan_alerts = detect_port_scan(logs)

    unusual_login_alerts = detect_unusual_login(logs)

    suspicious_activity_alerts = detect_suspicious_activity(logs)

    # Regroupement
    all_alerts = (
        brute_force_alerts
        + port_scan_alerts
        + unusual_login_alerts
        + suspicious_activity_alerts
    )

    print(f"\nTotal des alertes détectées : {len(all_alerts)}")

    # Sauvegarde PostgreSQL
    save_alerts(all_alerts)
