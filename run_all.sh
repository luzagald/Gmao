#!/bin/bash
echo "Mini-GMAO - Démarrage TURBO"

# Ports publics (plus jamais 401)
gh codespace ports visibility 8000:public -c $CODESPACE_NAME 2>/dev/null || true
gh codespace ports visibility 8501:public -c $CODESPACE_NAME 2>/dev/null || true

# Install dépendances
pip install pandas streamlit fastapi uvicorn pyarrow --quiet --no-cache-dir

# Génère le calendrier complet une seule fois (si pas déjà fait)
if [ ! -f "data/schedule_cache.parquet" ]; then
    echo "Première génération du calendrier complet (ça prend ~8 secondes)..."
    mkdir -p data
    python -c "
from maintenance_scheduler import create_complete_maintenance_schedule
import pandas as pd
df = create_complete_maintenance_schedule(start_year=2025, end_year=2030)
df.to_parquet('data/schedule_cache.parquet', compression='gzip')
print(f'Calendrier généré et sauvegardé : {len(df):,} lignes')
    "
else
    echo "Calendrier déjà généré → chargement instantané !"
fi

# Démarrage API + Streamlit
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
sleep 3
streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
#./start.sh