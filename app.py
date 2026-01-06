import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. FUNZIONE PER SFONDO CAMPO DA CALCIO LUMINOSO (ESTATE/GIORNO)
def apply_bright_football_style():
    # Link a un'immagine di un campo da calcio reale, luminoso e sotto il sole
    img_url = "https://images.unsplash.com/photo-1556056504-5c7696c4c28d?q=80&w=2076&auto=format&fit=crop"
    
    st.markdown(
        f"""
        <style>
        /* Sfondo principale a tutto schermo */
        .stApp {{
            background-image: url("{img_url}");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        
        /* Pannelli dati: Bianchi e molto leggibili per staccare dal verde */
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background-color: rgba(255, 255, 255, 0.96) !important;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        /* Testo Nero su tutta l'app (Nero assoluto per contrasto) */
        h1, h2, h3, p, span, label, .stTabs [data-baseweb="tab"] {{
            color: #000000 !important;
            font-weight: 700 !important;
        }}

        /* Sidebar (Menu laterale) bianca solida */
        [data-testid="stSidebar"] {{
            background-color: #ffffff !important;
            border-right: 3px solid #2e7d32;
        }}
        
        /* Testi Sidebar: Neri e grandi */
        [data-testid="stSidebar"] .stMarkdown p, 
        [data-testid="stSidebar"] label {{
            color: #000000 !important;
            font-size: 16px !important;
            font-weight: bold !important;
        }}
        
        /* Forza il colore nero nelle tabelle */
        .stDataFrame td, .stDataFrame th {{
            color: #000000 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_bright_football_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET CORRETTI (Valori con decimali precisi)
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. CARICAMENTO DATI NELLA BARRA LATERALE
st.sidebar.header("📂 Database Lega")
file_rose = st.sidebar.file_uploader("1. Carica Rose Attuali (CSV)", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica File Vincoli (CSV)", type="csv")

# FUNZIONI DI PULIZIA
def carica_rose(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Fantasquadra', 'Nome'])
    df['Fantasquadra'] = df['Fantasquadra'].str.strip().str.upper()
    df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce').fillna(0)
    return df

def carica_vincoli(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    df = df[df['Squadra'].notna()]
    df = df[~df['Squadra'].str.contains(r'\*|`|:', na=False)]
    df['Squadra'] = df['Squadra'].str.strip().str.upper()
    df['Squadra'] = df['Squadra'].replace({"NICHO": "NICHOLAS"})
    for col in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df_rose = carica_rose(file_rose)
df_vincoli = carica_vincoli(file_vincoli)

# 5. VISUALIZZAZIONE NELLE TAB
if df_rose is not None:
    tabs = st.tabs(["📊 Economia", "🏃 Dettaglio Rose", "📅 Vincoli Futuri"])

    with tabs[0]:
        st.subheader("Situazione Finanziaria")
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
        
        st.dataframe(analisi.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])

    with tabs[1]:
        squadre = sorted(df_rose['Fantasquadra'].unique())
        scelta_r = st.selectbox("Seleziona Squadra:", squadre, key="rose_sel")
        rosa_team = df_rose[df_rose['Fantasquadra'] == scelta_r]
        st.dataframe(rosa_team[['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    with tabs[2]:
        if df_vincoli is not None:
            st.subheader("Strategia Pluriennale")
            impegno = df_vin
