import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE (Titolo Bianco e Sfondo Scuro)
def apply_pro_style():
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
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background-color: rgba(0, 0, 0, 0.85) !important;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        h1 {{
            color: #ffffff !important;
            text-shadow: 3px 3px 5px #000000;
            text-align: center;
            font-size: 3rem !important;
        }}
        h2, h3, p, span, label, .stTabs [data-baseweb="tab"] {{
            color: #ffffff !important;
            font-weight: 700 !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: rgba(0, 0, 0, 0.95) !important;
            border-right: 2px solid #ffffff;
        }}
        .stDataFrame td, .stDataFrame th {{
            color: #ffffff !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_pro_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET AGGIORNATI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. CARICAMENTO DATI (Risolto errore Delimiter)
st.sidebar.header("📂 Menu Dati")
file_rose = st.sidebar.file_uploader("1. Carica Rose", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica Vincoli", type="csv")

def pulisci_dataframe(df):
    # Toglie spazi dai nomi delle colonne e dai dati testuali
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(['object']).columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def carica_file(file):
    if file is None: return None
    try:
        # Usiamo esplicitamente la virgola per evitare il "bad delimiter error"
        file.seek(0)
        df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
        return pulisci_dataframe(df)
    except Exception as e:
        # Se fallisce con la virgola (magari un export diverso), prova il punto e virgola
        try:
            file.seek(0)
            df = pd.read_csv(file, sep=';', skip_blank_lines=True, encoding='utf-8-sig')
            return pulisci_dataframe(df)
        except:
            st.error(f"Errore critico nel file: {e}")
            return None

df_rose = carica_file(file_rose)
df_vincoli = carica_file(file_vincoli)

if df_rose is not None:
    # Trasformiamo Prezzo in numero
    df_rose['Prezzo'] = pd.to_numeric(df_rose['Prezzo'], errors='coerce').fillna(0)
    df_rose['Fantasquadra'] = df_rose['Fantasquadra'].str.upper()

    tabs = st.tabs(["📊 Economia", "📈 Analisi Reparti", "🏆 Record & Top", "🏃 Rose", "📅 Vincoli"])

    # --- TAB ECONOMIA ---
    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Extra Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Totale'] = analisi['Valore Rosa'] + analisi['Extra Febbraio']
        st.dataframe(analisi.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Extra Febbraio'])

    # --- TAB ANALISI REPARTI ---
    with tabs[1]:
        st.subheader("Distribuzione Spesa per Ruolo")
        pivot = df_rose.pivot_table(index='Fantasquadra', columns='Ruolo', values='Prezzo', aggfunc='sum').fillna(0)
        ord_r = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
        pivot = pivot[[c for c in ord_r if c in pivot.columns]]
        
        try:
            st.dataframe(pivot.style.background_gradient(cmap='YlGn', axis=None).format("{:.1f}"), use_container_width=True)
        except ImportError:
            st.dataframe(pivot, use_container_width=True)
            st.info("💡 Per vedere i colori, ricorda di creare il file 'requirements.txt' con scritto 'matplotlib'")

    # --- TAB RECORD & TOP ---
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("💎 Top 20 più Costosi")
            top_20 = df_rose.sort_values(by='Prezzo', ascending=False).head(20)
            st.dataframe(top_20[['Nome', 'Fantasquadra', 'Ruolo', 'Prezzo']], hide_index=True, use_container_width=True)
        with c2:
            st.subheader("🥇 I Re dei Reparti")
            idx = df_rose.groupby('Ruolo')['Prezzo'].idxmax()
            st.table(df_rose.loc[idx, ['Ruolo', 'Nome', 'Fantasquadra', 'Prezzo']])

    # --- TAB DETTAGLIO ROSE ---
    with tabs[3]:
        squadre = sorted(df_rose['Fantasquadra'].unique())
        scelta = st.selectbox("Seleziona Squadra:", squadre)
        st.dataframe(df_rose[df_rose['Fantasquadra'] == scelta][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    # --- TAB VINCOLI ---
    with tabs[4]:
        if df_vincoli is not None:
            df_vincoli.columns = df_vincoli.columns.str.strip()
            # Pulizia per il file vincoli
            v_col = 'Costo 2026-27'
            if v_col in df_vincoli.columns:
                df_vincoli[v_col] = pd.to_numeric(df_vincoli[v_col], errors='coerce').fillna(0)
                impegno = df_vincoli.groupby('Squadra')[v_col].sum().reset_index()
                st.write("**Impegno economico 2026/27:**")
                st.dataframe(impegno, hide_index=True, use_container_width=True)
        else:
            st.info("Carica il file 'vincoli 26.csv' per vedere i dati futuri.")
else:
    st.info("👋 Carica i file CSV per visualizzare l'analisi.")
