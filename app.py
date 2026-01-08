import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS PER GRASSETTO ESTREMO E BOX ERRORI
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
    .search-card { background-color: #ffffff; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE PULIZIA NOMI OTTIMIZZATA ---
def super_clean(name):
    if not isinstance(name, str): return ""
    
    # 1. Correzione manuale dei "caratteri rotti" (Encoding Mojibake)
    # Questa mappa risolve i casi come MONTIPÃ² o BERNABÃ¨
    mappa_encoding = {
        'Ã²': 'Ò', 'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã³': 'Ó',
        'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì',
        'Ã\x88': 'È', 'Ã\x80': 'À', 'Ã\x92': 'Ò', 'Ã\x8c': 'Ì', 'Ã\x99': 'Ù',
        'Ã': 'À' # Fallback generico per la A
    }
    for err, corr in mappa_encoding.items():
        name = name.replace(err, corr)

    # 2. Normalizzazione caratteri speciali rari (ň -> O, č -> E)
    name = name.replace('ň', 'O').replace('č', 'E')
    
    # 3. Trasformazione in Maiuscolo e rimozione spazi
    name = name.upper().strip()

    # 4. Mappatura casi critici e varianti nomi
    mapping = {
        'PAZ N': 'NICOPAZ', 'NICO PAZ': 'NICOPAZ',
        'TIAGO GABRIEL': 'GABRIEL', 'GABRIEL': 'GABRIEL',
        'SULEMANA K': 'SULEMANA', 'SULEMANA I': 'SULEMANA',
        'KON M': 'MKONE', 'KON I': 'KONESASSUOLO',
        'MARTINEZ L': 'LAUTARO', 'THURAM M': 'THURAM',
        'VLAHOVIC ATA': 'VLAHOVIC' # Gestione caso specifico vlahovic ata
    }
    
    # Pulizia radicale: teniamo solo lettere (incluse accentate) e numeri
    clean_raw = "".join(re.findall(r'[A-ZÀÈÉÌÒÓÙ0-9]+', name))
    
    # Controllo se il nome pulito è nei nostri casi speciali
    for k, v in mapping.items():
        if k.replace(' ', '') in clean_raw: 
            return v.replace(' ', '')
    
    # 5. Fallback: Se non è un caso speciale, ordiniamo le parole (es: MARTINELLI T -> MARTINELLIT)
    words = re.findall(r'[A-ZÀÈÉÌÒÓÙ0-9]+', name)
    words = [w for w in words if len(w) > 1] or words
    return "".join(sorted(words))

# --- FUNZIONI CARICAMENTO ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        # Proviamo UTF-8, se fallisce Latin1 (standard Excel/CSV)
        try:
            df = pd.read_csv(f, engine='python', encoding='utf-8')
        except:
            df = pd.read_csv(f, engine='python', encoding='latin1')
            
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean)
            return df.rename(columns={'Qt.A': 'Quotazione', 'R': 'Ruolo_Q'})
        return df.dropna(how='all')
    except: return None

def clean_string(s):
    if pd.isna(s): return None
    return str(s).strip().upper()

def to_num(val):
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# --- CARICAMENTO FILE ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE MATCH ---
if f_rs is not None and f_qt is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean)
    
    map_ruoli = {'PORTIERE':'P','DIFENSORE':'D','CENTROCAMPISTA':'C','ATTACCANTE':'A'}
    f_rs['R_Match'] = f_rs['Ruolo'].str.upper().map(map_ruoli)
    
    # Merge Standard (Ruolo + Nome)
    f_rs_std = f_rs[f_rs['Ruolo'] != 'Giovani'].copy()
    f_rs_std = pd.merge(f_rs_std, f_qt[['Match_Nome', 'Ruolo_Q', 'Quotazione']], left_on=['Match_Nome', 'R_Match'], right_on=['Match_Nome', 'Ruolo_Q'], how='left')
    
    # Merge Giovani (Solo Nome)
    f_rs_gio = f_rs[f_rs['Ruolo'] == 'Giovani'].copy()
    f_rs_gio = pd.merge(f_rs_gio, f_qt.drop_duplicates('Match_Nome')[['Match_Nome', 'Quotazione']], on='Match_Nome', how='left')
    
    f_rs = pd.concat([f_rs_std, f_rs_gio], ignore_index=True).fillna({'Quotazione': 0})
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA**")
    if f_rs is not None:
        scelte = st.multiselect("**CERCA GIOCATORE**", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f"""<div class="search-card"><b>{n}</b> ({dr['Squadra_N']})<br>ASTA: {int(dr['Prezzo_N'])} | QUOT: {int(dr['Quotazione'])}</div>""", unsafe_allow_html=True)

# --- MAIN APP ---
st.title("⚽ **MUYFANTAMANAGER GOLDEN V3.2**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

with t[2]: # ROSE & TOOL INDIVIDUAZIONE 0
    if f_rs is not None:
        # --- TOOL INDIVIDUAZIONE 0 ---
        mancanti_tot = f_rs[f_rs['Quotazione'] == 0]['Nome'].unique()
        if len(mancanti_tot) > 0:
            st.markdown(f"""
            <div class="zero-tool">
                ⚠️ <b>TOOL INDIVIDUAZIONE 0</b><br>
                Trovati {len(mancanti_tot)} giocatori non riconosciuti nel listone:<br>
                <small>{', '.join(mancanti_tot)}</small>
            </div>
            """, unsafe_allow_html=True)
        
        sq = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].dropna().unique()), key="rose_sq")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        st.dataframe(df_sq.style.format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 **SIMULATORE SCAMBI**")
    # Qui andrà il tuo codice scambi originale che avevi in Golden 1
    st.info("Logica scambi pronta per l'integrazione.")
