import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:10px; padding:5px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

# 2. BUDGET FISSI
budgets = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 3. FUNZIONI DI RICERCA FILE
def find_file(target):
    """Cerca un file nella cartella ignorando maiuscole/minuscole"""
    all_files = os.listdir(".")
    for f in all_files:
        if f.lower() == target.lower():
            return f
    return None

def get_df(target_name):
    actual_file = find_file(target_name)
    if not actual_file: return None
    try:
        df = pd.read_csv(actual_file, sep=',', encoding='utf-8-sig').dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except: return None

def style_c(obj):
    s = obj.style if isinstance(obj, pd.DataFrame) else obj
    return s.set_properties(**{'text-align':'center'}).set_table_styles([dict(selector='th', props=[('text-align','center')])])

# 4. CARICAMENTO DATI
f_sc = get_df("scontridiretti.csv")
f_pt = get_df("classificapunti.csv")
f_rs = get_df("rose_complete.csv")
f_vn = get_df("vincoli.csv")

# 5. SIDEBAR STATUS
st.sidebar.header("🔍 Verifica File")
st.sidebar.write("Scontri:", "✅" if f_sc is not None else "❌")
st.sidebar.write("Punti:", "✅" if f_pt is not None else "❌")
st.sidebar.write("Rose:", "✅" if f_rs is not None else "❌")
st.sidebar.write("Vincoli:", "✅" if f_vn is not None else "❌")

# 6. COSTRUZIONE INTERFACCIA
if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    tabs_to_show = []
    if f_sc is not None or f_pt is not None: tabs_to_show.append("🏆 Classifiche")
    if f_rs is not None: 
        tabs_to_show.extend(["💰 Budget", "🧠 Strategia", "🏃 Rose"])
    if f_vn is not None: tabs_to_show.append("📅 Vincoli")
    
    t = st.tabs(tabs_to_show)
    idx = 0

    # TAB CLASSIFICHE
    if f_sc is not None or f_pt is not None:
        with t[idx]:
            c1, c2 = st.columns(2)
            if f_sc is not None:
                with c1:
                    st.write("🔥 **Scontri Diretti**")
                    st.dataframe(style_c(f_sc), hide_index=True, use_container_width=True)
            if f_pt is not None:
                with c2:
                    st.write("🎯 **Classifica Punti**")
                    for col in ['Punti Totali', 'Media']:
                        if col in f_pt.columns:
                            f_pt[col] = f_pt[col].astype(str).str.replace(',','.').apply(pd.to_numeric, errors='coerce')
                    st.dataframe(style_c(f_pt[['Posizione','Giocatore','Punti Totali','Media']]), hide_index=True, use_container_width=True)
        idx += 1

    # TAB ROSE E BUDGET
    if f_rs is not None:
        cs = f_rs.columns
        f_c, n_c, r_c, p_c = cs[0], cs[1], cs[2], cs[-1]
        f_rs[p_c] = pd.to_numeric(f_rs[p_c], errors='coerce').fillna(0).astype(int)
        
        # Budget
        with t[idx]:
            st.write("💰 **Situazione Crediti**")
            eco = f_rs.groupby(f_c)[p_c].sum().reset_index()
            eco['Extra'] = eco[f_c].str.upper().map(budgets).fillna(0)
            eco['Totale'] = (eco[p_c] + eco['Extra']).astype(int)
            st.dataframe(style_c(eco.sort_values('Totale', ascending=False)), hide_index=True, use_container_width=True)
        
        # Strategia
        with t[idx+1]:
            st.write("🧠 **Analisi Ruoli**")
            f_rs[r_c] = f_rs[r_c].replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
            piv = f_rs.pivot_table(index=f_c, columns=r_c, values=n_c, aggfunc='count').fillna(0).astype(int)
            st.dataframe(style_c(piv), use_container_width=True)
            
        # Rose
        with t[idx+2]:
            st.write("🏃 **Rose Squadre**")
            sq = st.selectbox("Seleziona Squadra:", sorted(f_rs[f_c].unique()))
            df_sq = f_rs[f_rs[f_c] == sq][[r_c, n_c, p_c]].sort_values(p_c, ascending=False)
            st.dataframe(style_c(df_sq.style.background_gradient(subset=[p_c], cmap='Greens')), hide_index=True, use_container_width=True)
        idx += 3

    # TAB VINCOLI
    if f_vn is not None:
        with t[idx]:
            st.write("📅 **Situazione Vincoli**")
            v_cs = f_vn.columns
            sv, gv, cv, dv = v_cs[0], v_cs[1], v_cs[2], v_cs[-1]
            f_vn[cv] = f_vn[cv].astype(str).str.replace(',','.').apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            vx, vy = st.columns([1, 2])
            with vx:
                st.write("**Riepilogo Debiti**")
                st.dataframe(style_c(f_vn.groupby(sv)[cv].sum().reset_index().sort_values(cv, ascending=False)), hide_index=True, use_container_width=True)
            with vy:
                sel = st.selectbox("Dettaglio:", sorted(f_vn[sv].unique()), key="vsel")
                df_v = f_vn[f_vn[sv] == sel][[gv, cv, dv]].copy()
                df_v[dv] = pd.to_numeric(df_v[dv], errors='coerce').fillna(0).astype(int)
                st.dataframe(style_c(df_v.sort_values(dv, ascending=False).style.map(lambda x: 'background-color: #ffcdd2' if x == 1 else '', subset=[dv])), hide_index=True, use_container_width=True)
else:
    st.warning("⚠️ Non trovo i file CSV. Assicurati che siano
