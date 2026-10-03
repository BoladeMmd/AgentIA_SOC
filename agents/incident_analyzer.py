import os
import psycopg2
from dotenv import load_dotenv
from groq import Groq


# =========================
# CHARGEMENT DES VARIABLES
# =========================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY introuvable dans le fichier .env")


# =========================
# CONFIGURATION
# =========================

MODEL = "openai/gpt-oss-20b"

DB_CONFIG = {
    "dbname": "ai_soc",
    "user": "postgres",
    "password": "****",
    "host": "localhost",
    "port": "5432"
}


# =========================
# CLIENT GROQ
# =========================

client = Groq(
    api_key=GROQ_API_KEY
)


# =========================
# RÉCUPÉRER LA DERNIÈRE ALERTE
# =========================

def get_latest_alert():

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        SELECT
            alert_id,
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
        FROM public.alerts
        ORDER BY detected_at DESC
        LIMIT 1;
    """

    cur.execute(query)

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row is None:
        return None

    return {
        "alert_id": row[0],
        "alert_type": row[1],
        "severity": row[2],
        "source_ip": row[3],
        "destination_ip": row[4],
        "username": row[5],
        "description": row[6],
        "failed_attempts": row[7],
        "unique_ports": row[8],
        "unique_destinations": row[9],
        "first_seen": row[10],
        "last_seen": row[11],
        "risk_score": row[12]
    }


# =========================
# ANALYSE GROQ
# =========================

def analyze_incident(alert):

    prompt = f"""
Tu es un analyste SOC spécialisé dans la cybersécurité défensive.

Analyse l'alerte suivante :

ID : {alert["alert_id"]}
Type : {alert["alert_type"]}
Sévérité : {alert["severity"]}
IP source : {alert["source_ip"]}
IP destination : {alert["destination_ip"]}
Utilisateur : {alert["username"]}
Description : {alert["description"]}
Tentatives échouées : {alert["failed_attempts"]}
Ports uniques : {alert["unique_ports"]}
Destinations uniques : {alert["unique_destinations"]}
Première détection : {alert["first_seen"]}
Dernière détection : {alert["last_seen"]}
Score de risque : {alert["risk_score"]}

Réponds exactement sous cette forme :

RESUME:
...

COMPORTEMENT:
...

RISQUE:
...

INDICATEURS:
...

RECOMMANDATIONS:
- Présente chaque recommandation sur une ligne différente.
- Commence chaque recommandation par "-".
- Ne regroupe jamais plusieurs recommandations sur la même ligne.
...

Règles :
- RISQUE doit être uniquement FAIBLE, MOYEN ou ÉLEVÉ.
- Reste factuel.
- Ne réalise aucune action automatiquement.
- Présente les mesures de réponse comme des recommandations à valider par l'analyste SOC.
- Ne propose aucune action offensive ou destructive.
- Pour toute mesure de blocage, de désactivation ou de modification de configuration,
  indique qu'elle doit être validée par l'analyste SOC avant exécution.
- N'invente aucune information absente de l'alerte.
- Toute la réponse doit être rédigée en français.
- Les recommandations doivent être rédigées en français.
- Ne réponds jamais en anglais.
"""


    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
                Tu es un analyste SOC spécialisé dans la cybersécurité défensive.

                IMPORTANT :
                - Tu dois répondre UNIQUEMENT en français.
                - Toutes les sections doivent être rédigées en français.
                - N'utilise jamais l'anglais, même pour les recommandations.
                - Conserve uniquement les termes techniques qui sont habituellement utilisés tels quels en cybersécurité, comme IP, MFA, firewall, SOC, SIEM ou phishing.
                - Les explications et les phrases doivent obligatoirement être en français.
                """
            },

            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=1000
    )

    analysis_text = response.choices[0].message.content

    return parse_analysis(analysis_text)

###############################
def parse_analysis(text):

    sections = {
        "summary": "",
        "behavior_analysis": "",
        "risk_level": "",
        "indicators": "",
        "recommendations": ""
    }

    current_section = None

    for line in text.splitlines():

        line = line.strip()

        if line.startswith("RESUME:"):
            current_section = "summary"
            sections["summary"] = line.replace("RESUME:", "").strip()

        elif line.startswith("COMPORTEMENT:"):
            current_section = "behavior_analysis"
            sections["behavior_analysis"] = line.replace(
                "COMPORTEMENT:", ""
            ).strip()

        elif line.startswith("RISQUE:"):
            current_section = "risk_level"
            sections["risk_level"] = line.replace(
                "RISQUE:", ""
            ).strip()

        elif line.startswith("INDICATEURS:"):
            current_section = "indicators"
            sections["indicators"] = line.replace(
                "INDICATEURS:", ""
            ).strip()

        elif line.startswith("RECOMMANDATIONS:"):
            current_section = "recommendations"
            sections["recommendations"] = line.replace(
                "RECOMMANDATIONS:", ""
            ).strip()

        elif current_section and line:

            sections[current_section] += " " + line

    return sections


# =========================
# SAUVEGARDER L'ANALYSE
# =========================

def save_analysis(alert_id, analysis):

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        INSERT INTO public.incident_analysis (
            alert_id,
            summary,
            behavior_analysis,
            risk_level,
            indicators,
            recommendations
        )
        VALUES (%s, %s, %s, %s, %s, %s)

        ON CONFLICT (alert_id)
        DO UPDATE SET
            summary = EXCLUDED.summary,
            behavior_analysis = EXCLUDED.behavior_analysis,
            risk_level = EXCLUDED.risk_level,
            indicators = EXCLUDED.indicators,
            recommendations = EXCLUDED.recommendations,
            created_at = CURRENT_TIMESTAMP;
    """

    cur.execute(
        query,
        (
            alert_id,
            analysis["summary"],
            analysis["behavior_analysis"],
            analysis["risk_level"],
            analysis["indicators"],
            analysis["recommendations"]
        )
    )

    conn.commit()

    cur.close()
    conn.close()

    print("\nAnalyse enregistrée dans PostgreSQL.")

# =========================
# PROGRAMME PRINCIPAL
# =========================

if __name__ == "__main__":

    print("\n================================")
    print("     AI SOC INCIDENT ANALYZER")
    print("================================")

    print("\nRecherche de la dernière alerte...")

    alert = get_latest_alert()

    if alert is None:

        print("Aucune alerte trouvée.")

    else:

        print("\nAlerte récupérée")
        print("-------------------------------")
        print(f"ID         : {alert['alert_id']}")
        print(f"Type       : {alert['alert_type']}")
        print(f"Sévérité   : {alert['severity']}")
        print(f"IP source  : {alert['source_ip']}")
        print(f"IP cible   : {alert['destination_ip']}")
        print(f"Risque     : {alert['risk_score']}")
        print("-------------------------------")

        print("\nAnalyse avec Groq en cours...\n")

        analysis = analyze_incident(alert)

        print("\n================================")
        print("        ANALYSE IA")
        print("================================")

        print("\nRésumé :")
        print(analysis["summary"])

        print("\nComportement :")
        print(analysis["behavior_analysis"])

        print("\nRisque :")
        print(analysis["risk_level"])

        print("\nIndicateurs :")
        print(analysis["indicators"])

        print("\nRecommandations :")
        print(analysis["recommendations"])

        save_analysis(
            alert["alert_id"],
            analysis
        )
