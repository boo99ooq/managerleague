import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE PROFESSIONALE (Sfondo scuro, testi bianchi/verdi)
def apply_advanced_style():
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
            border-right: 2px solid #2ecc71;
        }}
        /* Colore delle celle nelle tabelle */
        .stDataFrame td {{ color: white !important; }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_advanced_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET FISSI AGGIORNATI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. SIDEBAR
st.sidebar.header("📂 Gestione Database")
file_rose = st.sidebar.file_uploader("1. Carica Rose (CSV)", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica Vincoli (CSV)", type="csv")

# Funzioni caricamento
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

if df_rose is not None:
    tabs = st.tabs(["📊 Economia", "📈 Analisi Reparti", "🏃 Rose", "📅 Vincoli", "🔍 Cerca"])

    # --- TAB 0: ECONOMIA ---
    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Extra Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Totale'] = analisi['Valore Rosa'] + analisi['Extra Febbraio']
        st.dataframe(analisi.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Extra Febbraio'])

    # --- TAB 1: ANALISI REPARTI (NOVITÀ HEATMAP) ---
    with tabs[1]:
        st.subheader("Distribuzione della Spesa per Ruolo")
        
        # Creazione Tabella Pivot per Ruolo
        pivot_spesa = df_rose.pivot_table(
            index='Fantasquadra', 
            columns='Ruolo', 
            values='Prezzo', 
            aggfunc='sum'
        ).fillna(0)
        
        # Ordiniamo i ruoli in modo logico
        cols_ordine = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
        pivot_spesa = pivot_spesa[[c for c in cols_ordine if c in pivot_spesa.columns]]

        st.write("🔥 **Intensità di Spesa** (Colori più accesi = Investimento maggiore)")
        # Applichiamo la Heatmap
        st.dataframe(
            pivot_spesa.style.background_gradient(cmap='YlGn', axis=None).format("{:.1f}"),
            use_container_width=True
        )

        st.divider()
        st.write("📊 **Percentuale del Budget spesa per Reparto**")
        # Calcolo percentuale rispetto al totale della rosa
        pivot_pct = pivot_spesa.div(pivot_spesa.sum(axis=1), axis=0) * 100
        st.dataframe(
            pivot_pct.style.background_gradient(cmap='Blues', axis=None).format("{:.1f}%"),
            use_container_width=True
        )

    # --- TAB 2: DETTAGLIO ROSE ---
    with tabs[2]:
        squadre = sorted(df_rose['Fantasquadra'].unique())
        scelta = st.selectbox("Seleziona Squadra:", squadre)
        st.dataframe(df_rose[df_rose['Fantasquadra'] == scelta][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    # --- TAB 3: VINCOLI ---
    with tabs[3]:
        if df_vincoli is not None:
            st.dataframe(df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index(), hide_index=True)
        else: st.info("Carica i vincoli per i dati futuri.")

    # --- TAB 4: RICERCA ---
    with tabs[4]:
        nome = st.text_input("Cerca un calciatore:")
        if nome:
            st.dataframe(df_rose[df_rose['Nome'].str.contains(nome, case=False, na=False)], hide_index=True)

else:
    st.info("Carica i file CSV per attivare le statistiche.")
