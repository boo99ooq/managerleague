import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE: SFONDO VERDE CHIARO E TESTI SCURI
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
        /* Accentramento testo nelle colonne numeriche */
        [data-testid="stTable"] td { text-align: center !important; }
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

# 4. SIDEBAR PER INSERIMENTO FILE
st.sidebar.header("📂 Caricamento Dati")
f_scontri = st.sidebar.file_uploader("Classifica Scontri", type="csv")
f_punti = st.sidebar.file_uploader("Classifica Punti", type="csv")
f_rose = st.sidebar.file_uploader("Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("Vincoli 2026/27", type="csv")

# Funzioni di pulizia
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

df_scontri = carica_csv(f_scontri)
df_punti_tot = carica_csv(f_punti)
df_rose = carica_csv(f_rose)
df_vincoli = carica_csv(f_vinc)

# 5. LOGICA APPLICAZIONE
if df_rose is not None:
    df_rose = df_rose.dropna(subset=['Fantasquadra', 'Nome'])
    df_rose = pulisci_nomi(df_rose, 'Fantasquadra')
    df_rose['Prezzo'] = pd.to_numeric(df_rose['Prezzo'], errors='coerce').fillna(0)

    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # --- TAB CLASSIFICHE ---
    with tabs[0]:
        cl1, cl2 = st.columns(2)
        with cl1:
            st.subheader("🔥 Scontri Diretti")
            if df_scontri is not None:
                df_scontri = pulisci_nomi(df_scontri, 'Giocatore')
                cols = ['Posizione', 'Giocatore', 'Punti', 'Gol Fatti', 'Gol Subiti', 'Differenza Reti']
                st.dataframe(df_scontri[cols].sort_values('Punti', ascending=False), hide_index=True, 
                             column_config={
                                 "Posizione": st.column_config.Column(width="small"),
                                 "Punti": st.column_config.NumberColumn(format="%d", width="medium")
                             }, use_container_width=True)
            else: st.info("Carica scontridiretti.csv")
        with cl2:
            st.subheader("🎯 Punti Totali")
            if df_punti_tot is not None:
                df_punti_tot = pulisci_nomi(df_punti_tot, 'Giocatore')
                if 'Punti Totali' in df_punti_tot.columns:
                    df_punti_tot['Punti Totali'] = df_punti_tot['Punti Totali'].astype(str).str.replace(',', '.').astype(float)
                st.dataframe(df_punti_tot[['Posizione', 'Giocatore', 'Punti Totali', 'Media']].sort_values('Punti Totali', ascending=False), 
                             hide_index=True, column_config={"Posizione": st.column_config.Column(width="small")}, use_container_width=True)

    # --- TAB ECONOMIA ---
    with tabs[1]:
        st.subheader("💰 Bilancio Rose")
        eco = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco.columns = ['Fantasquadra', 'Costo della Rosa']
        eco['Extra Febbraio'] = eco['Fantasquadra'].map(budgets_fisso).fillna(0)
        eco['Budget Totale'] = eco['Costo della Rosa'] + eco['Extra Febbraio']
        st.dataframe(eco.sort_values('Budget Totale', ascending=False), hide_index=True, use_container_width=True)

    # --- TAB STRATEGIA ---
    with tabs[2]:
        st.subheader("📋 Analisi Reparti")
        ordine_ruoli = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
        pivot_count = df_rose.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
        colonne_presenti = [r for r in ordine_ruoli if r in pivot_count.columns]
        st.dataframe(pivot_count[colonne_presenti], use_container_width=True)

    # --- TAB ROSE ---
    with tabs[3]:
        sq_lista = sorted(df_rose['Fantasquadra'].unique())
        scelta_sq = st.selectbox("Seleziona Squadra:", sq_lista)
        df_sq = df_rose[df_rose['Fantasquadra'] == scelta_sq][['Ruolo', 'Nome', 'Prezzo']]
        st.dataframe(df_sq.sort_values('Prezzo', ascending=False).style.background_gradient(subset=['Prezzo'], cmap='Greens'), 
                     hide_index=True, use_container_width=True)

    # --- TAB VINCOLI ---
    with tabs[4]:
        st.subheader("📅 Contratti 2026/27")
        if df_vincoli is not None:
            df_v_clean = df_vincoli[df_vincoli['Giocatore'].notna()].copy()
            df_v_clean = df_v_clean[~df_v_clean['Squadra'].str.contains(r'\*|`|Riepilogo', na=False)]
            df_v_clean = pulisci_nomi(df_v_clean, 'Squadra')
            
            c_v1, c_v2 = st.columns([1, 2])
            with c_v1:
                st.write("**Riepilogo Debiti:**")
                riepilogo = df_v_clean.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
                st.dataframe(riepilogo.sort_values('Costo 2026-27', ascending=False), hide_index=True)
            with c_v2:
                sq_v_lista = sorted(df_v_clean['Squadra'].unique())
                scelta_v = st.selectbox("Vedi Giocatori di:", sq_v_lista)
                st.dataframe(df_v_clean[df_v_clean['Squadra'] == scelta_v][['Giocatore', 'Costo 2026-27']], hide_index=True, use_container_width=True)
        else: st.info("Carica il file dei vincoli.")
else:
    st.info("👋 Carica i file CSV per iniziare l'analisi.")
