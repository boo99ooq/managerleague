import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Gold V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS ORIGINALE (Grassetto estremo e box personalizzati)
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

# --- NUOVA FUNZIONE PULIZIA NOMI (Riparazione Accenti + Match) ---
def super_clean(name):
    if not isinstance(name, str): return ""
    
    # 1. Riparazione Mojibake (es. MONTIPÃ² -> MONTIPÒ)
    mappa_encoding = {
        'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì',
        'Ã\x88': 'È', 'Ã\x80': 'À', 'Ã\x92': 'Ò', 'Ã\x8c': 'Ì', 'Ã\x99': 'Ù', 'Ã': 'À'
    }
    for err, corr in mappa_encoding.items():
        name = name.replace(err, corr)

    # 2. Normalizzazione caratteri speciali rari
    name = name.replace('ň', 'O').replace('č', 'E').replace('ř', 'I').replace('ć', 'C')
    
    # 3. Trasformazione in Maiuscolo e rimozione punteggiatura finale
    name = name.upper().strip()
    name = re.sub(r'\s[A-Z]\.$', '', name) # Rimuove "DYBALA P."

    # 4. Mappatura Casi Critici (Dizionario della tua Golden Version + Nuovi)
    mapping = {
        'ZAMBO ANGUISSA': 'ANGUISSA', 'ESPOSITO F.P.': 'PIO ESPOSITO', 
        'MARTINEZ L.': 'LAUTARO', 'PAZ N.': 'NICOPAZ', 'NICO PAZ': 'NICOPAZ',
        'VLAHOVIC ATA': 'VLAHOVIC', 'SULEMANA K.': 'SULEMANA', 'SULEMANA I.': 'SULEMANA'
    }
    
    # Pulizia radicale per il match: solo lettere A-Z e lettere accentate
    clean_raw = "".join(re.findall(r'[A-ZÀÈÉÌÒÓÙ0-9]+', name))
    
    for k, v in mapping.items():
        if k.replace(' ', '').replace('.', '') in clean_raw: 
            return v.replace(' ', '')
    
    # Fallback: Ordina le parole per gestire "MARTINELLI T." -> "MARTINELLIT"
    words = re.findall(r'[A-ZÀÈÉÌÒÓÙ0-9]+', name)
    words = [w for w in words if len(w) > 1] or words
    return "".join(sorted(words))

# --- CARICAMENTO FILE ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        # Prova UTF-8, poi Latin1 per gestire i caratteri speciali del listone [cite: 6]
        try: df = pd.read_csv(f, engine='python', encoding='utf-8')
        except: df = pd.read_csv(f, engine='python', encoding='latin1')
            
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean)
            return df.rename(columns={'Qt.A': 'Quotazione', 'R': 'Ruolo_Q'})
        return df.dropna(how='all')
    except: return None

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# CARICAMENTO
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE ROSE CON MATCH POTENZIATO ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    
    if f_qt is not None:
        # Merge basato sulla colonna pulita 'Match_Nome'
        f_rs = pd.merge(f_rs, f_qt[['Match_Nome', 'Quotazione']], on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- SIDEBAR: RICERCA ---
with st.sidebar:
    st.header("🔍 **RICERCA GIOCATORE**")
    if f_rs is not None:
        scelte = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            vv = f_vn[f_vn['Giocatore'].apply(clean_string) == clean_string(n)]['Tot_Vincolo'].iloc[0] if (f_vn is not None) else 0
            st.markdown(f"""
            <div class="player-card card-grey">
                <b>{n}</b> (<b>{dr['Squadra_N']}</b>)<br>
                ASTA: <b>{int(dr['Prezzo_N'])}</b> | VINC: <b>{int(vv)}</b><br>
                QUOT: <b style="color:#1a73e8;">{int(dr['Quotazione'])}</b> | TOT: <b>{int(dr['Prezzo_N'] + vv)}</b>
            </div>
            """, unsafe_allow_html=True)

# --- MAIN APP ---
st.title("⚽ **MUYFANTAMANAGER GOLDEN V3.2**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

with t[0]: # CLASSIFICHE [cite: 13, 14]
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **CLASSIFICA PUNTI**")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style.background_gradient(subset=['P_N', 'FM'], cmap='YlGn'), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI DIRETTI**")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','Gol Fatti','Gol Subiti']].style.background_gradient(subset=['P_S'], cmap='Blues'), hide_index=True, use_container_width=True)

with t[1]: # BUDGET [cite: 16, 17]
    if f_rs is not None:
        st.subheader("💰 **BUDGET E PATRIMONIO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu['SPESA ROSE'] + bu['Tot_Vincolo'] + bu['CREDITI DISPONIBILI']
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False), hide_index=True, use_container_width=True)

with t[2]: # ROSE [cite: 18, 19]
    if f_rs is not None:
        # Tool segnalazione errori match
        mancanti = f_rs[f_rs['Quotazione'] == 0]['Nome'].unique()
        if len(mancanti) > 0:
            st.markdown(f'<div class="zero-tool">⚠️ {len(mancanti)} NON RICONOSCIUTI: {", ".join(mancanti)}</div>', unsafe_allow_html=True)
        
        sq = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].dropna().unique()))
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        st.dataframe(df_sq.style.format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI [cite: 21]
    if f_vn is not None:
        st.subheader("📅 **VINCOLI ATTIVI**")
        sq_v = st.selectbox("**FILTRA SQUADRA**", ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s]))
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v_display[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI [cite: 22, 23, 24, 25, 26, 27]
    st.subheader("🔄 **SIMULATORE SCAMBI**")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        lista_sq = sorted(f_rs['Squadra_N'].unique())
        with c1:
            sa = st.selectbox("**SQUADRA A**", lista_sq, key="sa")
            ga = st.multiselect("**ESCONO DA A**", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist())
        with c2:
            sb = st.selectbox("**SQUADRA B**", [s for s in lista_sq if s != sa], key="sb")
            gb = st.multiselect("**ESCONO DA B**", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist())
        
        if ga and gb:
            def get_val(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                v = f_vn[f_vn['Giocatore'].apply(clean_string)==clean_string(n)]['Tot_Vincolo'].iloc[0] if f_vn is not None else 0
                return p + v
            
            val_a = sum(get_val(n) for n in ga)
            val_b = sum(get_val(n) for n in gb)
            st.metric("Sbilanciamento Scambio", f"{int(val_a - val_b)} crediti")

with t[5]: # TAGLI [cite: 29, 30]
    st.subheader("✂️ **SIMULATORE TAGLI**")
    if f_rs is not None:
        sq_t = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sqt")
        gioc_t = st.selectbox("**GIOCATORE**", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
        if gioc_t:
            v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gioc_t)]['Prezzo_N'].iloc[0]
            rimborso = round(v_p * 0.6)
            st.markdown(f'<div class="cut-box"><h3>💰 RIMBORSO: {rimborso} CREDITI</h3></div>', unsafe_allow_html=True)
