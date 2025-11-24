#!/bin/bash
echo "Mini-GMAO - Démarrage en mode autonome (SANS Docker ni PostgreSQL)"

# 1. Installation des dépendances (une seule fois)
echo "Installation des dépendances..."
pip install pandas streamlit fastapi uvicorn sqlmodel psycopg2-binary --quiet

# 2. Vérification que les fichiers CSV sont bien là
if [ ! -f "import/MATRICE.csv" ] || [ ! -f "import/Param.csv" ]; then
    echo "ERREUR : Fichiers CSV manquants dans le dossier import/"
    echo "Assurez-vous que MATRICE.csv et Param.csv sont présents !"
    exit 1
fi

# 3. Lancement de l'API FastAPI (en arrière-plan)
echo "Démarrage de l'API FastAPI..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# 4. Petit délai pour que l'API démarre
sleep 3

# 5. Lancement du dashboard Streamlit
echo "Démarrage du tableau de bord Streamlit..."
echo "Ouvrez votre application ici : http://localhost:8501 (ou l'URL Codespaces)"
streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false

# Si Streamlit s'arrête, on tue l'API aussi
kill $API_PID 2>/dev/null
#./start.sh