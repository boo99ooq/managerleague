import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega Manageriale", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:10px; padding:5px;}</style>", unsafe_allow_html=True)

st.title("⚽ Centro Direzionale Fantalega")

# 2. BUDGET FISSI
budgets = {"GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5, "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5, "MATTEO": 166.5, "NICHOLAS": 113.0}

# 3. FUNZIONI
def get_df(nome_file):
    if os.path.exists(nome_file):
        try:
            df = pd.read_csv(nome_file, sep=',', encoding='utf-8-sig').dropna(how='all')
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            return None
    return None

def clean_n(df, c):
    if df is None or c not in df.columns: return df
    m = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[c] = df[c].astype(str).str.strip().str.upper().replace(m)
    return df

# 4. LETTURA DATI
f_sc = get_df("scontridiretti.csv")
f_pt = get_df("classificapunti.csv")
f_rs = get_df("rose_complete.csv")
f_vn = get_df("vincoli.csv")

# 5. APP
if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    t = st.tabs(["🏆 Classifica", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # ... [Le altre tab rimangono invariate] ...
    with t[0]:
        if f_sc is not None:
            st.write("🔥 **Scontri**")
            st.dataframe(clean_n(f_sc, 'Giocatore'), hide_index=True)

    if f_rs is not None:
        f_rs.columns = [c.lower() for c in f_rs.columns]
        f_rs = clean_n(f_rs, 'fantasquadra')
        col_prezzo = next((c for c in f_rs.columns if 'prezzo' in c), 'prezzo')
        f_rs[col_prezzo] = pd.to_numeric(f_rs[col_prezzo], errors='coerce').fillna(0).astype(int)

        with t[1]:
            st.write("💰 **Bilancio**")
            eco = f_rs.groupby('fantasquadra')[col_prezzo].sum().reset_index()
            eco['Extra'] = eco['fantasquadra'].map(budgets).fillna(0)
            eco['Totale'] = (eco[col_prezzo] + eco['Extra']).astype(int)
            st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=True)

        with t[2]:
            st.write("🧠 **Strategia**")
            cx, cy = st.columns([1.5, 1])
            with cx:
                col_ruolo = next((c for c in f_rs.columns if 'ruolo' in c), 'ruolo')
                col_nome = next((c for c in f_rs.columns if 'nome' in c), 'nome')
                f_rs[col_ruolo] = f_rs[col_ruolo].replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
                piv = f_rs.pivot_table(index='fantasquadra', columns=col_ruolo, values=col_nome, aggfunc='count').fillna(0).astype(int)
                st.dataframe(piv, use_container_width=True)
            with cy:
                top = f_rs.loc[f_rs.groupby('fantasquadra')[col_prezzo].idxmax()].sort_values(col_prezzo, ascending=False)
                st.write("**💎 Top Player**")
                st.dataframe(top[['fantasquadra',col_nome,col_prezzo]], hide_index=True)

        with t[3]:
            sq = st.selectbox("Squadra:", sorted(f_rs['fantasquadra'].unique()))
            col_nome = next((c for c in f_rs.columns if 'nome' in c), 'nome')
            df_sq = f_rs[f_rs['fantasquadra'] == sq].sort_values(col_prezzo, ascending=False)
            st.dataframe(df_sq[['ruolo', col_nome, col_prezzo]].style.background_gradient(subset=[col_nome, col_prezzo], cmap='Greens', gmap=df_sq[col_prezzo]), hide_index=True, use_container_width=True)

    # --- TAB VINCOLI MODIFICATA ---
    if f_vn is not None:
        with t[4]:
            st.write("📅 **Vincoli**")
            f_vn = clean_n(f_vn[f_vn['Squadra'].notna() & ~f_vn['Squadra'].str.contains(r'\*|Riepilogo')].copy(), 'Squadra')
            f_vn['Costo 2026-27'] = f_vn['Costo 2026-27'].astype(str).str.replace(',','.').apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            
            vx, vy = st.columns([1, 2])
            with vx:
                st.write("**Totale Debiti**")
                deb = f_vn.groupby('Squadra')['Costo 2026-27'].sum().reset_index().sort_values('Costo 2026-27', ascending=False)
                st.dataframe(deb, hide_index=True)
            
            with vy:
                sv = st.selectbox("Dettaglio Giocatori:", sorted(f_vn['Squadra'].unique()), key="vinc_sel")
                # Filtro i dati e seleziono SOLO le colonne richieste
                df_v = f_vn[f_vn['Squadra'] == sv][['Giocatore', 'Costo 2026-27', 'Durata (anni)']].copy()
                df_v['Durata (anni)'] = pd.to_numeric(df_v['Durata (anni)'], errors='coerce').fillna(0).astype(int)
                
                # Visualizzazione pulita
                st.dataframe(
                    df_v.sort_values('Durata (anni)', ascending=False).style.map(
                        lambda x: 'background-color: #ffcdd2' if x == 1 else '', subset=['Durata (anni)']
                    ), 
                    hide_index=True, 
                    use_container_width=True
                )
else:
    st.warning("⚠️ Nessun dato trovato. Carica i file CSV su GitHub.")
