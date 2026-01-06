import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE GLASSMORPHISM (Vetro satinato, meno nero, più trasparenza)
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
        
        /* Pannelli centrali: Effetto Vetro Satinato */
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
        
        /* TITOLO BIANCO CON GLOW */
        h1 {{
            color: #ffffff !important;
            text-shadow: 0 0 10px rgba(46, 204, 113, 0.8), 0 0 20px rgba(0,0,0,0.5);
            text-align: center;
            font-size: 3.5rem !important;
            padding-bottom: 20px;
        }}
        
        h2, h3, p, span, label, .stTabs [data-baseweb="tab"] {{
            color: #ffffff !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }}

        /* SIDEBAR: Trasparente satinata */
        [data-testid="stSidebar"] {{
            background: rgba(0, 0, 0, 0.6) !important;
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        /* Sistemazione colori input sidebar */
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {{
            color: #ffffff !important;
            font-weight: bold;
        }}
        
        /* Colore celle tabelle per contrasto */
        .stDataFrame td, .stDataFrame th {{
            color: #ffffff !important;
            background-color: rgba(0, 0, 0, 0.2) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_glass_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET AGGIORNATI
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
    for col in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df_rose = carica_rose(file_rose)
df_vincoli = carica_vincoli(file_vincoli)

# 5. VISUALIZZAZIONE
if df_rose is not None:
    tabs = st.tabs(["📊 Economia", "📈 Analisi Reparti", "🏆 Record & Top", "🏃 Rose", "📅 Vincoli"])

    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Extra Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Totale'] = analisi['Valore Rosa'] + analisi['Extra Febbraio']
        st.dataframe(analisi.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Extra Febbraio'])

    with tabs[1]:
        st.subheader("Distribuzione Spesa per Ruolo")
        pivot = df_rose.pivot_table(index='Fantasquadra', columns='Ruolo', values='Prezzo', aggfunc='sum').fillna(0)
        ord_r = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
        pivot = pivot[[c for c in ord_r if c in pivot.columns]]
        try:
            st.dataframe(pivot.style.background_gradient(cmap='YlGn', axis=None).format("{:.1f}"), use_container_width=True)
        except:
            st.dataframe(pivot, use_container_width=True)

    with tabs[2]:
        c1, col_space, c2 = st.columns([1, 0.1, 1])
        with c1:
            st.subheader("💎 Top 20 Giocatori")
            top_20 = df_rose.sort_values(by='Prezzo', ascending=False).head(20)
            st.dataframe(top_20[['Nome', 'Fantasquadra', 'Prezzo']], hide_index=True, use_container_width=True)
        with c2:
            st.subheader("💰 Costo Medio")
            media = df_rose.groupby('Fantasquadra')['Prezzo'].mean().reset_index()
            st.dataframe(media.sort_values('Prezzo', ascending=False).style.format({"Prezzo": "{:.2f}"}), hide_index=True)

    with tabs[3]:
        squadre_r = sorted(df_rose['Fantasquadra'].unique())
        scelta_r = st.selectbox("Seleziona Squadra:", squadre_r, key="rose_sel")
        st.dataframe(df_rose[df_rose['Fantasquadra'] == scelta_r][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    with tabs[4]:
        if df_vincoli is not None:
            st.subheader("Pianificazione Debiti 2026/27")
            riepilogo_v = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            riepilogo_v.columns = ['Fantasquadra', 'Impegno 26/27']
            cv1, cv2 = st.columns([1, 2])
            with cv1:
                st.dataframe(riepilogo_v.sort_values('Impegno 26/27', ascending=False), hide_index=True)
            with cv2:
                lista_v = sorted(df_vincoli['Squadra'].unique())
                scelta_v = st.selectbox("Dettaglio Vincoli:", lista_v, key="vinc_sel")
                dettaglio = df_vincoli[df_vincoli['Squadra'] == scelta_v]
                st.dataframe(dettaglio[['Giocatore', 'Costo 2026-27', 'Durata (anni)']], hide_index=True, use_container_width=True)
else:
    st.info("👋 Carica i file CSV per attivare i cruscotti.")
