import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE: VERDE CHIARO E PULITO
def apply_custom_style():
    st.markdown(
        """
        <style>
        .stApp { background-color: #e8f5e9; }
        [data-testid="stSidebar"] { background-color: #c8e6c9 !important; }
        h1, h2, h3, h4, h5, p, label, span { color: #1b5e20 !important; }
        h1 { text-align: center; font-weight: 800; padding-bottom: 20px; }
        .stTabs, .stDataFrame, .stTable {
            background-color: #ffffff !important;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_custom_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET FISSI (COSTANTI)
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. SIDEBAR PER CARICAMENTO
st.sidebar.header("📂 Caricamento Database")
f_scontri = st.sidebar.file_uploader("1. Classifica Scontri (scontridiretti.csv)", type="csv")
f_punti = st.sidebar.file_uploader("2. Classifica Punti (classificapunti.csv)", type="csv")
f_rose = st.sidebar.file_uploader("3. Rose Attuali (file rose)", type="csv")
f_vinc = st.sidebar.file_uploader("4. Vincoli 2026/27 (file vincoli)", type="csv")

# Funzioni di pulizia e mapping nomi
def pulisci_nomi(df, col):
    mappa = {
        "NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", 
        "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"
    }
    df[col] = df[col].astype(str).str.strip().str.upper().replace(mappa)
    return df

def carica_csv(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    return df

# Caricamento effettivo
df_scontri = carica_csv(f_scontri)
df_punti_tot = carica_csv(f_punti)
df_rose = carica_csv(f_rose)
df_vincoli = carica_csv(f_vinc)

# 5. LOGICA APPLICAZIONE
if df_rose is not None:
    # Identificazione colonne rose (flessibile)
    cols_map = {c.lower(): c for c in df_rose.columns}
    f_col = cols_map.get('fantasquadra', df_rose.columns[0])
    n_col = cols_map.get('nome', df_rose.columns[1])
    p_col = cols_map.get('prezzo', df_rose.columns[2])
    r_col = cols_map.get('ruolo', 'Ruolo')

    # Pulizia Rose
    df_rose = df_rose.dropna(subset=[f_col, n_col])
    df_rose = pulisci_nomi(df_rose, f_col)
    df_rose['Prezzo_Int'] = pd.to_numeric(df_rose[p_col], errors='coerce').fillna(0).astype(int)

    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # --- TAB CLASSIFICHE ---
    with tabs[0]:
        cl1, cl2 = st.columns(2)
        with cl1:
            st.subheader("🔥 Scontri Diretti")
            if df_scontri is not None:
                df_scontri = pulisci_nomi(df_scontri, 'Giocatore')
                cols_s = ['Posizione', 'Giocatore', 'Punti', 'Gol Fatti', 'Gol Subiti', 'Differenza Reti']
                st.dataframe(df_scontri[cols_s].sort_values('Punti', ascending=False), hide_index=True, use_container_width=True)
            else: st.info("In attesa di scontridiretti.csv")
        with cl2:
            st.subheader("🎯 Punti Totali")
            if df_punti_tot is not None:
                df_punti_tot = pulisci_nomi(df_punti_tot, 'Giocatore')
                # Gestione virgola decimale nei punteggi
                for col_p in ['Punti Totali', 'Media', 'Distacco']:
                    if col_p in df_punti_tot.columns:
                        df_punti_tot[col_p] = df_punti_tot[col_p].astype(str).str.replace(',', '.').astype(float)
                st.dataframe(df_punti_tot[['Posizione', 'Giocatore', 'Punti Totali', 'Media']], hide_index=True, use_container_width=True)

    # --- TAB ECONOMIA ---
    with tabs[1]:
        st.subheader("💰 Bilancio Rose")
        eco = df_rose.groupby(f_col)['Prezzo_Int'].sum().reset_index()
        eco.columns = ['Fantasquadra', 'Costo della Rosa']
        eco['Extra Febbraio'] = eco['Fantasquadra'].map(budgets_fisso).fillna(0)
        eco['Budget Totale'] = (eco['Costo della Rosa'] + eco['Extra Febbraio']).astype(int)
