import streamlit as st
import pandas as pd
import os

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Crediti Extra
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

def clean_and_filter(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "": return None
    return s_str.upper()

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# CARICAMENTO
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# ELABORAZIONE
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_and_filter).replace(map_n)
    f_rs = f_rs.dropna(subset=['Squadra_N'])
    f_rs['Prezzo_N'] = pd.to_numeric(f_rs['Prezzo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_and_filter).replace(map_n)
    f_vn = f_vn.dropna(subset=['Sq_N'])
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: 
        f_vn[c] = pd.to_numeric(f_vn[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn = f_vn.drop_duplicates(subset=['Sq_N', 'Giocatore'])

# TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

# ... (Parti Classifiche, Budget, Rose, Vincoli rimangono invariate come prima) ...
# [Le ometto qui per brevità ma sono incluse nella logica di caricamento sopra]

with t[4]: # SEZIONE SCAMBI
    if f_rs is not None:
        st.subheader("🔄 Simulatore Scambi")
        col_s1, col_s2 = st.columns(2)
        lista_sq = sorted(f_rs['Squadra_N'].unique())
        
        with col_s1:
            sq_a = st.selectbox("Squadra A", lista_sq, index=0)
            rosa_a = f_rs[f_rs['Squadra_N'] == sq_a]
            cessioni_a = st.multiselect(f"Giocatori in uscita da {sq_a}:", rosa_a['Nome'].tolist())
            val_uscita_a = rosa_a[rosa_a['Nome'].isin(cessioni_a)]['Prezzo_N'].sum()
            
        with col_s2:
            sq_b = st.selectbox("Squadra B", lista_sq, index=1)
            rosa_b = f_rs[f_rs['Squadra_N'] == sq_b]
            cessioni_b = st.multiselect(f"Giocatori in uscita da {sq_b}:", rosa_b['Nome'].tolist())
            val_uscita_b = rosa_b[rosa_b['Nome'].isin(cessioni_b)]['Prezzo_N'].sum()

        st.divider()
        st.write("### 📊 Impatto Economico")
        res1, res2 = st.columns(2)
        
        diff_a = val_uscita_a - val_uscita_b
        diff_b = val_uscita_b - val_uscita_a
        
        with res1:
            st.metric(f"Budget {sq_a}", f"{diff_a:g}", delta=diff_a, delta_color="normal")
            st.caption("Segno positivo = recuperi crediti. Segno negativo = spendi di più.")
        with res2:
            st.metric(f"Budget {sq_b}", f"{diff_b:g}", delta=diff_b, delta_color="normal")

# [Aggiungere qui il codice delle altre Tab per avere il file completo]
