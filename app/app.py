import os
import sys
import re

# ============================================================
# AJOUTER LA RACINE DU PROJET AU CHEMIN PYTHON
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, PROJECT_ROOT)


import streamlit as st
import psycopg2
import pandas as pd

from agents.incident_analyzer import (
    analyze_incident,
    save_analysis
)


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI SOC Dashboard",
    page_icon="🛡️",
    layout="wide"
)


DB_CONFIG = {
    "dbname": "ai_soc",
    "user": "postgres",
    "password": "passer",
    "host": "localhost",
    "port": "5432"
}


# ============================================================
# CONNEXION POSTGRESQL
# ============================================================

@st.cache_resource
def get_connection():

    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# RÉCUPÉRATION DES ALERTES
# ============================================================

@st.cache_data(ttl=10)
def get_alerts():

    conn = get_connection()

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
            risk_score,
            status,
            detected_at
        FROM public.alerts
        ORDER BY detected_at DESC;
    """

    df = pd.read_sql(query, conn)

    return df


# ============================================================
# RÉCUPÉRATION DE TOUTES LES ANALYSES
# ============================================================

@st.cache_data(ttl=10)
def get_analyses():

    conn = get_connection()

    query = """
        SELECT
            analysis_id,
            alert_id,
            summary,
            behavior_analysis,
            risk_level,
            indicators,
            recommendations,
            created_at
        FROM public.incident_analysis
        ORDER BY created_at DESC;
    """

    df = pd.read_sql(query, conn)

    return df


# ============================================================
# RÉCUPÉRATION DE L'ANALYSE D'UNE ALERTE
# ============================================================

@st.cache_data(ttl=5)
def get_analysis_for_alert(alert_id):

    conn = get_connection()

    query = """
        SELECT
            analysis_id,
            alert_id,
            summary,
            behavior_analysis,
            risk_level,
            indicators,
            recommendations,
            created_at
        FROM public.incident_analysis
        WHERE alert_id = %s
        ORDER BY created_at DESC
        LIMIT 1;
    """

    df = pd.read_sql(
        query,
        conn,
        params=(alert_id,)
    )

    return df


# ============================================================
# TITRE
# ============================================================

st.title("🛡️ AI SOC Dashboard")

st.caption(
    "Plateforme de surveillance et d'analyse intelligente "
    "des incidents de cybersécurité"
)


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

try:

    alerts = get_alerts()

except Exception as e:

    st.error(
        "Impossible de se connecter à PostgreSQL."
    )

    st.exception(e)

    st.stop()


# ============================================================
# STATISTIQUES
# ============================================================

total_alerts = len(alerts)

high_alerts = len(
    alerts[alerts["severity"] == "HIGH"]
)

medium_alerts = len(
    alerts[alerts["severity"] == "MEDIUM"]
)

low_alerts = len(
    alerts[alerts["severity"] == "LOW"]
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "🚨 Alertes",
        total_alerts
    )


with col2:

    st.metric(
        "🔴 HIGH",
        high_alerts
    )


with col3:

    st.metric(
        "🟠 MEDIUM",
        medium_alerts
    )


with col4:

    st.metric(
        "🟢 LOW",
        low_alerts
    )


st.divider()


# ============================================================
# ALERTES RÉCENTES
# ============================================================

st.divider()
st.subheader("🚨 Alertes récentes")

if alerts.empty:

    st.info("Aucune alerte disponible.")

else:

    # =========================
    # FILTRES
    # =========================

    st.markdown("### 🔎 Filtrer les alertes")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        severity_filter = st.selectbox(
            "Sévérité",
            ["Toutes"] + sorted(
                alerts["severity"].dropna().unique().tolist()
            )
        )

    with col2:
        type_filter = st.selectbox(
            "Type d'alerte",
            ["Tous"] + sorted(
                alerts["alert_type"].dropna().unique().tolist()
            )
        )

    with col3:
        status_filter = st.selectbox(
            "Statut",
            ["Tous"] + sorted(
                alerts["status"].dropna().unique().tolist()
            )
        )

    with col4:
        source_filter = st.selectbox(
            "IP source",
            ["Toutes"] + sorted(
                alerts["source_ip"].dropna().unique().tolist()
            )
        )

    # =========================
    # APPLICATION DES FILTRES
    # =========================

    filtered_alerts = alerts.copy()

    if severity_filter != "Toutes":
        filtered_alerts = filtered_alerts[
            filtered_alerts["severity"] == severity_filter
        ]

    if type_filter != "Tous":
        filtered_alerts = filtered_alerts[
            filtered_alerts["alert_type"] == type_filter
        ]

    if status_filter != "Tous":
        filtered_alerts = filtered_alerts[
            filtered_alerts["status"] == status_filter
        ]

    if source_filter != "Toutes":
        filtered_alerts = filtered_alerts[
            filtered_alerts["source_ip"] == source_filter
        ]

    st.write(
        f"**{len(filtered_alerts)} alerte(s) affichée(s)**"
    )

    # =========================
    # TABLEAU
    # =========================

    display_alerts = filtered_alerts[
        [
            "alert_id",
            "alert_type",
            "severity",
            "source_ip",
            "destination_ip",
            "username",
            "risk_score",
            "status",
            "detected_at"
        ]
    ].copy()

    # Affichage propre des destinations multiples
    display_alerts["destination_ip"] = display_alerts[
        "destination_ip"
    ].fillna("Plusieurs destinations")

    st.dataframe(
        display_alerts,
        use_container_width=True,
        hide_index=True
    )




# ============================================================
# SÉLECTION D'UNE ALERTE
# ============================================================

st.divider()

st.subheader("🔎 Analyse d'une alerte")


if not alerts.empty:

    alert_ids = alerts[
        "alert_id"
    ].tolist()


    selected_alert_id = st.selectbox(
        "Sélectionner une alerte",
        alert_ids
    )


    selected_alert = alerts[
        alerts["alert_id"] == selected_alert_id
    ].iloc[0]


    # ========================================================
    # INFORMATIONS SUR L'ALERTE
    # ========================================================

    st.markdown(
        "### Informations sur l'incident"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.write("**Type**")

        st.write(
            selected_alert["alert_type"]
        )


        st.write("**Sévérité**")

        st.write(
            selected_alert["severity"]
        )


        st.write("**Score de risque**")

        st.write(
            selected_alert["risk_score"]
        )


    with col2:

        st.write("**IP source**")

        st.write(
            selected_alert["source_ip"]
        )


        st.write("**IP destination**")

        st.write(
            selected_alert["destination_ip"]
        )


        st.write("**Utilisateur**")

        st.write(
            selected_alert["username"]
        )


    with col3:

        st.write("**Tentatives échouées**")

        st.write(
            selected_alert["failed_attempts"]
        )


        st.write("**Ports uniques**")

        st.write(
            selected_alert["unique_ports"]
        )


        st.write("**Destinations uniques**")

        st.write(
            selected_alert["unique_destinations"]
        )


    st.write("**Description**")


    st.info(
        selected_alert["description"]
    )


    # ========================================================
    # RÉCUPÉRER L'ANALYSE DE L'ALERTE
    # ========================================================

    selected_analysis = get_analysis_for_alert(
        selected_alert_id
    )


    # ========================================================
    # ANALYSE EXISTANTE
    # ========================================================

    if not selected_analysis.empty:

        analysis = selected_analysis.iloc[0]


        st.success(
            "✅ Une analyse IA est disponible pour cette alerte."
        )


        # ====================================================
        # RÉSUMÉ
        # ====================================================

        st.markdown(
            "### 📌 Résumé"
        )

        st.write(
            analysis["summary"]
        )


        # ====================================================
        # COMPORTEMENT
        # ====================================================

        st.markdown(
            "### 🔎 Comportement"
        )

        st.write(
            analysis["behavior_analysis"]
        )


        # ====================================================
        # RISQUE
        # ====================================================

        st.markdown(
            "### ⚠️ Niveau de risque"
        )


        risk = str(
            analysis["risk_level"]
        ).strip().upper()


        if risk == "HIGH":

            st.error(
                f"🔴 {risk}"
            )

        elif risk == "MEDIUM":

            st.warning(
                f"🟠 {risk}"
            )

        else:

            st.success(
                f"🟢 {risk}"
            )


        # ====================================================
        # INDICATEURS
        # ====================================================

        st.markdown(
            "### 🎯 Indicateurs"
        )

        st.write(
            analysis["indicators"]
        )


        # ====================================================
        # RECOMMANDATIONS
        # ====================================================

        st.markdown(
            "### 🛡️ Recommandations"
        )


        recommendations = str(
            analysis["recommendations"]
        ).strip()


        # ----------------------------------------------------
        # NETTOYAGE MARKDOWN
        # ----------------------------------------------------

        recommendations = recommendations.replace(
            "**",
            ""
        )


        # ----------------------------------------------------
        # CAS :
        #
        # recommandation 1 - recommandation 2 - recommandation 3
        # ----------------------------------------------------

        recommendations = re.sub(
            r"\s+-\s+",
            "\n",
            recommendations
        )


        # ----------------------------------------------------
        # CAS :
        #
        # 1. recommandation 2. recommandation 3. recommandation
        # ----------------------------------------------------

        recommendations = re.sub(
            r"\s+(?=\d+\.\s+)",
            "\n",
            recommendations
        )


        # ----------------------------------------------------
        # AFFICHAGE
        # ----------------------------------------------------

        for recommendation in recommendations.splitlines():

            recommendation = recommendation.strip()


            if not recommendation:

                continue


            # Supprimer "-" au début

            recommendation = re.sub(
                r"^-\s*",
                "",
                recommendation
            )


            # Supprimer "1.", "2.", etc.

            recommendation = re.sub(
                r"^\d+\.\s*",
                "",
                recommendation
            )


            st.markdown(
                f"- {recommendation}"
            )


    # ========================================================
    # AUCUNE ANALYSE
    # ========================================================

    else:

        st.warning(
            "⚠️ Aucune analyse IA n'est encore disponible "
            "pour cette alerte."
        )


        st.markdown(
            "Vous pouvez demander à l'agent IA d'analyser "
            "cet incident."
        )


        # ====================================================
        # BOUTON GROQ
        # ====================================================

        if st.button(
            "🤖 Analyser cette alerte avec l'IA",
            type="primary"
        ):

            with st.spinner(
                "Analyse de l'incident avec Groq en cours..."
            ):

                try:

                    # ----------------------------------------
                    # ANALYSE GROQ
                    # ----------------------------------------

                    analysis = analyze_incident(
                        selected_alert.to_dict()
                    )


                    # ----------------------------------------
                    # SAUVEGARDE POSTGRESQL
                    # ----------------------------------------

                    save_analysis(
                        selected_alert_id,
                        analysis
                    )


                    st.success(
                        "✅ Analyse terminée et enregistrée "
                        "dans PostgreSQL."
                    )


                    # ----------------------------------------
                    # VIDER LE CACHE
                    # ----------------------------------------

                    get_analysis_for_alert.clear()


                    # ----------------------------------------
                    # RAFRAÎCHIR STREAMLIT
                    # ----------------------------------------

                    st.rerun()


                except Exception as e:

                    st.error(
                        "❌ Erreur pendant l'analyse IA."
                    )

                    st.exception(e)


else:

    st.info(
        "Aucune alerte à analyser."
    )