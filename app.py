import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# --- CSS ORIGINALE ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
    .cut-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #1a1a1a; }
    .zero-tool { background-color: #ffebee; color: #c62828; padding: 15px; border-radius: 10px; border: 2px solid #c62828; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DEFINIZIONE FUNZIONI (Tutte all'inizio per evitare NameError) ---

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def super_clean_name(name):
    """Il 'motore' che corregge accenti e diciture extra per il match perfetto"""
    if not isinstance(name, str): return ""
    
    # 1. Riparazione encoding (Mojibake)
    mappa_encoding = {
        'Ã²': 'O', 'Ã³': 'O', 'Ã¨': 'E', 'Ã©': 'E', 'Ã¹': 'U', 'Ã¬': 'I',
        'Ã\x88': 'E', 'Ã\x80': 'A', 'Ã\x92': 'O', 'Ã\x8c': 'I', 'Ã\x99': 'U', 'Ã': 'A'
    }
    for err, corr in mappa_encoding.items():
        name = name.replace(err, corr)

    # 2. Normalizzazione (Rimuove accenti standard)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    
    # 3. Pulizia diciture extra e iniziali (es: "VLAHOVIC ATA" -> "VLAHOVIC", "DYBALA P." -> "DYBALA")
    name = re.sub(r'\sATA$', '', name)
    name = re.sub(r'\s[A-Z]\.$', '', name)
    name = re.sub(r'\s[A-Z]$', '', name)
    
    # 4. Casi specifici della tua lega
    mapping = {
        'ZAMBO ANGUISSA': 'ANGUISSA', 'ESPOSITO FP': 'PIOESPOSITO', 
        'MARTINEZ L': 'LAUTARO', 'PAZ N': 'NICOPAZ', 'NICO PAZ': 'NICOPAZ',
        'SULEMANA I': 'SULEMANA', 'SULEMANA K': 'SULEMANA'
    }
    
    # Solo lettere e numeri
    clean_raw = "".join(re.findall(r'[A-Z0-9]', name))
    
    return mapping.get(clean_raw, clean_raw)

def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        # Caricamento con gestione encoding
        try: df = pd.read_csv(f, engine='python', encoding='utf-8')
        except: df = pd.read_csv(f, engine='python', encoding='latin1')
        
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Key'] = df['Nome'].apply(super_clean_name)
            return df.rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except: return None

# --- 3. CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- 4. ELABORAZIONE ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome_Originale'] = f_rs['Nome']
    f_rs['Match_Key'] = f_rs['Nome'].apply(super_clean_name)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    
    if f_qt is not None:
        # Merge sul campo 'Match_Key' creato per entrambi
        f_rs = pd.merge(f_rs, f_qt[['Match_Key', 'Quotazione']], on='Match_Key', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_name)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- 5. APP UI ---
st.title("⚽ **MUYFANTAMANAGER GOLDEN V3.2**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **CLASSIFICA PUNTI**")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N']].sort_values('Posizione'), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI DIRETTI**")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S']], hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 **BUDGET E PATRIMONIO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu['SPESA ROSE'] + bu['Tot_Vincolo'] + bu['CREDITI DISPONIBILI']
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        # Tool segnalazione errori
        mancanti = f_rs[f_rs['Quotazione'] == 0]['Nome_Originale'].unique()
        if len(mancanti) > 0:
            st.markdown(f'<div class="zero-tool">⚠️ {len(mancanti)} GIOCATORI NON TROVATI: {", ".join(mancanti)}</div>', unsafe_allow_html=True)
        
        sq = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].dropna().unique()), key="sel_sq")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome_Originale', 'Prezzo_N', 'Quotazione']]
        st.dataframe(df_sq, hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 **VINCOLI ATTIVI**")
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']], hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 **SIMULATORE SCAMBI**")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        lista_sq = sorted(f_rs['Squadra_N'].unique())
        with c1:
            sa = st.selectbox("**SQUADRA A**", lista_sq, key="sa")
            ga = st.multiselect("**ESCONO DA A**", f_rs[f_rs['Squadra_N']==sa]['Nome_Originale'].tolist())
        with c2:
            sb = st.selectbox("**SQUADRA B**", [s for s in lista_sq if s != sa], key="sb")
            gb = st.multiselect("**ESCONO DA B**", f_rs[f_rs['Squadra_N']==sb]['Nome_Originale'].tolist())
        
        if ga and gb:
            def get_val(n):
                # Cerco il valore del giocatore (Prezzo + Vincolo) in modo sicuro
                p_row = f_rs[f_rs['Nome_Originale'] == n]
                prezzo = p_row['Prezzo_N'].iloc[0] if not p_row.empty else 0
                
                v_row = f_vn[f_vn['Giocatore_Match'] == super_clean_name(n)] if f_vn is not None else pd.DataFrame()
                vincolo = v_row['Tot_Vincolo'].iloc[0] if not v_row.empty else 0
                return prezzo + vincolo
            
            val_a = sum(get_val(n) for n in ga)
            val_b = sum(get_val(n) for n in gb)
            st.metric("Sbilanciamento Scambio", f"{int(val_a - val_b)} crediti")

with t[5]: # TAGLI
    st.subheader("✂️ **SIMULATORE TAGLI**")
    if f_rs is not None:
        sq_t = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sqt")
        gioc_t = st.selectbox("**GIOCATORE**", f_rs[f_rs['Squadra_N'] == sq_t]['Nome_Originale'].tolist())
        if gioc_t:
            v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome_Originale'] == gioc_t)]['Prezzo_N'].iloc[0]
            rimborso = round(v_p * 0.6)
            st.markdown(f'<div class="cut-box"><h3>💰 RIMBORSO: {rimborso} CREDITI</h3></div>', unsafe_allow_html=True)
