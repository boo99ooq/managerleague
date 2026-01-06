import streamlit as st
import pandas as pd

# 1. FUNZIONE PER LO SFONDO CHIARO E STILE PULITO
def apply_light_football_style():
    st.markdown(
        f"""
        <style>
        /* Immagine di sfondo: Campo verde chiaro e luminoso */
        .stApp {{
            background-image: url("https://images.unsplash.com/photo-1556056504-5c7696c4c28d?q=80&w=2076&auto=format&fit=crop");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        
        /* Pannelli bianchi semi-trasparenti per un effetto pulito */
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background-color: rgba(255, 255, 255, 0.85) !important;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        /* Testi neri per massima leggibilità su sfondo chiaro */
        h1, h2, h3, p, span, label, .stTabs [data-baseweb="tab"] {{
            color: #1e3d1e !important; /* Verde molto scuro quasi nero */
            font-weight: 600;
        }}

        /* Sidebar (Barra laterale) - Sfondo chiaro */
        [data-testid="stSidebar"] {{
            background-color: rgba(255, 255, 255, 0.9) !important;
        }}
        
        /* Colore dei testi nella Sidebar */
        [data-testid="stSidebar"] .stMarkdown p, 
        [data-testid="stSidebar"] label {{
            color: #1e3d1e !important;
        }}
        
        /* Bottoni e input */
        .stButton>button {{
            background-color: #2e7d32;
            color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 2. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
apply_light_football_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET CORRETTI (Valori aggiornati)
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131, "PIETRO": 101.5,
    "PIERLUIGI": 105, "GIGI": 232.5, "ANDREA": 139, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113
}

# 4. SIDEBAR
st.sidebar.header("📂 Caricamento Dati")
file_rose = st.sidebar.file_uploader("1. Rose Attuali (CSV)", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Vincoli (CSV)", type="csv")

def carica_e_pulisci_rose(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Fantasquadra', 'Nome'])
    df['Fantasquadra'] = df['Fantasquadra'].str.strip().str.upper()
    df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce').fillna(0)
    return df

def carica_e_pulisci_vincoli(file):
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

df_rose = carica_e_pulisci_rose(file_rose)
df_vincoli = carica_e_pulisci_vincoli(file_vincoli)

# 5. TAB
if df_rose is not None:
    nomi_tab = ["📊 Economia", "🏃 Rose", "📅 Vincoli"]
    tabs = st.tabs(nomi_tab[:2] + (["📅 Vincoli"] if df_vincoli is not None else []))

    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
        st.dataframe(analisi.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])

    with tabs[1]:
        squadre = sorted(df_rose['Fantasquadra'].unique())
        scelta = st.selectbox("Squadra:", squadre, key="r")
        st.dataframe(df_rose[df_rose['Fantasquadra'] == scelta][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    if df_vincoli is not None:
        with tabs[2]:
            st.subheader("Strategia Futura")
            impegno = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("Debiti 26/27")
                st.dataframe(impegno, hide_index=True)
            with c2:
                s_v = st.selectbox("Dettaglio vincoli:", sorted(df_vincoli['Squadra'].unique()), key="v")
                st.dataframe(df_vincoli[df_vincoli['Squadra'] == s_v][['Giocatore', 'Costo 2026-27', 'Durata (anni)']], hide_index=True)
else:
    st.info("Carica i
