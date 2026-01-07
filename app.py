import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE GLASSMORPHISM
def apply_glass_style():
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
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 20px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        h1 {{
            color: #ffffff !important;
            text-shadow: 0 0 15px rgba(46, 204, 113, 0.9);
            text-align: center;
            font-size: 3.5rem !important;
        }}
        h2, h3, p, span, label, .stTabs [data-baseweb="tab"] {{
            color: #ffffff !important;
        }}
        [data-testid="stSidebar"] {{
            background: rgba(0, 0, 0, 0.8) !important;
            backdrop-filter: blur(15px);
        }}
        .stDataFrame td, .stDataFrame th {{
            color: #ffffff !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_glass_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. SIDEBAR PER CARICAMENTO
st.sidebar.header("📂 Menu Dati")
file_class_scontri = st.sidebar.file_uploader("1. Classifica Scontri Diretti (scontridiretti.csv)", type="csv")
file_class_punti = st.sidebar.file_uploader("2. Classifica Punti Totali (classificapunti.csv)", type="csv")
file_rose = st.sidebar.file_uploader("3. Carica Rose (nuove rose.csv)", type="csv")
file_vincoli = st.sidebar.file_uploader("4. Carica Vincoli (vincoli.csv)", type="csv")

# Funzioni di pulizia
def pulisci_nomi(df, col):
    mappa = {
        "NICO FABIO": "NICHOLAS", 
        "NICHO": "NICHOLAS", 
        "DANI ROBI": "DANI ROBI",
        "MATTEO STEFANO": "MATTEO"
    }
    df[col] = df[col].str.strip().str.upper().replace(mappa)
    return df

def carica_csv(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    return df

df_scontri = carica_csv(file_class_scontri)
df_punti_tot = carica_csv(file_class_punti)
df_rose = carica_csv(file_rose)
df_vincoli = carica_csv(file_vincoli)

# 5. LOGICA VISUALIZZAZIONE
if df_rose is not None:
    # Pulizia Rose
    df_rose = df_rose.dropna(subset=['Fantasquadra', 'Nome'])
    df_rose = pulisci_nomi(df_rose, 'Fantasquadra')
    df_rose['Prezzo'] = pd.to_numeric(df_rose['Prezzo'], errors='coerce').fillna(0)

    # Definizione Tab
    nomi_tabs = ["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏆 Top & Record", "🏃 Rose", "📅 Vincoli"]
    tabs = st.tabs(nomi_tabs)

    # --- TAB 0: CLASSIFICHE ---
    with tabs[0]:
        col_cl1, col_cl2 = st.columns(2)
        
        with col_cl1:
            st.subheader("🔥 Scontri Diretti")
            if df_scontri is not None:
                df_scontri = pulisci_nomi(df_scontri, 'Giocatore')
                df_disp_s = df_scontri[['Posizione', 'Giocatore', 'Punti', 'Gol Fatti', 'Gol Subiti']]
                st.dataframe(df_disp_s.sort_values('Punti', ascending=False), hide_index=True, use_container_width=True)
                st.bar_chart(df_scontri, x='Giocatore', y='Punti', color="#2ecc71")
            else:
                st.info("Carica 'scontridiretti.csv'")

        with col_cl2:
            st.subheader("🎯 Punti Totali")
            if df_punti_tot is not None:
                df_punti_tot = pulisci_nomi(df_punti_tot, 'Giocatore')
                # Pulizia numeri con virgola (es 1074,5 -> 1074.5)
                for c in ['Punti Totali', 'Distacco']:
                    if c in df_punti_tot.columns:
                        df_punti_tot[c] = df_punti_tot[c].astype(str).str.replace(',', '.').astype(float)
                
                df_disp_p = df_punti_tot[['Posizione', 'Giocatore', 'Punti Totali', 'Media', 'Distacco']]
                st.dataframe(df_disp_p.sort_values('Punti Totali', ascending=False), hide_index=True, use_container_width=True)
                st.bar_chart(df_punti_tot, x='Giocatore', y='Punti Totali', color="#3498db")
            else:
                st.info("Carica 'classificapunti.csv'")

    # --- TAB 1: ECONOMIA ---
    with tabs[1]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Potenziale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
        st.dataframe(analisi.sort_values('Potenziale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])

    # --- TAB 2: STRATEGIA ---
    with tabs[2]:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 Conteggio per Ruolo")
            pivot_count = df_rose.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
            st.dataframe(pivot_count, use_container_width=True)
        with col2:
            st.subheader("🕵️ Analisi Strategica")
            idx_max = df_rose.groupby('Fantasquadra')['Prezzo'].idxmax()
            top_p = df_rose.loc[idx_max, ['Fantasquadra', 'Nome', 'Prezzo']]
            st.write("**Giocatore più costoso per squadra:**")
            st.dataframe(top_p.sort_values('Prezzo', ascending=False), hide_index=True)

    # --- TAB 3: TOP & RECORD ---
    with tabs[3]:
        st.subheader("💎 I 20 Giocatori più pagati della Lega")
        st.dataframe(df_rose.sort_values('Prezzo', ascending=False).head(20)[['Nome', 'Fantasquadra', 'Prezzo']], hide_index=True, use_container_width=True)

    # --- TAB 4: ROSE ---
    with tabs[4]:
        sq = sorted(df_rose['Fantasquadra'].unique())
        scelta = st.selectbox("Vedi Rosa di:", sq)
        st.dataframe(df_rose[df_rose['Fantasquadra'] == scelta][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    # --- TAB 5: VINCOLI ---
    with tabs[5]:
        if df_vincoli is not None:
            df_vincoli = pulisci_nomi(df_vincoli, 'Squadra')
            if 'Costo 2026-27' in df_vincoli.columns:
                df_vincoli['Costo 2026-27'] = pd.to_numeric(df_vincoli['Costo 2026-27'], errors='coerce').fillna(0)
                riepilogo_v = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
                st.dataframe(riepilogo_v.sort_values('Costo 2026-27', ascending=False), hide_index=True)
