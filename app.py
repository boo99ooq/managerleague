import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:10px; padding:5px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

# 2. BUDGET
budgets = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 3. FUNZIONI
def get_df(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', encoding='utf-8-sig').dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except: return None

def clean_n(df, c):
    if df is None or c not in df.columns: return df
    m = {"NICO FABIO":"NICHOLAS","NICHO":"NICHOLAS","DANI ROBI":"DANI ROBI","MATTEO STEFANO":"MATTEO"}
    df[c] = df[c].astype(str).str.strip().str.upper().replace(m)
    return df

def style_c(df):
    return df.style.set_properties(**{'text-align':'center'}).set_table_styles([dict(selector='th', props=[('text-align','center')])])

# 4. CARICAMENTO
f_sc, f_pt, f_rs, f_vn = get_df("scontridiretti.csv"), get_df("classificapunti.csv"), get_df("rose_complete.csv"), get_df("vincoli.csv")

# 5. APP
if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    t = st.tabs(["🏆 Classifica", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    with t[0]:
        c1, c2 = st.columns(2)
        if f_sc is not None:
            with c1: 
                st.write("🔥 **Scontri**")
                st.dataframe(style_c(clean_n(f_sc, 'Giocatore')), hide_index=True, use_container_width=True)
        if f_pt is not None:
            with c2:
                st.write("🎯 **Punti**")
                df_pt = clean_n(f_pt, 'Giocatore')
                for col in ['Punti Totali', 'Media']:
                    if col in df_pt.columns:
                        df_pt[col] = df_pt[col].astype(str).str.replace(',','.')
                        df_pt[col] = pd.to_numeric(df_pt[col], errors='coerce')
                st.dataframe(style_c(df_pt[['Posizione','Giocatore','Punti Totali','Media']]), hide_index=True, use_container_width=True)

    if f_rs is not None:
        cs = f_rs.columns
        if len(cs) >= 4:
            f_c, n_c, r_c, p_c = cs[0], cs[1], cs[2], cs[-1]
            f_rs = clean_n(f_rs, f_c)
            f_rs[p_c] = pd.to_numeric(f_rs[p_c], errors='coerce').fillna(0).astype(int)
            
            with t[1]:
                st.write("💰 **Bilancio**")
                eco = f_rs.groupby(f_c)[p_c].sum().reset_index()
                eco['Extra'] = eco[f_c].map(budgets).fillna(0)
                eco['Totale'] = (eco[p_c] + eco['Extra']).astype(int)
                st.dataframe(style_c(eco.sort_values('Totale', ascending=False)), hide_index=True, use_container_width=True)
            with t[2]:
                st.write("🧠 **Strategia**")
                f_rs[r_c] = f_rs[r_c].replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
                piv = f_rs.pivot_table(index=f_c, columns=r_c, values=n_c, aggfunc='count').fillna(0).astype(int)
                st.dataframe(style_c(piv), use_container_width=True)
            with t[3]:
                sq = st.selectbox("Squadra:", sorted(f_rs[f_c].unique()))
                df_sq = f_rs[f_rs[f_c] == sq][[r_c, n_c, p_c]].sort_values(p_c, ascending=False)
                st.dataframe(style_c(df_sq.style.background_gradient(subset=[n_c, p_c], cmap='Greens', gmap=df_sq[p_c])), hide_index=True, use_container_width=True)
        else:
            st.error("Il file rose_complete.csv deve avere almeno 4 colonne: Squadra, Nome, Ruolo, Prezzo.")

    if f_vn is not None:
        with t[4]:
            st.write("📅 **Vincoli**")
            v_cs = f_vn.columns
            if len(v_cs) >= 3:
                sv, gv, cv, dv = v_cs[0], v_cs[1], v_cs[2], v_cs[-1]
                f_vn = clean_n(f_vn[f_vn[sv].notna() & ~f_vn[sv].str.contains(r'\*|Riepilogo')].copy(), sv)
                f_vn[cv] = f_vn[cv].astype(str).str.replace(',','.').apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
                
                vx, vy = st.columns([1, 2])
                with vx:
                    deb = f_vn.groupby(sv)[cv].sum().reset_index().sort_values(cv, ascending=False)
                    st.dataframe(style_c(deb), hide_index=True, use_container_width=True)
                with vy:
                    sel = st.selectbox("Dettaglio:", sorted(f_vn[sv].unique()), key="vsel")
                    df_v = f_vn[f_vn[sv] == sel][[gv, cv, dv]].copy()
                    df_v[dv] = pd.to_numeric(df_v[dv], errors='coerce').fillna(0).astype(int)
                    st.dataframe(style_c(df_v.sort_values(dv, ascending=False).style.map(lambda x: 'background-color: #ffcdd2' if x == 1 else '', subset=[dv])), hide_index=True, use_container_width=True)
            else:
                st.error("Il file vincoli.csv deve avere almeno 3 colonne.")
else:
    st.info("👋 Carica i CSV su GitHub.")
