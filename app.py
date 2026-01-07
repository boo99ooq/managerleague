import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE GLASSMORPHISM COMPATTO
def apply_compact_glass_style():
    img_url = "https://images.unsplash.com/photo-1556056504-5c7696c4c28d?q=80&w=2076&auto=format&fit=crop"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{img_url}");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        
        /* Pannelli centrali */
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(12px);
            padding: 15px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        /* RIDUZIONE SPAZIO SIDEBAR */
        [data-testid="stSidebar"] {{
            background: rgba(0, 0, 0, 0.8) !important;
            backdrop-filter: blur(15px);
        }}
        
        /* Riduci altezza dei blocchi file uploader */
        [data-testid="stFileUploader"] {{
            padding-bottom: 0px !important;
            margin-bottom: -15px !important;
        }}
        
        /* Rimpicciolisci i testi delle etichette uploader */
        [data-testid="stFileUploader"] label p {{
            font-size: 14px !important;
            margin-bottom: -10px !important;
        }}

        /* Titolo Principale */
        h1 {{
            color: #ffffff !important;
            text-shadow: 0 0 10px rgba(46, 204, 113, 0.9);
            text-align: center;
            font-size: 2.5rem !important;
        }}
        
        h2, h3, p, span, label, .stTabs [data-baseweb="tab"] {{
            color: #ffffff !important;
        }}
        
        .stDataFrame td, .stDataFrame th {{
            color: #ffffff !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_compact_glass_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. SIDEBAR COMPATTA
st.sidebar.subheader("📂 Carica Database")

# Caricamento file con etichette brevi per risparmiare spazio
f_scontri = st.sidebar.file_uploader("Classifica Scontri", type="csv")
f_punti = st.sidebar.file_uploader("Classifica Punti", type="csv")
f_rose = st.sidebar.file_uploader("Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("Vincoli 26/27", type="csv")

# Funzioni di pulizia e caricamento
def pulisci_nomi(df, col):
    mappa = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[col] = df[col].astype(str).str.strip().str.upper().replace(mappa)
    return df

def carica_csv(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    return df

df_scontri = carica_csv(f_scontri)
df_punti_tot = carica_csv(f_punti)
df_rose = carica_csv(f_rose)
df_vincoli = carica_csv(f_vinc)

# 5. LOGICA VISUALIZZAZIONE
if df_rose is not None:
    df_rose = df_rose.dropna(subset=['Fantasquadra', 'Nome'])
    df_rose = pulisci_nomi(df_rose, 'Fantasquadra')
    df_rose['Prezzo'] = pd.to_numeric(df_rose['Prezzo'], errors='coerce').fillna(0)

    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    with tabs[0]:
        c_cl1, c_cl2 = st.columns(2)
        with c_cl1:
            st.write("**🔥 Scontri Diretti**")
            if df_scontri is not None:
                df_scontri = pulisci_nomi(df_scontri, 'Giocatore')
                st.dataframe(df
