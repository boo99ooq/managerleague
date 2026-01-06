import streamlit as st
import pandas as pd

# 1. FUNZIONE PER LO SFONDO E LO STILE (Migliorata per visibilità sidebar e tabelle)
def apply_custom_style():
    st.markdown(
        f"""
        <style>
        /* Sfondo principale */
        .stApp {{
            background-image: url("https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=2070&auto=format&fit=crop");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        
        /* Pannelli delle tabelle e metriche */
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background-color: rgba(0, 0, 0, 0.7) !important;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        /* Stile speciale per la Sidebar (Barra laterale) */
        [data-testid="stSidebar"] {{
            background-color: rgba(0, 0, 0, 0.8) !important;
        }}
        
        /* Colore dei testi nella Sidebar */
        [data-testid="stSidebar"] .stMarkdown p, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: #ffffff !important;
            font-weight: bold;
        }}

        /* Forza il bianco per tutti i testi principali dell'app */
        h1, h2, h3, p, span, label, .stTabs [data-baseweb="tab"] {{
            color: #ffffff !important;
        }}
        
        /* Migliora la visibilità dei nomi nelle tabelle */
        .stDataFrame td, .stDataFrame th {{
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 2. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
apply_custom_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET DI FEBBRAIO (Valori Aggiornati)
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131, "PIETRO": 101.5,
    "PIERLUIGI": 105, "GIGI": 232.5, "ANDREA": 139, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113
}

# 4. SIDEBAR PER CARICAMENTO
st.sidebar.header("📂 Database")
file_rose = st.sidebar.file_uploader("1. Carica Rose Attuali (CSV)", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica File Vincoli (CSV)", type="csv")

# FUNZIONI DI CARICAMENTO DATI
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

# 5. VISUALIZZAZIONE DATI
if df_rose is not None:
    nomi_tab = ["📊 Potenziale Economico", "🏃 Dettaglio Rose"]
    if df_vincoli is not None: nomi_tab.append("📅 Vincoli e Futuro")
    tabs = st.tabs(nomi_tab)

    # --- TAB 1: ECONOMIA ---
    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Potenziale Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
        
        st.subheader("Riepilogo Finanziario")
        st.dataframe(analisi.sort_values('Potenziale Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])

    # --- TAB 2: DETTAGLIO ---
    with tabs[1]:
        squadre_rose = sorted(df_rose['Fantasquadra'].unique())
        scelta_rosa = st.selectbox("Seleziona Squadra:", squadre_rose, key="sel_rose")
        dati_squadra = df_rose[df_rose['Fantasquadra'] == scelta_rosa]
        st.dataframe(dati_squadra[['Ruolo', 'Nome', 'Prezzo']], use_container_width=True, hide_index=True)

    # --- TAB 3: VINCOLI ---
    if df_vincoli is not None:
        with tabs[2]:
            st.subheader("Strategia Pluriennale")
            impegno_2627 = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            impegno_2627.columns = ['Fantasquadra', 'Spesa Impegnata 26/27']
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("**Debiti per la prossima stagione:**")
                st.dataframe(impegno_2627.sort_values('Spesa Impegnata 26/27', ascending=False), hide_index=True)
            with c2:
                squadre_vincoli = sorted(df_vincoli['Squadra'].unique())
                scelta_v = st.selectbox("Dettaglio Vincoli per:", squadre_vincoli, key="sel_vincoli")
                vincoli_team = df_vincoli[df_vincoli['Squadra'] == scelta_v]
                if not vincoli_team.empty:
                    st.dataframe(vincoli_team[['Giocatore', 'Costo 2026-27', 'Durata (anni)']], hide_index=True, use_container_width=True)
                else:
                    st.warning("Nessun vincolo trovato.")
else:
    st.info("👋 Carica i file CSV per generare i grafici e le tabelle.")
