import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE E STILE
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

def apply_style():
    st.markdown("""
        <style>
        .stApp { background-color: #e8f5e9; }
        [data-testid="stSidebar"] { background-color: #c8e6c9 !important; }
        h1, h2, h3, h4, h5, p, label, span { color: #1b5e20 !important; font-family: 'Segoe UI', sans-serif; }
        h1 { text-align: center; font-weight: 800; color: #2e7d32 !important; padding-bottom: 20px; }
        .stTabs, .stDataFrame, .stTable {
            background-color: #ffffff !important;
            padding: 10px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

apply_style()
st.title("⚽ Centro Direzionale Fantalega")

# 2. DATI FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 3. CARICAMENTO SIDEBAR
st.sidebar.header("📂 Database Lega")
f_scontri = st.sidebar.file_uploader("1. Scontri Diretti", type="csv")
f_punti = st.sidebar.file_uploader("2. Punti Totali", type="csv")
f_rose = st.sidebar.file_uploader("3. Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("4. Vincoli 26/27", type="csv")

def pulisci_nomi(df, col):
    if df is None or col not in df.columns: return df
    mappa = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[col] = df[col].astype(str).str.strip().str.upper().replace(mappa)
    return df

def carica(f):
    if f is None: return None
    try:
        df = pd.read_csv(f, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    except: return None

d_sc = carica(f_scontri)
d_pt = carica(f_punti)
d_rs = carica(f_rose)
d_vn = carica(f_vinc)

# 4. LOGICA TAB
if any([d_sc is not None, d_pt is not None, d_rs is not None, d_vn is not None]):
    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # --- TAB CLASSIFICHE ---
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Scontri Diretti")
            if d_sc is not None:
                d_sc = pulisci_nomi(d_sc, 'Giocatore')
                st.dataframe(d_sc, hide_index=True, use_container_width=True)
            else: st.info("Carica 'scontridiretti.csv'")
        with c2:
            st.subheader("🎯 Punti Totali")
            if d_pt is not None:
                d_pt = pulisci_nomi(d_pt, 'Giocatore')
                for c in ['Punti Totali', 'Media', 'Distacco']:
                    if c in d_pt.columns:
                        d_pt[c] = d_pt[c].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce').fillna(0)
                st.dataframe(d_pt[['Posizione', 'Giocatore', 'Punti Totali', 'Media']], hide_index=True, use_container_width=True)
            else: st.info("Carica 'classificapunti.csv'")

    # --- TAB ECONOMIA ---
    with tabs[1]:
        st.subheader("💰 Bilancio Rose")
        if d_rs is not None:
            # Identificazione Colonne Rose
            f_col = next((c for c in d_rs.columns if 'fantasquadra' in c.lower()), d_rs.columns[0])
            p_col = next((c for c in d_rs.columns if 'prezzo' in c.lower()), d_rs.columns[-1])
            d_rs = pulisci_nomi(d_rs, f_col)
            d_rs[p_col] = pd.to_numeric(d_rs[p_col], errors='coerce').fillna(0)
            
            eco = d_rs.groupby(f_col)[p_col].sum().reset_index()
            eco.columns = ['Fantasquadra', 'Costo Rosa']
            eco['Extra'] = eco['Fantasquadra'].map(budgets_fisso).fillna(0)
            eco['Totale'] = (eco['Costo Rosa'] + eco['Extra']).astype(int)
            st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
        else: st.info("Carica il file delle Rose.")

    # --- TAB STRATEGIA ---
    with tabs[2]:
        st.subheader("📋 Analisi Strategica")
        if d_rs is not None:
            cx, cy = st.columns([1.5, 1])
            f_col = next((c for c in d_rs.columns if 'fantasquadra' in c.lower()), d_rs.columns[0])
            n_col = next((c for c in d_rs.columns if 'nome' in c.lower()), d_rs.columns[1])
            p_col = next((c for c in d_rs.columns if 'prezzo' in c.lower()), d_rs.columns[-1])
            r_col = next((c for c in d_rs.columns if 'ruolo' in c.lower()), 'Ruolo')
            
            with cx:
                st.write("**Distribuzione Ruoli:**")
                ord_r = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
                piv = d_rs.pivot_table(index=f_col, columns=r_col, values=n_col, aggfunc='count').fillna(0).astype(int)
                st.dataframe(piv[[r for r in ord_r if r in piv.columns]], use_container_width=True)
            with cy:
                st.write("**💎 Top Player:**")
                idx = d_rs.groupby(f_col)[p_col].idxmax()
                st.dataframe(d_rs.loc[idx, [f_col, n_col, p_col]].sort_values(p_col, ascending=False), hide_index=True)
        else: st.info("Carica il file delle Rose.")

    # --- TAB ROSE ---
    with tabs[3]:
        st.subheader("🏃 Dettaglio Rose")
        if d_rs is not None:
            f_col = next((c for c in d_rs.columns if 'fantasquadra' in c.lower()), d_rs.columns[0])
            n_col = next((c for c in d_rs.columns if 'nome' in c.lower()), d_rs.columns[1])
            p_col = next((c for c in d_rs.columns if 'prezzo' in c.lower()), d_rs.columns[-1])
            r_col = next((c for c in d_rs.columns if 'ruolo' in c.lower()), 'Ruolo')
            
            sq = st.selectbox("Seleziona Squadra:", sorted(d_rs[f_col].unique()))
            df_sq = d_rs[d_rs[f_col] == sq][[r_col, n_col, p_col]].copy()
            df_sq[p_col] = df_sq[p_col].astype(int)
            df_sq_sorted = df_sq.sort_values(p_col, ascending=False)
            st.dataframe(df_sq_sorted.style.background_gradient(subset=[n_col, p_col], cmap='Greens', gmap=df_sq_sorted[p_col]), hide_index=True, use_container_width=True)
        else: st.info("Carica il file delle Rose.")

    # --- TAB VINCOLI ---
    with tabs[4]:
        st.subheader("📅 Contratti Futuri")
        if d_vn is not None:
            d_vn = d_vn[d_vn['Squadra'].notna() & ~d_vn['Squadra'].str.contains(r'\*|`|Riepilogo', na=False)].copy()
            d_vn = pulisci_nomi(d_vn, 'Squadra')
            vx, vy = st.columns([1, 2])
            with vx:
                st.write("**Riepilogo Debiti:**")
                c_futuro = 'Costo 2026-27'
                if c_futuro in d_vn.columns:
                    d_vn[c_futuro] = d_vn[c_futuro].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce').fillna(0).astype(int)
                    st.dataframe(d_vn.groupby('Squadra')[c_futuro].sum().reset_index().sort_values(c_futuro, ascending=False), hide_index=True)
            with vy:
                s_v = st.selectbox("Dettaglio vincoli di:", sorted(d_vn['Squadra'].unique()))
                st.dataframe(d_vn[d_vn['Squadra'] == s_v][['Giocatore', c_futuro]], hide_index=True, use_container_width=True)
        else: st.info("Carica il file dei Vincoli.")
else:
    st.info("👋 Benvenuto! Carica i file CSV dalla barra laterale per visualizzare i dati.")
