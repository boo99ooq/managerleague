def set_bg_image():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("");
            background-attachment: fixed;
            background-size: cover;
        }}
        
        /* Pannelli semi-trasparenti per leggere bene i dati */
        .stTabs, .stMetric, [data-testid="stMetricValue"], .stDataFrame, .stTable {{
            background-color: rgba(0, 0, 0, 0.6) !important;
            padding: 15px;
            border-radius: 10px;
            color: white !important;
        }}
        
        /* Colore dei titoli per farli risaltare */
        h1, h2, h3, p {{
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg_image()
import streamlit as st
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.title("⚽ Centro Direzionale Fantalega")

# 2. Budget di Febbraio
budgets_fisso = {
    "GIANNI": 164, "DANI ROBI": 162, "MARCO": 194, "PIETRO": 164,
    "PIERLUIGI": 240, "GIGI": 222, "ANDREA": 165, "GIUSEPPE": 174,
    "MATTEO": 166, "NICHOLAS": 162
}

# 3. Sidebar per caricamento
st.sidebar.header("Caricamento Database")
file_rose = st.sidebar.file_uploader("1. Carica Rose Attuali (CSV)", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica File Vincoli (CSV)", type="csv")

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
    
    # Rimuoviamo righe di testo/commenti (quelle che iniziano con * o `)
    df = df[df['Squadra'].notna()]
    df = df[~df['Squadra'].str.contains(r'\*|`|:', na=False)]
    
    # Standardizzazione nomi squadre per farli combaciare con budgets_fisso
    df['Squadra'] = df['Squadra'].str.strip().str.upper()
    mappa_nomi = {"NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"} 
    df['Squadra'] = df['Squadra'].replace(mappa_nomi)
    
    # Conversione numerica costi
    for col in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df_rose = carica_e_pulisci_rose(file_rose)
df_vincoli = carica_e_pulisci_vincoli(file_vincoli)

if df_rose is not None:
    nomi_tab = ["📊 Potenziale Economico", "🏃 Dettaglio Rose"]
    if df_vincoli is not None: nomi_tab.append("📅 Vincoli e Futuro")
    tabs = st.tabs(nomi_tab)

    # --- TAB 1: ECONOMIA CORRENTE ---
    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Potenziale Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
        st.dataframe(analisi.sort_values('Potenziale Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])

    # --- TAB 2: DETTAGLIO ROSE ---
    with tabs[1]:
        squadre_rose = sorted(df_rose['Fantasquadra'].unique())
        scelta_rosa = st.selectbox("Seleziona Squadra per Rose:", squadre_rose, key="sel_rose")
        dati_squadra = df_rose[df_rose['Fantasquadra'] == scelta_rosa]
        st.dataframe(dati_squadra[['Ruolo', 'Nome', 'Prezzo']], use_container_width=True, hide_index=True)

    # --- TAB 3: VINCOLI (CORRETTA) ---
    if df_vincoli is not None:
        with tabs[2]:
            st.subheader("Pianificazione Contratti Futuri")
            
            # 1. Riepilogo Generale
            impegno_2627 = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            impegno_2627.columns = ['Fantasquadra', 'Spesa Impegnata 26/27']
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("**Riepilogo Debiti 26/27:**")
                st.dataframe(impegno_2627.sort_values('Spesa Impegnata 26/27', ascending=False), hide_index=True)
            
            with c2:
                # 2. Selettore INDIPENDENTE per i vincoli
                squadre_vincoli = sorted(df_vincoli['Squadra'].unique())
                scelta_v = st.selectbox("Visualizza i vincoli di:", squadre_vincoli, key="sel_vincoli")
                
                vincoli_team = df_vincoli[df_vincoli['Squadra'] == scelta_v]
                st.write(f"**Giocatori Blindati per {scelta_v}:**")
                
                if not vincoli_team.empty:
                    st.dataframe(
                        vincoli_team[['Giocatore', 'Costo 2026-27', 'Durata (anni)']], 
                        hide_index=True, 
                        use_container_width=True
                    )
                else:
                    st.warning("Nessun vincolo trovato per questa squadra.")
else:
    st.info("👋 Carica i file CSV per attivare i cruscotti.")

