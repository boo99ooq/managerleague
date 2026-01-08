import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS: Neretto estremo 900 su TUTTO
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame, td, th, p, div, span, label, input { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
    .punto-incontro-box { background-color: #fff3e0; padding: 8px 25px; border-radius: 12px; border: 3px solid #ff9800; text-align: center; width: fit-content; margin: auto; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; }
    .cut-player-name { font-size: 3.2em; color: #d32f2f; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
    .cut-refund-value { font-size: 1.8em; color: #2e7d32; background: #e8f5e9; padding: 10px 20px; border-radius: 8px; display: inline-block; border: 2px solid #2e7d32; }
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 3px solid #333; text-align: center; min-height: 120px; }
    .text-ufficiale { color: #2e7d32; }
    .text-probabile { color: #ed6c02; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean_match)
            return df[['Match_Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- GESTIONE DB MERCATO (FIX KEYERROR) ---
cols_m = ["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"]
if os.path.exists(FILE_DB):
    try:
        df_mercato = pd.read_csv(FILE_DB)
        if not all(c in df_mercato.columns for c in cols_m): df_mercato = pd.DataFrame(columns=cols_m)
    except: df_mercato = pd.DataFrame(columns=cols_m)
else:
    df_mercato = pd.DataFrame(columns=cols_m)

rimborsi_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[2]: # ROSE + RICERCA TOTALE
    if f_rs is not None:
        st.subheader("🏃 GESTIONE ROSE")
        c_r1, c_r2 = st.columns([1, 2])
        with c_r1:
            sq_sel = st.selectbox("**FILTRA SQUADRA**", ["TUTTE"] + sorted(f_rs['Squadra_N'].unique()), key="sq_rose")
        with c_r2:
            cerca_gioc = st.text_input("🔍 **CERCA GIOCATORE (IN TUTTA LA LEGA)**", "").upper()
        
        df_disp = f_rs.copy()
        if sq_sel != "TUTTE": df_disp = df_disp[df_disp['Squadra_N'] == sq_sel]
        if cerca_gioc: df_disp = df_disp[df_disp['Nome'].str.contains(cerca_gioc, na=False)]
            
        st.dataframe(df_disp[['Squadra_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].style.set_properties(**{'font-weight': '900'}).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 VINCOLI ATTIVI")
        df_v = f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False)
        st.dataframe(df_v.style.set_properties(**{'font-weight': '900'}).format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)

with t[5]: # TAGLI
    st.subheader("✂️ TAGLI GOLDEN")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_tag")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_tag")
        if gt:
            v_a = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            vm = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame()
            v_v = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt}</div><div class="cut-refund-value">RIMBORSO: {round((v_a + v_v) * 0.6):g} CREDITI</div><br><br>ASTA: {v_a:g} | VINCOLI: {v_v:g}</div>''', unsafe_allow_html=True)

with t[6]: # MERCATO (FIXED)
    st.subheader("🚀 MERCATO GENNAIO")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc_m = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI"):
            if sc_m != "" and sc_m not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == sc_m].iloc[0]
                vm_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(sc_m)] if f_vn is not None else pd.DataFrame()
                vv_m = vm_m['Tot_Vincolo'].iloc[0] if not vm_m.empty else 0
                s, q = info['Prezzo_N'], info['Quotazione']
                nuova = pd.DataFrame([{"GIOCATORE": sc_m, "SQUADRA": info['Squadra_N'], "SPESA": s, "QUOT": q, "RIMB_BASE": (s+q)*0.5, "VINCOLO": vv_m, "TOTALE": ((s+q)*0.5)+vv_m, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    
    if not df_mercato.empty:
        st.write("---")
        for idx, row in df_mercato.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 2, 1, 1])
            with c1: st.markdown(f"**{row['GIOCATORE']}**<br><small>{row['SQUADRA']}</small>", unsafe_allow_html=True)
            with c2: st.write(f"{row['SPESA']:g}")
            with c3: st.write(f"{row['QUOT']:g}")
            with c4: st.markdown(f"<small>50%:{row['RIMB_BASE']:g}+V:{row['VINCOLO']:g}</small>", unsafe_allow_html=True)
            with c5: st.write(f"**{row['TOTALE']:g}**")
            with c6:
                st.write(f"{row['STATO']}")
                sc1, sc2 = st.columns(2)
                if row['STATO'] == "PROBABILE" and sc1.button("✅", key=f"u_{idx}"): df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if sc2.button("🗑️", key=f"d_{idx}"): df_mercato = df_mercato.drop(idx); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
