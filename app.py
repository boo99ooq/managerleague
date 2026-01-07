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

# 3. BUDGET FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. SIDEBAR PER CARICAMENTO
st.sidebar.header("📂 Caricamento Dati")
f_scontri = st.sidebar.file_uploader("Classifica Scontri", type="csv")
f_punti = st.sidebar.file_uploader("Classifica Punti", type="csv")
f_rose = st.sidebar.file_uploader("Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("Vincoli 2026/27", type="csv")

# --- FUNZIONI DI PULIZIA E MAPPING ---
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
    # Prova a leggere il file con codifica corretta
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    return df

# --- TENTATIVO DI CARICAMENTO ---
df_scontri = carica_csv(f_scontri)
df_punti_tot = carica_csv(f_punti)
df_rose = carica_csv(f_rose)
df_vincoli = carica_csv(f_vinc)

# 5. LOGICA PRINCIPALE
if df_rose is not None:
    # Cerchiamo di capire i nomi delle colonne anche se variano
    cols_mapping = {col.lower(): col for col in df_rose.columns}
    f_col = cols_mapping.get('fantasquadra', df_rose.columns[0])
    n_col = cols_mapping.get('nome', df_rose.columns[1])
    p_col = cols_mapping.get('prezzo', df_rose.columns[2])
    r_col = cols_mapping.get('ruolo', 'Ruolo')

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
                st.dataframe(df_scontri.sort_values('Punti', ascending=False), hide_index=True)
            else: st.info("In attesa di scontridiretti.csv")
        with cl2:
            st.subheader("🎯 Punti Totali")
            if df_punti_tot is not None:
                df_punti_tot = pulisci_nomi(df_punti_tot, 'Giocatore')
                # Fix decimali classifica punti
                if 'Punti Totali' in df_punti_tot.columns:
                    df_punti_tot['Punti Totali'] = df_punti_
