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
            background: rgba(0, 0, 0, 0.7) !important;
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

# 3. BUDGET FISSI (DA FEBBRAIO)
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. CARICAMENTO DATI
st.sidebar.header("📂 Menu Dati")
file_rose = st.sidebar.file_uploader("1. Carica Rose", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica Vincoli", type="csv")

def carica_rose(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Fantasquadra', 'Nome'])
    df['Fantasquadra'] = df['Fantasquadra'].str.strip().str.upper()
    df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce').fillna(0)
    df['Fantasquadra'] = df['Fantasquadra'].replace({"NICHO": "NICHOLAS"})
    return df

def carica_vincoli(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    df = df[df['Giocatore'].notna()]
    df = df[~df['Squadra'].str.contains(r'\*|`|:', na=False)]
    df['Squadra'] = df['Squadra'].str.strip().str.upper()
    df['Squadra'] = df['Squadra'].replace({"NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"})
    for col in ['Costo 2026-27']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df_rose = carica_rose(file_rose)
df_vincoli = carica_vincoli(file_vincoli)

if df_rose is not None:
    tabs = st.tabs(["📊 Riepilogo", "📈 Strategia", "🏆 Top & Record", "🏃 Rose", "📅 Vincoli"])

    # --- TAB RIEPILOGO ---
    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        st.dataframe(analisi.sort_values('Valore Rosa', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y='Valore Rosa')

    # --- TAB STRATEGIA (NOVITÀ!) ---
    with tabs[1]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Conteggio Giocatori per Ruolo")
            # Conta quanti giocatori ha ogni squadra per ruolo
            count_pivot = df_rose.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0)
            st.dataframe(count_pivot.astype(int), use_container_width=True)
            st.caption("Serve per capire chi deve comprare per completare i reparti.")

        with col2:
            st.subheader("💸 Analisi Low Cost (Prezzo 1)")
            # Mostra chi ha fatto più acquisti a 1 credito
            low_cost = df_rose[df_rose['Prezzo'] == 1].groupby('Fantasquadra')['Nome'].count().reset_index()
            low_cost.columns = ['Fantasquadra', 'N. Giocatori a 1']
            st.dataframe(low_cost.sort_values('N. Giocatori a 1', ascending=False), hide_index=True, use_container_width=True)
            st.caption("Scommesse vinte o riempitivi?")

    # --- TAB TOP & RECORD ---
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("💎 Top 20 Spese")
            st.dataframe(df_rose.sort_values('Prezzo', ascending=False).head(20)[['Nome', 'Fantasquadra', 'Prezzo']], hide_index=True)
        with c2:
            st.subheader("🥇 I più cari per Ruolo")
            st.table(df_rose.loc[df_rose.groupby('Ruolo')['Prezzo'].idxmax(), ['Ruolo', 'Nome', 'Prezzo']])

    # --- TAB ROSE ---
    with tabs[3]:
        sq = sorted(df_rose['Fantasquadra'].unique())
        s = st.selectbox("Scegli Squadra:", sq)
        st.dataframe(df_rose[df_rose['Fantasquadra'] == s][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    # --- TAB VINCOLI ---
    with tabs[4]:
        if df_vincoli is not None:
            riepilogo_v = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            st.write("**Impegno economico futuro (2026/27):**")
            st.dataframe(riepilogo_v.sort_values('Costo 2026-27', ascending=False), hide_index=True)
            
            sq_v = sorted(df_vincoli['Squadra'].unique())
            s_v = st.selectbox("Vedi Giocatori Vincolati:", sq_v)
            st.dataframe(df_vincoli[df_vincoli['Squadra'] == s_v][['Giocatore', 'Costo 2026-27']], hide_index=True)
else:
    st.info("Carica i CSV per vedere le nuove statistiche di mercato!")
