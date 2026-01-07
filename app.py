import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE: VERDE CHIARO PROFESSIONALE
def apply_custom_style():
    st.markdown(
        """
        <style>
        .stApp { background-color: #e8f5e9; }
        [data-testid="stSidebar"] { background-color: #c8e6c9 !important; }
        h1, h2, h3, h4, h5, p, label, span { color: #1b5e20 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        h1 { text-align: center; font-weight: 800; padding-bottom: 20px; color: #2e7d32 !important; }
        .stTabs, .stDataFrame, .stTable {
            background-color: #ffffff !important;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        /* Sidebar compatta */
        section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_custom_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET FISSI (DA FEBBRAIO)
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. SIDEBAR: CARICAMENTO FILE (Layout compatto)
st.sidebar.header("📂 Database Lega")
f_scontri = st.sidebar.file_uploader("Classifica Scontri", type="csv")
f_punti = st.sidebar.file_uploader("Classifica Punti", type="csv")
f_rose = st.sidebar.file_uploader("Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("Vincoli 2026/27", type="csv")

# --- FUNZIONI DI SUPPORTO ---
def pulisci_nomi(df, col):
    if df is None or col not in df.columns: return df
    mappa = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[col] = df[col].astype(str).str.strip().str.upper().replace(mappa)
    return df

def carica_csv(file):
    if file is None: return None
    try:
        file.seek(0)
        df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

# Caricamento
df_scontri = carica_csv(f_scontri)
df_punti_tot = carica_csv(f_punti)
df_rose = carica_csv(f_rose)
df_vincoli = carica_csv(f_vinc)

# 5. VISUALIZZAZIONE MODULARE (L'app non si blocca se manca un file)
if any([df_scontri is not None, df_punti_tot is not None, df_rose is not None, df_vincoli is not None]):
    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # --- TAB CLASSIFICHE ---
    with tabs[0]:
        cl1, cl2 = st.columns(2)
        with cl1:
            st.subheader("🔥 Scontri Diretti")
            if df_scontri is not None:
                df_scontri = pulisci_nomi(df_scontri, 'Giocatore')
                st.dataframe(df_scontri, hide_index=True, use_container_width=True,
                             column_config={"Posizione": st.column_config.Column(width="small")})
            else: st.info("Carica 'scontridiretti.csv'")
        
        with cl2:
            st.subheader("🎯 Punti Totali")
            if df_punti_tot is not None:
                df_punti_tot = pulisci_nomi(df_punti_tot, 'Giocatore')
                for c in ['Punti Totali', 'Media', 'Distacco']:
                    if c in df_punti_tot.columns:
                        df_punti_tot[c] = df_punti_tot[c].astype(str).str.replace(',', '.').astype(float)
                st.dataframe(df_punti_tot[['Posizione', 'Giocatore', 'Punti Totali', 'Media']], 
                             hide_index=True, use_container_width=True,
                             column_config={"Posizione": st.column_config.Column(width="small")})
            else: st.info("Carica 'classificapunti.csv'")

    # --- TAB ECONOMIA ---
    with tabs[1]:
        st.subheader("💰 Bilancio Rose")
        if df_rose is not None:
            # R
