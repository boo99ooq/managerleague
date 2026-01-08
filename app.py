import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS STYLE
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 2px solid; }
    .error-box { background-color: #ffebee; border-color: #c62828; color: #c62828; }
    .warning-box { background-color: #fff3e0; border-color: #ef6c00; color: #ef6c00; }
    .search-card { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #1a73e8; margin-bottom: 8px; color: black; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE DI PULIZIA E MAPPATURA ---
def super_clean_v4(name):
    if not isinstance(name, str): return ""
    # Gestione caratteri sporchi da encoding
    name = name.replace('Ã’', 'O').replace('Ãˆ', 'E').replace('Ã ', 'A').replace('Ã¨', 'E')
    # Normalizzazione standard
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    # Mappatura manuale nomi critici
    mapping = {
        'MONTIPO': 'MONTIPO', 'MARTINELLI T': 'MARTINELLI', 'GABRIEL': 'TIAGOGABRIEL',
        'GUDMUNDSSON': 'AGUDMUNDSSON', 'NICO PAZ': 'NPAZ', 'KONE M (S)': 'IKONE',
        'SUCIC': 'PSUCIC', 'TOURE E': 'TOURE', 'BERNABE': 'BERNABE',
        'BERISHA E': 'MBERISHA', 'SORENSEN J': 'OSORENSEN', 'SOULE': 'SOULE',
        'THURAM M': 'THURAM', 'LAURIENTE': 'LAURIENTE', 'CASTELLANOS': 'CASTELLANOS',
        'RODRIGUEZ J': 'JERODRIGUEZ', 'NDRI': 'AKINSANMIRO', 'BUFFON': 'BUFFON',
        'MARTINEZ L': 'LMARTINEZ', 'FERGUSON': 'FERGUSON', 'TERRACCIANO': 'TERRACCIANO'
    }
    
    clean = "".join(re.findall(r'[A-Z0-9]+', n))
    for k, v in mapping.items():
        if k.replace(' ', '') in clean: return v
    
    # Se non in mapping, ordina le lettere/parole per flessibilità
    words = re.findall(r'[A-Z0-9]+', n)
    return "".join(sorted(words))

# --- CARICAMENTO DATI ---
def load_file(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return None

f_rs = load_file("rose_complete.csv")
f_qt = load_file("quotazioni.csv")
# Altri file (vincoli, punti, ecc.) omessi per brevità ma gestiti allo stesso modo

# Mappatura Ruoli Rose -> Quotazioni
map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A', 'Giovani': 'A'}

# LOGICA DI MATCHING POTENZIATA
if f_rs is not None and f_qt is not None:
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_v4)
    f_rs['R_Quot'] = f_rs['Ruolo'].map(map_r)
    
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_v4)
    # Merge su Chiave + Ruolo per risolvere i doppioni (Ferguson, Terracciano)
    f_rs = pd.merge(f_rs, f_qt[['MatchKey', 'R', 'Qt.A']], 
                    left_on=['MatchKey', 'R_Quot'], 
                    right_on=['MatchKey', 'R'], 
                    how='left').fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- MAIN APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V8.4")
tabs = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI", "🕵️ MERCATO"])

with tabs[2]: # ROSE & DEBUG TOOL
    if f_rs is not None:
        # 1. TOOL INDIVIDUAZIONE 0
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        # Escludiamo i giovani noti che non sono in lista se necessario, 
        # ma qui li mostriamo tutti per pulizia
        if not mancanti.empty:
            st.markdown(f"""<div class="status-box error-box">
                ⚠️ <b>GIOCATORI NON RICONOSCIUTI ({len(mancanti)}):</b><br>
                {", ".join(mancanti['Nome'].unique())}
            </div>""", unsafe_allow_html=True)

        # 2. TOOL DOPPIONI (MatchKey + Ruolo)
        # Se hanno stessa chiave e stesso ruolo ma sono righe diverse
        duplicates = f_rs[f_rs.duplicated(subset=['MatchKey', 'R_Quot'], keep=False)]
        if not duplicates.empty:
            st.markdown(f"""<div class="status-box warning-box">
                👯 <b>DOPPIONI NELLE ROSE:</b><br>
                {", ".join(duplicates['Nome'].unique())}
            </div>""", unsafe_allow_html=True)

        # 3. VISUALIZZAZIONE
        sq_list = sorted(f_rs['Fantasquadra'].unique())
        sq_sel = st.selectbox("SQUADRA", sq_list)
        df_sq = f_rs[f_rs['Fantasquadra'] == sq_sel]
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo', 'Quotazione']], use_container_width=True, hide_index=True)
    else:
        st.error("File rose_complete.csv non trovato.")

with tabs[4]: # SCAMBI
    st.subheader("🔄 SIMULATORE SCAMBI")
    # Logica scambi...

with tabs[6]: # MERCATO
    st.subheader("🕵️ SCOUTING SVINCOLATI")
    if f_qt is not None and f_rs is not None:
        occupati = f_rs['MatchKey'].tolist()
        liberi = f_qt[~f_qt['MatchKey'].isin(occupati)].sort_values('Qt.A', ascending=False)
        st.dataframe(liberi[['R', 'Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'}), use_container_width=True, hide_index=True)

# SIDEBAR
with st.sidebar:
    st.header("🔍 RICERCA GIOCATORE")
    if f_rs is not None:
        search = st.multiselect("CERCA", sorted(f_rs['Nome'].unique()))
        for n in search:
            r = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f'<div class="search-card"><b>{n}</b> ({r["Fantasquadra"]})<br>VAL: {int(r["Prezzo"])} | QUOT: {int(r["Quotazione"])}</div>', unsafe_allow_html=True)
