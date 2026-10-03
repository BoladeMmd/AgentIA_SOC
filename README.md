## 🛡️ AI SOC Agent

**AI SOC Agent** est un prototype d'agent intelligent dédié à la détection, la qualification et l'analyse d'incidents de cybersécurité.

Le projet combine Data Engineering, détection basée sur des règles et Intelligence Artificielle générative afin de construire une chaîne complète allant de la collecte des logs jusqu'à l'analyse des incidents dans une interface Streamlit.

**🎓 Projet personnel** réalisé dans une démarche d'apprentissage et d'expérimentation autour de la Data Engineering, de l'IA et de la cybersécurité.

## 🎯 Objectif du projet

L'objectif est de concevoir un système capable de :

- générer et exploiter des logs de sécurité ;
- centraliser les événements dans une base PostgreSQL ;
- détecter automatiquement certains comportements suspects ;
- générer des alertes avec un niveau de risque ;
- transmettre les alertes à un modèle d'IA pour faciliter leur analyse ;
- enregistrer les analyses produites ;
- présenter les incidents dans un dashboard interactif.

Le projet cherche principalement à explorer comment **l'IA générative** peut assister un **analyste SOC** dans la compréhension et la qualification d'incidents, sans automatiser d'actions offensives ou destructrices.


## 🏗️ Architecture





## 🔍 Détection des menaces

Le système utilise actuellement plusieurs mécanismes de détection basés sur des règles.

**🔴 Brute Force**

Détection d'un nombre important de tentatives de connexion échouées provenant d'une même adresse IP et visant un même utilisateur.

**🟠 Port Scan**

Détection d'une source qui tente de communiquer avec un grand nombre de ports différents.

**🟠 Unusual Login**

Identification de connexions réussies effectuées pendant des horaires considérés comme inhabituels.

**🔴 Suspicious Activity**

Détection d'une concentration importante de tentatives échouées provenant d'une même source et concernant plusieurs destinations ou ports.

**🤖 Analyse des incidents avec l'IA**

Après détection, les alertes peuvent être analysées par un modèle de langage via la Groq API.
L'agent reçoit les informations disponibles sur l'alerte et produit une analyse structurée en français.

**Analyse générée**

RESUME ---> COMPORTEMENT ---> RISQUE ---> INDICATEURS ---> RECOMMANDATIONS    


L'analyse permet notamment de fournir :

- un résumé de l'incident ;
- une description du comportement observé ;
- un niveau de risque ;
- les principaux indicateurs ;
- des recommandations de réponse.

Les **recommandations** sont présentées comme des mesures à valider par **l'analyste SOC** avant toute exécution.

## 🗄️ Base de données

Le projet utilise **PostgreSQL** pour centraliser les données.

***security_logs**
Contient les événements de sécurité :

event_id,

timestamp,

source_ip,

destination_ip,

username,

event_type,

status,

port,

scenario.

***alerts**
Contient les alertes générées par le moteur de détection :

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

detected_at.

***incident_analysis**
Contient les analyses générées par l'IA :

analysis_id,

alert_id,

summary,

behavior_analysis,

risk_level,

indicators,

recommendations,

created_at.

Une relation est établie entre les **alertes** et leurs **analyses** grâce à **alert_id.**
Les données ont été générées de façon synthetiques et controlés.


## 🖥️ Dashboard Streamlit

Le projet dispose d'une interface web développée avec Streamlit.

Le dashboard permet de :

- consulter les alertes récentes ;
- filtrer les alertes par sévérité ;
- filtrer par type d'alerte ;
- filtrer par statut ;
- rechercher une IP source ;
- consulter les détails d'un incident ;
- consulter l'analyse produite par l'IA ;
- demander une nouvelle analyse IA lorsqu'elle n'existe pas encore.



## Exemple de workflow

<img width="285" height="284" alt="agent5" src="https://github.com/user-attachments/assets/854b66a3-a8c1-4f6c-bb48-7c5b41ec880f" />

       
## 🛠️ Technologies utilisées
 - **Python**

 - **Pandas**

 - **PostgreSQL**

 - **SQL**

 - **psycopg2**

 - **Groq API**

 - **LLM openai/gpt-oss-20b**

 - **Streamlit**


## 📁 Structure du projet

<img width="299" height="350" alt="structureAgentIA" src="https://github.com/user-attachments/assets/d2468356-03e3-46ce-9c1f-4c1ab2f2ae52" />




## ⚙️ Installation

**1. Cloner le dépôt**
```bash
git clone https://github.com/VOTRE_USERNAME/ai-soc-agent.git
```  
```bash
cd ai-soc-agent
```

**2. Créer l'environnement Python**
Avec Conda :
```bash
conda create -n ai_soc python=3.11
```
```bash
conda activate ai_soc
```

**3. Installer les dépendances**
```bash
pip install -r requirements.txt
```



## 🗄️ Configuration PostgreSQL

Créer une base de données :

**CREATE DATABASE ai_soc;**

Puis créer les tables nécessaires au projet :

- **security_logs**
- **alerts**
- **incident_analysis**

Les informations de connexion PostgreSQL doivent être adaptées à votre environnement local.

## ▶️ Utilisation

**Générer les logs**

python utils/log_generator.py

**Charger les logs dans PostgreSQL**

python database/load_logs.py

**Lancer la détection des menaces**

python agents/threat_detector.py

**Lancer le dashboard**

streamlit run app/app.py

Le dashboard sera ensuite accessible depuis votre navigateur.


## 🔄 Pipeline complet

Une exécution typique du projet suit ce processus :


<img width="251" height="278" alt="exempleagentia" src="https://github.com/user-attachments/assets/e417e56d-b56b-4c67-9ae8-4d3c221d25eb" />



## 📊 Exemple de scénarios détectés

Le générateur de données permet de simuler différents comportements :

**BRUTE_FORCE**
**PORT_SCAN**
**UNUSUAL_LOGIN**
**SUSPICIOUS_ACTIVITY**

Ces scénarios permettent de tester le pipeline de détection sans utiliser de données de sécurité réelles.


Les recommandations générées par l'IA doivent être analysées et validées par un professionnel de la sécurité avant toute mise en œuvre.


## 🚀 Perspectives d'amélioration

Plusieurs évolutions sont envisageables :

- ingestion de logs en temps réel ;
- connexion à des sources de logs réelles ;
- intégration avec Kafka ;
- ajout d'un SIEM ;
- détection basée sur le Machine Learning ;
- amélioration du scoring des risques.




## 👤 Auteur

**Boladé MAMADOU**

**Ingénieur de données et intelligence artificielle.**

**Mail**: bolademamadou7@gmail.com

**Linkedin**: https://www.linkedin.com/in/bolad%C3%A9-mamadou-a1a91833a/?isSelfProfile=true















