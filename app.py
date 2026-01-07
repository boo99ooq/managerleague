import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

bg_extra = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 2. CARICAMENTO ROBUSTO
def load_data(name):
    actual_file = next((f for f in os.listdir(".") if f.lower() == name.lower()), None)
    if actual_file:
        try:
            # Prova a leggere il file tentando vari separatori
            df = pd.read_csv(actual_file, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except: return None
    return None

def style_df(obj):
    styler = obj if hasattr(obj, 'style') == False else obj.style
    return styler.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

# 3. LETTURA
f_sc, f_pt, f_rs, f_vn = load_data("scontridiretti.csv"), load_data("classificapunti.csv"), load_data("rose_complete.csv"), load_data("vincoli.csv")

# 4. TAB
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

# --- CLASSIFICHE ---
with t[0]:
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1: st.subheader("🔥 Scontri"); st.dataframe(style_df(f_sc), hide_index=True, use_container_width=True)
    if f_pt is not None:
        with c2: st.subheader("🎯 Punti"); st.dataframe(style_df(f_pt), hide_index=True, use_container_width=True)

# --- LOGICA ROSE (Budget, Strategia, Rose) ---
if f_rs is not None and len(f_rs.columns) >= 3:
    # Usiamo le posizioni: 0=Squadra, 1=Giocatore, 2=Ruolo, Ultima=Prezzo
    cols = f_rs.columns
    f_rs[cols[-1]] = pd.to_numeric(f_rs[cols[-1]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
    
    with t[1]: # BUDGET
        st.subheader("💰 Bilancio Crediti")
        eco = f_rs.groupby(cols[0])[cols[-1]].sum().reset_index()
        # Normalizziamo il nome per il match con il dizionario budget
        eco['Extra'] = eco[cols[0]].str.strip().str.upper().map(bg_extra).fillna(0)
        eco['Totale'] = (eco[cols[-1]] + eco['Extra']).astype(int)
        st.dataframe(style_df(eco.sort_values('Totale', ascending=False)), hide_index=True, use_container_width=True)
    
    with t[2]: # STRATEGIA
        st.subheader("🧠 Distribuzione Ruoli")
        df_strat = f_rs.copy()
        df_strat[cols[2]] = df_strat[cols[2]].astype(str).str.upper().replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
        piv = df_strat.pivot_table(index=cols[0], columns=cols[2], values=cols[1], aggfunc='count').fillna(0).astype(int)
        st.dataframe(style_df(piv), use_container_width=True)

    with t[3]: # ROSE
        st.subheader("🏃 Rose Squadre")
        squadre = sorted(f_rs[cols[0]].unique())
        sq = st.selectbox("Seleziona Squadra:", squadre)
        df_sq = f_rs[f_rs[cols[0]] == sq][[cols[2], cols[1], cols[-1]]].sort_values(cols[-1], ascending=False)
        st_color = df_sq.style.background_gradient(subset=[cols[-1]], cmap='Greens')
        st.dataframe(style_df(st_color), hide_index=True, use_container_width=True)

# --- VINCOLI ---
if f_vn is not None and len(f_vn.columns) >= 3:
    with t[4]:
        st.subheader("📅 Gestione Vincoli")
        vc = f_vn.columns # 0:Squadra, 1:Giocatore, 2:Costo, 3:Anni
        f_vn[vc[2]] = pd.to_numeric(f_vn[vc[2]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
        
        v1, v2 = st.columns([1, 2])
        with v1:
            st.write("**Crediti Impegnati**")
            deb = f_vn.groupby(vc[0])[vc[2]].sum().reset_index().sort_values(vc[2], ascending=False)
            st.dataframe(style_df(deb), hide_index=True, use_container_width=True)
        with v2:
            st.write("**Dettaglio Giocatori**")
            sq_v = st.selectbox("Squadra:", sorted(f_vn[vc[0]].unique()), key="v_sel")
            det = f_vn[f_vn[vc[0]] == sq_v][[vc[1], vc[2], vc[-1]]].copy()
            det[vc[-1]] = pd.to_
