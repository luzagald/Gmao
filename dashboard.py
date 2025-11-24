# ===========================================
# Mini-GMAO - Dashboard Streamlit
# ===========================================
import streamlit as st
import pandas as pd
import requests
import os
from maintenance_scheduler import create_complete_maintenance_schedule

# Backend API runs on localhost:8000 (same container)
API = "http://localhost:8000"

st.set_page_config(page_title="Mini-GMAO", layout="wide")
st.title("🚜 Mini-GMAO - Tableau de bord")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Choisir une page", [
    "🔎 Recherche globale", 
    "📊 Données CSV", 
    "📅 Entretiens programmés",
    "🔔 Alertes", 
    "✅ Actions"
])

# CSV files configuration
csv_files = {
    "MATRICE - Parc d'engins": "import/MATRICE.csv",
    "VIDANGE - Historique vidanges": "import/VIDANGE.csv",
    "SUIVI_CURATIF - Interventions": "import/SUIVI_CURATIF.csv",
    "Param - Paramètres maintenance": "import/Param.csv"
}

# ==================== PAGE: Recherche globale ====================
if page == "🔎 Recherche globale":
    st.header("🔎 Recherche globale par matricule")
    
    search_term = st.text_input("Entrer un matricule (partiel ou complet)")
    
    if search_term:
        results_found = False
        
        for label, file_path in csv_files.items():
            try:
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path, encoding='cp1252', sep=';')
                    
                    # Rechercher dans la colonne matricule si elle existe
                    if 'matricule' in df.columns:
                        df_filtered = df[df['matricule'].astype(str).str.contains(search_term, case=False, na=False)]
                        
                        if len(df_filtered) > 0:
                            results_found = True
                            st.subheader(f"📌 {label}")
                            st.info(f"{len(df_filtered)} résultat(s)")
                            st.dataframe(df_filtered, use_container_width=True, height=300)
                            
                            # Bouton de téléchargement
                            csv_export = df_filtered.to_csv(index=False, sep=';', encoding='cp1252')
                            st.download_button(
                                label=f"💾 Télécharger {label}",
                                data=csv_export,
                                file_name=f"{label.replace(' ', '_')}_resultat.csv",
                                mime="text/csv",
                                key=f"download_{label}"
                            )
            except Exception as e:
                st.warning(f"⚠️ Erreur avec {label}: {e}")
        
        if not results_found:
            st.warning(f"❌ Aucun résultat trouvé pour '{search_term}' dans les fichiers CSV")
    else:
        st.info("💡 Entrez un matricule pour rechercher dans tous les fichiers CSV")

# ==================== PAGE: Données CSV ====================
elif page == "📊 Données CSV":
    st.header("📊 Visualisation des données CSV")
    
    # Sélection du fichier CSV
    selected = st.selectbox("Sélectionner un fichier CSV", list(csv_files.keys()))
    file_path = csv_files[selected]
    
    try:
        # Charger le CSV
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, encoding='cp1252', sep=';')
            
            st.success(f"✅ {len(df)} lignes chargées")
            
            # Filtre par matricule si la colonne existe
            if 'matricule' in df.columns:
                st.subheader("🔍 Recherche par matricule (dans ce fichier)")
                search_term = st.text_input("Entrer un matricule (partiel ou complet)", key="single_search")
                
                if search_term:
                    # Filtrer le dataframe
                    df_filtered = df[df['matricule'].astype(str).str.contains(search_term, case=False, na=False)]
                    st.info(f"📌 {len(df_filtered)} résultat(s) trouvé(s)")
                    st.dataframe(df_filtered, use_container_width=True, height=500)
                else:
                    st.dataframe(df, use_container_width=True, height=500)
            else:
                st.dataframe(df, use_container_width=True, height=500)
            
            # Téléchargement
            csv_export = df.to_csv(index=False, sep=';', encoding='cp1252')
            st.download_button(
                label="💾 Télécharger le tableau",
                data=csv_export,
                file_name=f"{selected.replace(' ', '_')}.csv",
                mime="text/csv"
            )
            
        else:
            st.error(f"❌ Fichier non trouvé: {file_path}")
            
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement: {e}")

