import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

# Configurazione Budget Extra
bg_extra = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 2. FUNZIONE CARICAMENTO UNIVERSALE
def load_data(name):
    for f in os.listdir("."):
        if f.lower() == name.lower():
            try:
                # Legge qualsiasi separatore (, o ;)
                df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
                df.columns = df.columns.str.strip()
                return df
            except:
                return None
    return None

def style_df(df):
    return df.style.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

# 3. LETTURA FILE
f_sc = load_data("scontridiretti.csv")
f_pt = load_data("classificapunti.csv")
f_rs = load_data("rose_complete.csv")
f_vn = load_data("vincoli.csv")

# 4. LOGICA TAB
tabs_list = []
if f_sc is not None or f_pt is not None: tabs_list.append("🏆 Classifiche")
if f_rs is not None: tabs_list.extend(["💰 Budget", "🧠 Strategia", "🏃 Rose"])
if f_vn is not None: tabs_list.append("📅 Vincoli")

if tabs_list:
    t = st.tabs(tabs_list)
    curr = 0

    # --- TAB CLASSIFICHE ---
    if f_sc is not None or f_pt is not None:
        with t[curr]:
            c1, c2 = st.columns(2)
            if f_sc is not None:
                with c1:
                    st.subheader("🔥 Scontri Diretti")
                    st.dataframe(style_df(f_sc), hide_index=True, use_container_width=True)
            if f_pt is not None:
                with c2:
                    st.subheader("🎯 Classifica Punti")
                    st.dataframe(style_df(f_pt), hide_index=True, use_container_width=True)
        curr += 1

    # --- TAB ROSE (Budget, Strategia, Rose) ---
    if f_rs is not None:
        # Usa le posizioni per evitare errori di nome colonna
        # Assumiamo: 0:Squadra, 1:Nome, 2:Ruolo, Ultima:Prezzo
        c = f_rs.columns
        f_rs[c[-1]] = pd.to_numeric(f_rs[c[-1]].astype(str).str.replace(',','.'), errors='coerce').fillna(0)

        with t[curr]: # Budget
            st.subheader("💰 Bilancio Crediti")
            spesa = f_rs.groupby(c[0])[c[-1]].sum().reset_index()
            spesa['Extra'] = spesa[c[0]].str.upper().map(bg_extra).fillna(0)
            spesa['Totale'] = (spesa[c[-1]] + spesa['Extra']).astype(int)
            st.dataframe(style_df(spesa.sort_values('Totale', ascending=False)), hide_index=True, use_container_width=True)
        
        with t[curr+1]: # Strategia
            st.subheader("🧠 Distribuzione Ruoli")
            f_rs[c[2]] = f_rs[c[2]].replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
            pivot = f_rs.pivot_table(index=c[0], columns=c[2], values=c[1], aggfunc='count').fillna(0).astype(int)
            st.dataframe(style_df(pivot), use_container_width=True)

        with t[curr+2]: # Rose
            st.subheader("🏃 Rose Squadre")
            sel_sq = st.selectbox("Scegli Squadra:", sorted(f_rs[c[0]].unique()))
            rosa = f_rs[f_rs[c[0]] == sel_sq][[c[2], c[1], c[-1]]].sort_values(c[-1], ascending=False)
            st.dataframe(style_df(rosa.style.background_gradient(subset=[c[-1]], cmap='Greens')), hide_index=True, use_container_width=True)
        curr += 3

    # --- TAB VINCOLI (Layout richiesto e rinforzato) ---
    if f_vn is not None:
        with t[curr]:
            st.subheader("📅 Gestione Vincoli")
            v = f_vn.columns
            # 0:Squadra, 1:Giocatore, 2:Costo, 3:Anni (o ultima)
            f_vn[v[2]] = pd.to_numeric(f_vn[v[2]].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
            f_vn[v[-1]] = pd.to_numeric(f_vn[v[-1]], errors='coerce').fillna(0).astype(int)

            v_c1, v_c2 = st.columns([1, 2])
            with v_c1:
                st.write("**Crediti Impegnati**")
                debiti = f_vn.groupby(v[0])[v[2]].sum().reset_index().sort_values(v[2], ascending=False)
                st.dataframe(style_df(debiti), hide_index=True, use_container_width=True)
            
            with v_c2:
                st.write("**Dettaglio Giocatori**")
                sel_v = st.selectbox("Squadra:", sorted(f_vn[v[0]].unique()), key="v_sel_box")
                det = f_vn[f_vn[v[0]] == sel_v][[v[1], v[2], v[-1]]].copy()
                # Rosso se scade tra 1 anno
                styled_v = det.sort_values(v[-1]).style.map(lambda x: 'background-color: #ffcdd2' if x == 1 else '', subset=[v[-1]])
                st.dataframe(style_c_extra(styled_v), hide_index=True, use_container_width=True)

else:
    st.warning("⚠️ Nessun file CSV rilevato. Controlla che i nomi dei file su GitHub siano corretti.")

# Funzione extra per centrare gli stili condizionali
def style_c_extra(styler):
    return styler.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
