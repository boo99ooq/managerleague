import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE: VERDE PRATO CHIARO
def apply_custom_style():
    st.markdown(
        """
        <style>
        .stApp { background-color: #e8f5e9; }
        [data-testid="stSidebar"] { background-color: #c8e6c9 !important; }
        h1, h2, h3, h4, h5, p, label, span { color: #1b5e20 !important; font-family: 'Segoe UI', sans-serif; }
        h1 { text-align: center; font-weight: 800; color: #2e7d32 !important; }
        .stTabs, .stDataFrame, .stTable {
            background-color: #ffffff !important;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
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

# 4. SIDEBAR PER CARICAMENTO
st.sidebar.header("📂 Database Lega")
f_scontri = st.sidebar.file_uploader("1. Classifica Scontri", type="csv")
f_punti = st.sidebar.file_uploader("2. Classifica Punti", type="csv")
f_rose = st.sidebar.file_uploader("3. Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("4. Vincoli 2026/27", type="csv")

# Funzioni di supporto
def pulisci_nomi(df, col):
    if df is None or col not in df.columns: return df
    mappa = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[col] = df[col].astype(str).str.strip().str.upper().replace(mappa)
    return df

def carica_csv(file):
    if file is None: return None
    try:
        file.seek(0)
        df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except: return None

df_scontri = carica_csv(f_scontri)
df_punti_tot = carica_csv(f_punti)
df_rose = carica_csv(f_rose)
df_vincoli = carica_csv(f_vinc)

# 5. LOGICA APPLICAZIONE
if any([df_scontri is not None, df_punti_tot is not None, df_rose is not None, df_vincoli is not None]):
    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # --- TAB CLASSIFICHE ---
    with tabs[0]:
        cl1, cl2 = st.columns(2)
        with cl1:
            st.subheader("🔥 Scontri Diretti")
            if df_scontri is not None:
                df_scontri = pulisci_nomi(df_scontri, 'Giocatore')
                cols_s = ['Posizione', 'Giocatore', 'Punti', 'Gol Fatti', 'Gol Subiti', 'Differenza Reti']
                st.dataframe(df_scontri[cols_s].sort_values('Punti', ascending=False), hide_index=True, use_container_width=True)
            else: st.info("Carica 'scontridiretti.csv'")
        with cl2:
            st.subheader("🎯 Punti Totali")
            if df_punti_tot is not None:
                df_punti_tot = pulisci_nomi(df_punti_tot, 'Giocatore')
                # FIX VIRGOLA: Trasformiamo "1074,5" in 1074.5 per i calcoli
                for col_p in ['Punti Totali', 'Media', 'Distacco']:
                    if col_p in df_punti_tot.columns:
                        df_punti_tot[col_p] = df_punti_tot[col_p].astype(str).str.replace(',', '.').astype(float)
                st.dataframe(df_punti_tot[['Posizione', 'Giocatore', 'Punti Totali', 'Media']], hide_index=True, use_container_width=True)
            else: st.info("Carica 'classificapunti.csv'")

    # --- TAB ECONOMIA ---
    with tabs[1]:
        st.subheader("💰 Bilancio Rose")
        if df_rose is not None:
            c_map = {c.lower(): c for c in df_rose.columns}
            f_col = c_map.get('fantasquadra', df_rose.columns[0])
            p_col = c_map.get('prezzo', df_rose.columns[-1])
            df_rose = pulisci_nomi(df_rose, f_col)
            eco = df_rose.groupby(f_col)[p_col].sum().reset_index()
            eco.columns = ['Fantasquadra', 'Costo della Rosa']
            eco['Costo della Rosa'] = eco['Costo della Rosa'].astype(int)
            eco['Extra Febbraio'] = eco['Fantasquadra'].map(budgets_fisso).fillna(0)
            eco['Budget Totale'] = (eco['Costo della Rosa'] + eco['Extra Febbraio']).astype(int)
            st.dataframe(eco.sort_values('Budget Totale', ascending=False), hide_index=True, use_container_width=True)
        else: st.warning("Carica il file delle Rose.")

    # --- TAB STRATEGIA ---
    with tabs[2]:
        st.subheader("📋 Analisi Strategica")
        if df_rose is not None:
            c1, c2 = st.columns([1.5, 1])
            c_map = {c.lower(): c for c in df_rose.columns}
            f_col = c_map.get('fantasquadra', df_rose.columns[0])
            n_col = c_map.get('nome', df_rose.columns[1])
            p_col = c_map.get('prezzo', df_rose.columns[-1])
            r_col = c_map.get('ruolo', 'Ruolo')
            with c1:
                st.write("**Distribuzione Ruoli:**")
                ord_r = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
                pivot = df_rose.pivot_table(index=f_col, columns=r_col, values=n_col, aggfunc='count').fillna(0).astype(int)
                col_p = [r for r in ord_r if r in pivot.columns]
                st.dataframe(pivot[col_p], use_container_width=True)
            with c2:
                st.write("**💎 Top Player per Squadra:**")
                df_rose[p_col] = pd.to_numeric(df_rose[p_col], errors='coerce').fillna(0).astype(int)
                idx_m = df_rose.groupby(f_col)[p_col].idxmax()
                st.dataframe(df_rose.loc[idx_m, [f_col, n_col, p_col]].sort_values(p_col, ascending=False), hide_index=True, use_container_width=True)

    # --- TAB ROSE ---
    with tabs[3]:
        if df_rose is not None:
            c_map = {c.lower(): c for c in df_rose.columns}
            f_col = c_map.get('fantasquadra', df_rose.columns[0])
            n_col = c_map.get('nome', df_rose.columns[1])
            p_col = c_map.get('prezzo', df_rose.columns[-1])
            r_col = c_map.get('ruolo', 'Ruolo')
            sq = sorted(df_rose[f_col].unique())
            scelta = st.selectbox("Seleziona Squadra:", sq)
            d_sq = df_rose[df_rose[f_col] == scelta][[r_col, n_col, p_col]].copy()
            d_sq[p_col] = d_sq[p_col].astype(int)
            st.dataframe(d_sq.sort_values(p_col, ascending=False).style.background_gradient(subset=[n_col, p_col], cmap='Greens'), hide_index=True, use_container_width=True)

    # --- TAB VINCOLI ---
    with tabs[4]:
        st.subheader("📅 Contratti Futuri")
        if df_vincoli is not None:
            df_v = df_vincoli.copy()
            df_v = df_v[df_v['Squadra'].notna() & ~df_v['Squadra'].str.contains(r'\*|`|Riepilogo', na=False)]
            df_v = pulisci_nomi(df_v, 'Squadra')
            cv1, cv2 = st.columns([1, 2])
            with cv1:
                st.write("**Riepilogo Debiti:**")
                rip = df_v.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
                rip['Costo 2026-27'] = rip['Costo 2026-27'].astype(int)
                st.dataframe(rip.sort_values('Costo 2026-27', ascending=False), hide_index=True)
            with cv2:
                sv = st.selectbox("Dettaglio di:", sorted(df_v['Squadra'].unique()))
                st.dataframe(df_v[df_v['Squadra'] == sv][['Giocatore', 'Costo 2026-27']], hide_index=True, use_container_width=True)
else:
    st.info("👋 Carica i file CSV nella barra laterale per attivare i cruscotti.")
