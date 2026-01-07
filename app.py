import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE GLASSMORPHISM COMPATTO (Sidebar ultra-ridotta)
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
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(12px);
            padding: 15px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        [data-testid="stSidebar"] {{
            background: rgba(0, 0, 0, 0.8) !important;
            backdrop-filter: blur(15px);
            width: 260px !important;
        }}
        /* Riduzione estrema spazi file uploader */
        [data-testid="stFileUploader"] {{
            padding-bottom: 0px !important;
            margin-bottom: -25px !important;
        }}
        [data-testid="stFileUploader"] label p {{
            font-size: 13px !important;
            color: #2ecc71 !important;
            margin-bottom: -15px !important;
        }}
        h1 {{
            color: #ffffff !important;
            text-shadow: 0 0 10px rgba(46, 204, 113, 0.9);
            text-align: center;
            font-size: 2.2rem !important;
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
st.sidebar.markdown("### 📂 Database")
f_scontri = st.sidebar.file_uploader("Scontri Diretti", type="csv")
f_punti = st.sidebar.file_uploader("Classifica Punti", type="csv")
f_rose = st.sidebar.file_uploader("Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("Vincoli 26/27", type="csv")

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
            st.markdown("##### 🔥 Scontri Diretti")
            if df_scontri is not None:
                df_scontri = pulisci_nomi(df_scontri, 'Giocatore')
                st.dataframe(df_scontri[['Posizione', 'Giocatore', 'Punti']].sort_values('Punti', ascending=False), hide_index=True)
            else: st.caption("In attesa di scontridiretti.csv")
        with c_cl2:
            st.markdown("##### 🎯 Punti Totali")
            if df_punti_tot is not None:
                df_punti_tot = pulisci_nomi(df_punti_tot, 'Giocatore')
                if 'Punti Totali' in df_punti_tot.columns:
                    df_punti_tot['Punti Totali'] = df_punti_tot['Punti Totali'].astype(str).str.replace(',', '.').astype(float)
                st.dataframe(df_punti_tot[['Giocatore', 'Punti Totali', 'Media']].sort_values('Punti Totali', ascending=False), hide_index=True)
            else: st.caption("In attesa di classificapunti.csv")

    with tabs[1]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi['Extra'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Totale'] = analisi['Prezzo'] + analisi['Extra']
        st.dataframe(analisi.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Prezzo', 'Extra'])

    with tabs[2]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📋 Conteggio per Ruolo")
            pivot_count = df_rose.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
            st.dataframe(pivot_count, use_container_width=True)
        with col2:
            st.markdown("##### 🕵️ Top Spesa per Squadra")
            idx_max = df_rose.groupby('Fantasquadra')['Prezzo'].idxmax()
            st.dataframe(df_rose.loc[idx_max, ['Fantasquadra', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False), hide_index=True)

    with tabs[3]:
        sq = sorted(df_rose['Fantasquadra'].unique())
        scelta = st.selectbox("Seleziona Rosa:", sq)
        st.dataframe(df_rose[df_rose['Fantasquadra'] == scelta][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    with tabs[4]:
        if df_vincoli is not None:
            df_vincoli = pulisci_nomi(df_vincoli, 'Squadra')
            if 'Costo 2026-27' in df_vincoli.columns:
                df_vincoli['Costo 2026-27'] = pd.to_numeric(df_vincoli['Costo 2026-27'], errors='coerce').fillna(0)
                riepilogo_v = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
                st.dataframe(riepilogo_v.sort_values('Costo 2026-27', ascending=False), hide_index=True)
        else: st.caption("In attesa di vincoli.csv")
else:
    st.info("👋 Carica i file CSV per generare il cruscotto della lega.")
