import streamlit as st
import pandas as pd
import os
import unicodedata
import re

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

# --- FUNZIONE PULIZIA NOMI (Riparazione Accenti + Match) ---
def super_clean(name):
    if not isinstance(name, str): return ""
    mappa_encoding = {
        'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì',
        'Ã\x88': 'È', 'Ã\x80': 'À', 'Ã\x92': 'Ò', 'Ã\x8c': 'Ì', 'Ã\x99': 'Ù', 'Ã': 'À'
    }
    for err, corr in mappa_encoding.items():
        name = name.replace(err, corr)
    name = name.replace('ň', 'O').replace('č', 'E').replace('ř', 'I').replace('ć', 'C')
    name = name.upper().strip()
    name = re.sub(r'\s[A-Z]\.$', '', name)
    mapping = {
        'ZAMBO ANGUISSA': 'ANGUISSA', 'ESPOSITO F.P.': 'PIO ESPOSITO', 
        'MARTINEZ L.': 'LAUTARO', 'PAZ N.': 'NICOPAZ', 'NICO PAZ': 'NICOPAZ',
        'VLAHOVIC ATA': 'VLAHOVIC', 'SULEMANA K.': 'SULEMANA', 'SULEMANA I.': 'SULEMANA'
    }
    clean_raw = "".join(re.findall(r'[A-ZÀÈÉÌÒÓÙ0-9]+', name))
    for k, v in mapping.items():
        if k.replace(' ', '').replace('.', '') in clean_raw: return v.replace(' ', '')
    words = re.findall(r'[A-ZÀÈÉÌÒÓÙ0-9]+', name)
    words = [w for w in words if len(w) > 1] or words
    return "".join(sorted(words))

# --- CARICAMENTO FILE ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        try: df = pd.read_csv(f, engine='python', encoding='utf-8')
        except: df = pd.read_csv(f, engine='python', encoding='latin1') [cite: 6]
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean)
            return df.rename(columns={'Qt.A': 'Quotazione', 'R': 'Ruolo_Q'}) [cite: 6]
        return df.dropna(how='all')
    except: return None

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None [cite: 7]
    return s_str.upper()

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0 [cite: 7]
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# CARICAMENTO
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num) [cite: 8]
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt[['Match_Nome', 'Quotazione']], on='Match_Nome', how='left').fillna({'Quotazione': 0}) [cite: 8]

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c] [cite: 8]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI" [cite: 8]

# --- SIDEBAR: RICERCA ---
with st.sidebar:
    st.header("🔍 **RICERCA GIOCATORE**")
    if f_rs is not None:
        scelte = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            # FIX SICUREZZA VINCOLI
            v_match = f_vn[f_vn['Giocatore_Match'] == clean_string(n)] if f_vn is not None else pd.DataFrame()
            vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0 [cite: 9, 10]
            st.markdown(f"""
            <div class="player-card card-grey">
                <b>{n}</b> (<b>{dr['Squadra_N']}</b>)<br>
                ASTA: <b>{int(dr['Prezzo_N'])}</b> | VINC: <b>{int(vv)}</b><br>
                QUOT: <b style="color:#1a73e8;">{int(dr['Quotazione'])}</b> | TOT: <b>{int(dr['Prezzo_N'] + vv)}</b>
            </div>
            """, unsafe_allow_html=True) [cite: 10, 11, 12]

# --- MAIN APP ---
st.title("⚽ **MUYFANTAMANAGER GOLDEN V3.2**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **CLASSIFICA PUNTI**")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione'), hide_index=True, use_container_width=True) [cite: 13]
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI DIRETTI**")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','Gol Fatti','Gol Subiti']], hide_index=True, use_container_width=True) [cite: 14]

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 **BUDGET E PATRIMONIO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1) [cite: 16]
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu['SPESA ROSE'] + bu['Tot_Vincolo'] + bu['CREDITI DISPONIBILI'] [cite: 16]
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False), hide_index=True, use_container_width=True) [cite: 17]

with t[2]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]['Nome'].unique()
        if len(mancanti) > 0:
            st.markdown(f'<div class="zero-tool">⚠️ {len(mancanti)} NON RICONOSCIUTI: {", ".join(mancanti)}</div>', unsafe_allow_html=True)
        sq = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].dropna().unique()))
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        st.dataframe(df_sq, hide_index=True, use_container_width=True) [cite: 18, 20]

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 **VINCOLI ATTIVI**")
        sq_v = st.selectbox("**FILTRA SQUADRA**", ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s]))
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v_display[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']], hide_index=True, use_container_width=True) [cite: 21]

with t[4]: # SCAMBI
    st.subheader("🔄 **SIMULATORE SCAMBI**")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        lista_sq = sorted(f_rs['Squadra_N'].unique())
        with c1:
            sa = st.selectbox("**SQUADRA A**", lista_sq, key="sa")
            ga = st.multiselect("**ESCONO DA A**", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist()) [cite: 22]
        with c2:
            sb = st.selectbox("**SQUADRA B**", [s for s in lista_sq if s != sa], key="sb")
            gb = st.multiselect("**ESCONO DA B**", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist()) [cite: 22]
        
        if ga and gb:
            def get_val(n):
                p_row = f_rs[f_rs['Nome']==n]
                p = p_row['Prezzo_N'].iloc[0] if not p_row.empty else 0 [cite: 23]
                # FIX IndexError: controllo se il giocatore esiste nei vincoli
                v_row = f_vn[f_vn['Giocatore_Match'] == clean_string(n)] if f_vn is not None else pd.DataFrame()
                v = v_row['Tot_Vincolo'].iloc[0] if not v_row.empty else 0 [cite: 23]
                return p + v
            
            val_a = sum(get_val(n) for n in ga) [cite: 24]
            val_b = sum(get_val(n) for n in gb) [cite: 24]
            st.metric("Sbilanciamento Scambio", f"{int(val_a - val_b)} crediti") [cite: 25]

with t[5]: # TAGLI
    st.subheader("✂️ **SIMULATORE TAGLI**")
    if f_rs is not None:
        sq_t = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sqt")
        gioc_t = st.selectbox("**GIOCATORE**", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
        if gioc_t:
            p_row = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gioc_t)]
            v_p = p_row['Prezzo_N'].iloc[0] if not p_row.empty else 0 [cite: 29]
            rimborso = round(v_p * 0.6) [cite: 29]
            st.markdown(f'<div class="cut-box"><h3>💰 RIMBORSO: {rimborso} CREDITI</h3></div>', unsafe_allow_html=True) [cite: 30]