# ==================== PAGE : Entretiens programmés (VERSION TURBO PAR ANNÉE) ====================
elif page == "Entretiens programmés":
    st.header("Calendrier des entretiens programmés")

    # Sélection des années (tu peux cocher plusieurs)
    années_dispo = list(range(2025, 2031))
    années_choisies = st.multiselect(
        "Sélectionner les années à afficher",
        années_dispo,
        default=[2026, 2027, 2028],
        help="Cochez les années souhaitées – le calcul se fait à la volée !"
    )

    if not années_choisies:
        st.info("Veuillez sélectionner au moins une année.")
    else:
        with st.spinner(f"Génération du calendrier pour {len(années_choisies)} année(s)..."):
            # On génère uniquement les années demandées
            dfs = []
            for année in années_choisies:
                df_année = create_complete_maintenance_schedule(
                    start_year=année,
                    end_year=année  # ← 1 an à la fois
                )
                dfs.append(df_année)
            schedule_df = pd.concat(dfs, ignore_index=True)

        st.success(f"Calendrier généré : {len(schedule_df):,} entretiens pour {len(années_choisies)} année(s)")

        # Filtres classiques
        col1, col2 = st.columns(2)
        matricule_filter = col1.text_input("Filtrer par matricule")
        type_filter = col2.multiselect("Filtrer par type", options=["C", "N", "CH"], default=["C", "N", "CH"])

        df = schedule_df[schedule_df['type'].isin(type_filter)]
        if matricule_filter:
            df = df[df['matricule'].astype(str).str.contains(matricule_filter, case=False, na=False)]

        # Affichage
        aff = df[['année', 'date', 'matricule', 'engin', 'opération', 'type_nom', 'catégorie']].copy()
        aff['date'] = pd.to_datetime(aff['date']).dt.strftime('%d/%m/%Y')
        aff = aff.sort_values(['année', 'date'])

        st.dataframe(aff, use_container_width=True, hide_index=True)

        # Export
        csv = aff.to_csv(index=False, sep=';')
        st.download_button(
            "Exporter ce calendrier (CSV)",
            data=csv,
            file_name=f"calendrier_entretiens_{'_'.join(map(str, sorted(années_choisies)))}.csv",
            mime="text/csv"
        )

