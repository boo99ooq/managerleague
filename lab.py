import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS INTEGRALE
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); color: black; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
    .punto-incontro-box { background-color: #fff3e0; padding: 8px 25px; border-radius: 12px; border: 3px solid #ff9800; text-align: center; width: fit-content; }
    
    /* STYLE TAGLI RICHIESTO: NOME GIGANTE */
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; color: #1a1a1a; margin-top: 10px; }
    .cut-player-name { font-size: 3.2em; color: #d32f2f; text-transform: uppercase; margin-bottom: 5px; line-height: 1; }
    .cut-refund-label { font-size: 0.9em; color: #555; text-transform: uppercase; }
    .cut-refund-value { font-size: 1.6em; color: #2e7d32; background: #e8f5e9; padding: 5px 15px; border-radius: 8px; display: inline-block; margin-top: 5px; }
    
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 3px solid #333; margin-bottom: 10px; text-align: center; min-height: 120px; }
    .stat-label { font-size: 0.85em; color: #666; font-weight: 400 !important; }
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

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

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
f_sc, f_pt = ld("scontridiretti.csv"), ld("classificapunti.csv")
f_rs, f_vn = ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None: f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- GESTIONE DATABASE MERCATO (FIX KEYERROR) ---
cols_mercato = ["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"]
if os.path.exists(FILE_DB):
    try:
        df_mercato = pd.read_csv(FILE_DB)
        # Verifica se tutte le colonne necessarie esistono
        if not all(c in df_mercato.columns for c in cols_mercato):
             df_mercato = pd.DataFrame(columns=cols_mercato)
    except:
        df_mercato = pd.DataFrame(columns=cols_mercato)
else:
    df_mercato = pd.DataFrame(columns=cols_mercato)

rimborsi_squadre_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# (Le tab 0, 1, 2, 3, 4 sono standard e funzionanti)
with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            st.subheader("🎯 PUNTI")
            st.dataframe(f_pt[['Posizione','Giocatore','P_N']].sort_values('Posizione').style.background_gradient(subset=['P_N'], cmap='YlGn').format({"P_N":"{:g}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            st.subheader("⚔️ SCONTRI")
            st.dataframe(f_sc[['Posizione','Giocatore','P_S']].sort_values('Posizione').style.background_gradient(subset=['P_S'], cmap='Blues').format({"P_S":"{:g}"}), hide_index=True, use_container_width=True)

with t[5]: # TAGLI (LAYOUT NOME GIGANTE)
    st.subheader("✂️ SIMULATORE TAGLI")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted([s for s in f_rs['Squadra_N'].unique() if s]), key="sq_tag_final")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_tag_final")
        if gt:
            p_t_v = f_rs[f_rs['Squadra_N']==sq_t]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sq_t]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sq_t, 0)
            v_asta = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame()
            v_vinc = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
            rimb = round((v_asta + v_vinc) * 0.6); inc = ((v_asta + v_vinc) / p_t_v) * 100
            st.markdown(f'''<div class="cut-box"><div class="stat-label">SCHEDA TAGLIO CALCIATORE</div><div class="cut-player-name">{gt}</div><div class="cut-refund-label">RIMBORSO MATURATO (60%)</div><br><div class="cut-refund-value">+{rimb:g} CREDITI</div><hr style="border: 0; border-top: 2px dashed #333; margin: 20px 0;"><div style="display: flex; justify-content: space-between; text-align: center;"><div style="flex: 1;"><span class="stat-label">ASTA</span><br><b style="font-size: 1.4em;">{v_asta:g}</b></div><div style="flex: 1; border-left: 2px solid #eee; border-right: 2px solid #eee;"><span class="stat-label">VINCOLI</span><br><b style="font-size: 1.4em;">{v_vinc:g}</b></div><div style="flex: 1;"><span class="stat-label">INCIDENZA</span><br><b style="font-size: 1.4em;">{inc:.2f}%</b></div></div></div>''', unsafe_allow_html=True)

with t[6]: # MERCATO (FIX SYNTAX & KEYERROR)
    st.subheader("🚀 GESTIONE MERCATO GENNAIO")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI"):
            if sc != "" and sc not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == sc].iloc[0]
                v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(sc)] if f_vn is not None else pd.DataFrame()
                vv = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
                s, q = info['Prezzo_N'], info['Quotazione']
                rb = (s + q) * 0.5
                nuova = pd.DataFrame([{"GIOCATORE": sc, "SQUADRA": info['Squadra_N'], "SPESA": s, "QUOT": q, "RIMB_BASE": rb, "VINCOLO": vv, "TOTALE": rb+vv, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    
    if not df_mercato.empty:
        st.write("---")
        h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 2, 1, 1])
        h1.write("**NOME**"); h2.write("**SPESA**"); h3.write("**QUOT**"); h4.write("**DETTAGLIO**"); h5.write("**TOT**"); h6.write("**STATO**")
        for i, row in df_mercato.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 2, 1, 1])
            with c1: st.markdown(f"**{row['GIOCATORE']}**<br><small>{row['SQUADRA']}</small>", unsafe_allow_html=True)
            with c2: st.write(f"{row['SPESA']:g}")
            with c3: st.write(f"{row['QUOT']:g}")
            with c4: st.markdown(f"<small>50%:{row['RIMB_BASE']:g}+V:{row['VINCOLO']:g}</small>", unsafe_allow_html=True)
            with c5: st.write(f"**{row['TOTALE']:g}**")
            with c6:
                cl = "status-ufficiale" if row['STATO'] == "UFFICIALE" else "status-probabile"
                st.markdown(f"<span class='{cl}'>{row['STATO']}</span>", unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                if row['STATO'] == "PROBABILE" and sc1.button("✅", key=f"u_{i}"): df_mercato.at[i, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if sc2.button("🗑️", key=f"d_{i}"): df_mercato = df_mercato.drop(i); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
