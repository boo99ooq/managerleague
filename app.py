import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE REVISIONATO (Sidebar unificata, tabelle colorate, font leggibili)
def apply_custom_style():
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
        
        /* Pannelli centrali */
        .stTabs, .stMetric, .stDataFrame {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(15px);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        /* SIDEBAR UNIFICATA (No blocchi separati) */
        [data-testid="stSidebar"] {{
            background: rgba(0, 0, 0, 0.85) !important;
            backdrop-filter: blur(10px);
            border-right: 1px solid #2ecc71;
        }}
        
        /* Testi Sidebar più grandi e leggibili */
        [data-testid="stSidebar"] label p {{
            font-size: 16px !important;
            font-weight: bold !important;
            color: #ffffff !important;
            margin-bottom: 5px !important;
        }}
        
        /* Riduzione spazio tra i caricamenti */
        [data-testid="stFileUploader"] {{
            margin-bottom: -10px !important;
        }}

        h1 {{
            color: #ffffff !important;
            text-shadow: 2px 2px 8px #000;
            text-align: center;
            font-size: 3rem !important;
        }}
        
        h2, h3, h4, h5, p, span {{
            color: #ffffff !important;
        }}

        /* Centratura colonne specifiche tramite classi Streamlit (ove possibile) */
        .stDataFrame [data-testid="stTable"] {{
            text-align: center !important;
        }}
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

# 4. CARICAMENTO DATI SIDEBAR
st.sidebar.markdown("### 🛠️ Configurazione Dati")
f_scontri = st.sidebar.file_uploader("Classifica Scontri", type="csv")
f_punti = st.sidebar.file_uploader("Classifica Punti", type="csv")
f_rose = st.sidebar.file_uploader("Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("Vincoli 2026/27", type="csv")

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

# 5. LOGICA APPLICAZIONE
if df_rose is not None:
    # Pre-elaborazione Rose
    df_rose = df_rose.dropna(subset=['Fantasquadra', 'Nome'])
    df_rose = pulisci_nomi(df_rose, 'Fantasquadra')
    df_rose['Prezzo'] = pd.to_numeric(df_rose['Prezzo'], errors='coerce').fillna(0)

    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # --- TAB CLASSIFICHE ---
    with tabs[0]:
        cl1, cl2 = st.columns(2)
        with cl1:
            st.markdown("#### 🔥 Scontri Diretti")
            if df_scontri is not None:
                df_scontri = pulisci_nomi(df_scontri, 'Giocatore')
                # Riduciamo larghezza 'Posizione' e mostriamo tutto
                df_s_display = df_scontri[['Posizione', 'Giocatore', 'Punti', 'Gol Fatti', 'Gol Subiti', 'Differenza Reti']]
                st.dataframe(df_s_display.sort_values('Punti', ascending=False), 
                             hide_index=True, 
                             column_config={"Posizione": st.column_config.Column(width="small"), "Punti": st.column_config.Column(help="Punti in classifica", width="medium")})
            else: st.info("Carica scontridiretti.csv")
        
        with cl2:
            st.markdown("#### 🎯 Punti Totali")
            if df_punti_tot is not None:
                df_punti_tot = pulisci_nomi(df_punti_tot, 'Giocatore')
                if 'Punti Totali' in df_punti_tot.columns:
                    df_punti_tot['Punti Totali'] = df_punti_tot['Punti Totali'].astype(str).str.replace(',', '.').astype(float)
                st.dataframe(df_punti_tot[['Posizione', 'Giocatore', 'Punti Totali', 'Media']].sort_values('Punti Totali', ascending=False), 
                             hide_index=True,
                             column_config={"Posizione": st.column_config.Column(width="small")})

    # --- TAB ECONOMIA ---
    with tabs[1]:
        st.markdown("#### 💰 Analisi Costi Rose")
        eco = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco.columns = ['Fantasquadra', 'Costo della Rosa']
        eco['Extra Febbraio'] = eco['Fantasquadra'].map(budgets_fisso).fillna(0)
        eco['Budget Totale'] = eco['Costo della Rosa'] + eco['Extra Febbraio']
        st.dataframe(eco.sort_values('Budget Totale', ascending=False), hide_index=True, use_container_width=True)

    # --- TAB STRATEGIA ---
    with tabs[2]:
        st.markdown("#### 📋 Distribuzione Ruoli")
        # Ordine ruoli richiesto
        ordine_ruoli = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
        pivot_count = df_rose.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
        
        # Riordino colonne se presenti
        colonne_presenti = [r for r in ordine_ruoli if r in pivot_count.columns]
        st.dataframe(pivot_count[colonne_presenti], use_container_width=True)

    # --- TAB ROSE ---
    with tabs[3]:
        sq_lista = sorted(df_rose['Fantasquadra'].unique())
        scelta_sq = st.selectbox("Seleziona Squadra:", sq_lista)
        df_sq = df_rose[df_rose['Fantasquadra'] == scelta_sq][['Ruolo', 'Nome', 'Prezzo']]
        
        # Tabella colorata in base al prezzo (Verde acceso per prezzi alti)
        st.dataframe(df_sq.style.background_gradient(subset=['Prezzo'], cmap='YlGn'), 
                     hide_index=True, use_container_width=True)

    # --- TAB VINCOLI (CORRETTA) ---
    with tabs[4]:
        st.markdown("#### 📅 Vincoli Stagione 2026/27")
        if df_vincoli is not None:
            # Pulizia per evitare duplicati sporchi nel CSV
            df_v_clean = df_vincoli[df_vincoli['Squadra'].notna() & ~df_vincoli['Squadra'].str.contains('\*|`|Riepilogo', na=False)].copy()
            df_v_clean = pulisci_nomi(df_v_clean, 'Squadra')
            
            # Selettore per evitare il tabellone unico gigante
            sq_v_lista = sorted(df_v_clean['Squadra'].unique())
            scelta_v = st.selectbox("Dettaglio vincoli per:", sq_v_lista)
            
            dettaglio = df_v_clean[df_v_clean['Squadra'] == scelta_v]
            st.dataframe(dettaglio[['Giocatore', 'Costo 2026-27']], hide_index=True, use_container_width=True)
            
            st.divider()
            st.write("**Riepilogo Impegni Futuri:**")
            riepilogo = df_v_clean.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            st.dataframe(riepilogo.sort_values('Costo 2026-27', ascending=False), hide_index=True)
        else:
            st.info("Carica il file dei vincoli per visualizzare i dettagli.")

else:
    st.info("👋 Carica i file CSV per generare i dati della lega.")