elif page == "Alertes":
    st.header("Alertes de maintenance")

    # Choix de la fenêtre d'alertes
    fenêtre = st.slider("Fenêtre d'alertes (jours dans le futur)", 15, 180, 90)

    with st.spinner("Calcul des alertes en cours..."):
        # On génère seulement l'année en cours + l'année suivante (suffisant pour les alertes)
        today = pd.Timestamp.today()
        année_courante = today.year
        année_suivante = année_courante + 1

        df = create_complete_maintenance_schedule(
            start_year=année_courante,
            end_year=année_suivante
        )
        df['date'] = pd.to_datetime(df['date'])
        today_norm = today.normalize()

        alertes = df[df['date'] >= today_norm].copy()
        alertes['jours'] = (alertes['date'] - today_norm).dt.days
        alertes = alertes[alertes['jours'] <= fenêtre].sort_values('jours')

        

    # Filtres dans la sidebar
    st.sidebar.subheader("Filtres Alertes")
    filtre_matricule = st.sidebar.text_input("Matricule (partiel ou complet)", "")
    max_jours = st.sidebar.slider("Afficher jusqu'à (jours)", 15, 365, 90, step=15)

    # Application des filtres
    if filtre_matricule:
        alertes = alertes[alertes['matricule'].astype(str).str.contains(filtre_matricule, case=False, na=False)]

    alertes = alertes[alertes['jours'] <= max_jours].copy()

    # Ajout de la colonne Urgence avec icônes
    def niveau_urgence(j):
        if j <= 15:
            return "Urgent (≤15j)"
        elif j <= 30:
            return "Proche (≤30j)"
        else:
            return "Planifié (≤90j)"

    alertes['Urgence'] = alertes['jours'].apply(niveau_urgence)

    if alertes.empty:
        st.success("Aucune alerte dans la période sélectionnée ! Tout est sous contrôle.")
    else:
        # Stats rapides
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Urgent (≤15j)", len(alertes[alertes['jours'] <= 15]))
        col2.metric("Proche (≤30j)", len(alertes[alertes['jours'] <= 30]))
        col3.metric("Planifié (≤90j)", len(alertes[alertes['jours'] <= 90]))
        col4.metric("Total alertes", len(alertes))

        # Préparation du tableau d'affichage
        aff = alertes[['Urgence', 'jours', 'matricule', 'engin', 'opération', 'type_nom', 'date', 'catégorie']].copy()
        aff['date'] = aff['date'].dt.strftime('%d/%m/%Y')
        aff = aff.rename(columns={
            'jours': 'Jours restants',
            'matricule': 'Matricule',
            'engin': 'Engin',
            'opération': 'Opération',
            'type_nom': 'Type',
            'date': 'Date prévue',
            'catégorie': 'Catégorie'
        })

        # Couleurs de fond
        def colore_ligne(row):
            if "Urgent" in row['Urgence']:
                return ['background-color: #ffebee'] * len(row)   # rouge clair
            elif "Proche" in row['Urgence']:
                return ['background-color: #fff8e1'] * len(row)   # jaune clair
            else:
                return ['background-color: #e8f5e9'] * len(row)   # vert clair

        # Affichage final
        st.dataframe(
            aff.style.apply(colore_ligne, axis=1).format({'Jours restants': '{:.0f}'}),
            use_container_width=True,
            hide_index=True
        )

        # Export CSV
        csv_data = aff.copy()
        csv_data['Urgence'] = csv_data['Urgence'].str.replace('Urgent (≤15j)', 'Urgent').str.replace('Proche (≤30j)', 'Proche').str.replace('Planifié (≤90j)', 'Planifié')
        csv = csv_data.to_csv(index=False, sep=';')
        st.download_button(
            label="Exporter ces alertes (CSV)",
            data=csv,
            file_name=f"alertes_maintenance_{today.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    st.info("Alertes générées automatiquement à partir de Param.csv + exclusions par catégorie. Aucune base de données requise !")
# ==================== PAGE: Actions ====================
elif page == "✅ Actions":
    st.header("✅ Actions de maintenance")
    
    action = st.selectbox("Choisir une action", ["Marquer un job fait", "Ajouter un engin"])
    
    if action == "Marquer un job fait":
        job_id = st.number_input("ID du job", min_value=1, step=1)
        if st.button("✅ Marquer comme fait"):
            try:
                resp = requests.put(f"{API}/jobs/{job_id}/done", timeout=5)
                if resp.status_code == 200:
                    st.success(f"Job {job_id} marqué comme fait ! Prochaine échéance recalculée.")
                else:
                    st.error(f"Erreur : {resp.text}")
            except Exception as e:
                st.error(f"Erreur de connexion: {e}")
    
    elif action == "Ajouter un engin":
        with st.form("new_asset"):
            name = st.text_input("Nom de l'engin")
            reg = st.text_input("Immatriculation")
            km = st.number_input("Kilométrage actuel", min_value=0)
            submitted = st.form_submit_button("Ajouter")
            if submitted:
                try:
                    resp = requests.post(f"{API}/assets", json={"name": name, "reg_number": reg, "km": km}, timeout=5)
                    if resp.status_code == 200:
                        st.success("Engin ajouté !")
                    else:
                        st.error(f"Erreur: {resp.text}")
                except Exception as e:
                    st.error(f"Erreur de connexion: {e}")

# ==================== FOOTER ====================
st.sidebar.markdown("---")
st.sidebar.info("""
**Instructions:**
1. Créez une base de données PostgreSQL depuis le panneau Database
2. Lancez le script d'import: `python import_csv.py`
3. Les alertes et actions seront disponibles
""")
