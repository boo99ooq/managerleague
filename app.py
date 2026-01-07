import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE PROFESSIONALE
def apply_pro_style():
    img_url = "[https://images.unsplash.com/photo-1556056504-5c7696c4c28d?q=80&w=2076&auto=format&fit=crop](https://images.unsplash.com/photo-1556056504-5c7696c4c28d?q=80&w=2076&auto=format&fit=crop)"
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

# 4. SIDEBAR
st.sidebar.header("📂 Menu Dati")
file_rose = st.sidebar.file_uploader("1. Carica Rose", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica Vincoli", type="csv")

# --- FUNZIONI DI PULIZIA AVANZATA ---
def carica_rose(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Fantasquadra', 'Nome'])
    df['Fantasquadra'] = df['Fantasquadra'].str.strip().str.upper()
    df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce').fillna(0)
    # Correzione nomi squadre
    df['Fantasquadra'] = df['Fantasquadra'].replace({"NICHO": "NICHOLAS"})
    return df

def carica_vincoli(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    df.columns = df.columns.str.strip()
    
    # 1. Rimuoviamo le righe di riepilogo "sporche" (quelle che iniziano con * o ` o non hanno giocatore)
    df = df[df['Giocatore'].notna()] 
    df = df[~df['Squadra'].str.contains(r'\*|`|:', na=False)]
    
    # 2. Pulizia e Standardizzazione nomi
    df['Squadra'] = df['Squadra'].str.strip().str.upper()
    mappa_nomi = {"NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}
    df['Squadra'] = df['Squadra'].replace(mappa_nomi)
    
    # 3. Conversione costi in numeri
    for col in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

df_rose = carica_rose(file_rose)
df_vincoli = carica_vincoli(file_vincoli)

if df_rose is not None:
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
        except:
            st.dataframe(pivot, use_container_width=True)

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
        squadre_r = sorted(df_rose['Fantasquadra'].unique())
        scelta_r = st.selectbox("Seleziona Squadra:", squadre_r, key="sb_rose")
        st.dataframe(df_rose[df_rose['Fantasquadra'] == scelta_r][['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

    # --- TAB VINCOLI (RISOLTA) ---
    with tabs[4]:
        if df_vincoli is not None:
            st.subheader("Pianificazione Debiti 2026/27")
            
            # 1. Riepilogo pulito e ordinato
            riepilogo_v = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            riepilogo_v.columns = ['Fantasquadra', 'Impegno 26/27 (Crediti)']
            
            col_v1, col_v2 = st.columns([1, 2])
            
            with col_v1:
                st.write("**Classifica Debiti:**")
                st.dataframe(riepilogo_v.sort_values('Impegno 26/27 (Crediti)', ascending=False), hide_index=True)
            
            with col_v2:
                # 2. Selettore specifico per i vincoli (permette di vedere i giocatori di ogni squadra)
                lista_squadre_v = sorted(df_vincoli['Squadra'].unique())
                scelta_v = st.selectbox("Dettaglio Giocatori Vincolati:", lista_squadre_v, key="sb_vinc")
                
                dettaglio_team = df_vincoli[df_vincoli['Squadra'] == scelta_v]
                st.write(f"**Giocatori di {scelta_v} con contratto per il 26/27:**")
                st.dataframe(
                    dettaglio_team[['Giocatore', 'Costo 2026-27', 'Durata (anni)']].sort_values('Costo 2026-27', ascending=False),
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info("Carica il file 'vincoli 26.csv' per visualizzare i debiti futuri.")

else:
    st.info("👋 Carica i file CSV per iniziare l'analisi.")
