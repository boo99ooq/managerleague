import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS INTEGRALE (Grassetto, card sidebar rinforzate e box riepilogo)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    /* CARD STILE RINFORZATO PER TUTTE LE SEZIONI */
    .player-card { 
        padding: 12px; 
        border-radius: 10px; 
        margin-bottom: 12px; 
        border: 3px solid #333; 
        box-shadow: 4px 4px 8px rgba(0,0,0,0.2); 
        color: black; 
    }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
    .cut-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 3px solid #ff4b4b; color: #1a1a1a; box-shadow: 4px 4px 8px rgba(0,0,0,0.1); }
    .refund-box { 
        background-color: #f8f9fa; 
        padding: 10px; 
        border-radius: 10px; 
        border: 3px solid #333; 
        margin-bottom: 10px; 
        text-align: center;
        min-height: 120px;
    }
    .status-ufficiale { color: #2e7d32; font-weight: 900; }
    .status-probabile { color: #ed6c02; font-weight: 900; }
    .info-small { font-size: 0.8em; color: #666; font-weight: 400 !important; }
    .text-ufficiale { color: #2e7d32; font-size: 0.85em; }
    .text-probabile { color: #ed6c02; font-size: 0.85em; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items():
        name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    mapping = {'ZAMBO ANGUISSA': 'ANGUISSA', 'MARTINEZ L.': 'LAUTARO', 'PAZ N.': 'NICO PAZ', 'CASTELLANOS T.': 'CASTELLANOS', 'MARTINELLI T.': 'MARTINELLI'}
    return mapping.get(name, re.sub(r'\s[A-Z]\.$', '', name))

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
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE DATI ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- GESTIONE DATABASE MERCATO ---
if os.path.exists(FILE_DB):
    df_mercato = pd.read_csv(FILE_DB)
    if not df_mercato.empty and f_rs is not None:
        for i, row in df_mercato.iterrows():
            if row.get('SPESA', 0) == 0:
                match = f_rs[f_rs['Nome'] == row['GIOCATORE']]
                if not match.empty:
                    s, q = match.iloc[0]['Prezzo_N'], match.iloc[0]['Quotazione']
                    v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(row['GIOCATORE'])] if f_vn is not None else pd.DataFrame()
                    vv = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
                    rb = (s + q) * 0.5
                    df_mercato.at[i, 'SPESA'], df_mercato.at[i, 'QUOT'], df_mercato.at[i, 'RIMB_BASE'], df_mercato.at[i, 'VINCOLO'], df_mercato.at[i, 'TOTALE'] = s, q, rb, vv, rb+vv
else:
    df_mercato = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"])

rimborsi_squadre_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR: RICERCA CARD RINFORZATE ---
with st.sidebar:
    st.header("🔍 **RICERCA GIOCATORE**")
    if f_rs is not None:
        scelte = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(n)] if f_vn is not None else pd.DataFrame()
            vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
            r = str(dr['Ruolo']).upper()
            bg = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'''
                <div class="player-card" style="background-color: {bg};">
                    <b style="font-size: 1.1em;">{n}</b><br>
                    <small>({dr["Squadra_N"]})</small><hr style="margin: 8px 0; border: 0; border-top: 2px solid #333;">
                    ASTA: <b>{int(dr["Prezzo_N"])}</b> | VINC: <b>{int(vv)}</b><br>
                    QUOT: <b style="color: #1a73e8;">{int(dr["Quotazione"])}</b>
                </div>
            ''', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **RIMBORSO CESSIONI**"])

# TAB CLASSIFICHE
with t[0]:
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **CLASSIFICA PUNTI**")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N']].sort_values('Posizione').style.background_gradient(subset=['P_N'], cmap='YlGn').format({"P_N": "{:g}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI DIRETTI**")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            f_sc['GF'] = f_sc['Gol Fatti'].apply(to_num)
            f_sc['GS'] = f_sc['Gol Subiti'].apply(to_num)
            f_sc['DR'] = f_sc['GF'] - f_sc['GS']
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','GF','GS','DR']].sort_values('Posizione').style.background_gradient(subset=['P_S'], cmap='Blues').format({"P_S": "{:g}", "GF": "{:g}", "GS": "{:g}", "DR": "{:g}"}), hide_index=True, use_container_width=True)

# TAB BUDGET
with t[1]:
    if f_rs is not None:
        st.subheader("💰 **BUDGET DINAMICO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rimborsi_squadre_tot).fillna(0)
        voci_disp = ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI']
        sel = st.multiselect("**VOCI PATRIMONIO:**", voci_disp, default=voci_disp)
        bu['PATRIMONIO TOTALE'] = bu[sel].sum(axis=1) if sel else 0
        st.dataframe(bu[['Squadra_N'] + sel + ['PATRIMONIO TOTALE']].sort_values("PATRIMONIO TOTALE", ascending=False).style.background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE']).format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}), hide_index=True, use_container_width=True)

# TAB ROSE
with t[2]:
    if f_rs is not None:
        sq = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="rose_sel")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        def color_ruoli(row):
            r = str(row['Ruolo']).upper(); bg = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: 900;'] * len(row)
        st.dataframe(df_sq.style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

# TAB VINCOLI
with t[3]:
    if f_vn is not None:
        st.subheader("📅 **VINCOLI ATTIVI**")
        sq_v = st.selectbox("**FILTRA SQUADRA**", ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s]), key="vinc_sel")
        df_v_disp = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v_disp[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.background_gradient(subset=['Tot_Vincolo'], cmap='Purples').format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)

# TAB SCAMBI (CARD RINFORZATE)
with t[4]:
    st.subheader("🔄 **SIMULATORE SCAMBI**")
    if f_rs is not None:
        sc1, sc2 = st.columns(2); lista_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        with sc1: sa = st.selectbox("**SQUADRA A**", lista_sq, key="sa_f"); ga = st.multiselect("**DA A**", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
        with sc2: sb = st.selectbox("**SQUADRA B**", [s for s in lista_sq if s != sa], key="sb_f"); gb = st.multiselect("**DA B**", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
        if ga and gb:
            def get_val(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]; vm = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame(); v = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
                return {'t': p + v, 'v': v}
            da, db = {n: get_val(n) for n in ga}, {n: get_val(n) for n in gb}
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values()); nuovo_tot = round((ta + tb) / 2)
            st.divider(); r1, r2 = st.columns(2)
            with r1:
                for n, i in db.items():
                    peso = i['t']/tb if tb > 0 else 1/len(gb); nuovo_t = round(peso*nuovo_tot)
                    st.markdown(f'<div class="player-card" style="background-color: #e3f2fd; border: 3px solid #333;"><b>{n}</b><br>NUOVA VAL: <b>{max(0, nuovo_t-int(i["v"]))}</b></div>', unsafe_allow_html=True)
            with r2:
                for n, i in da.items():
                    peso = i['t']/ta if ta > 0 else 1/len(ga); nuovo_t = round(peso*nuovo_tot)
                    st.markdown(f'<div class="player-card" style="background-color: #fbe9e7; border: 3px solid #333;"><b>{n}</b><br>NUOVA VAL: <b>{max(0, nuovo_t-int(i["v"]))}</b></div>', unsafe_allow_html=True)

# TAB TAGLI (CARD RINFORZATA)
with t[5]:
    st.subheader("✂️ **SIMULATORE TAGLI**")
    sq_t = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_tag"); gt = st.selectbox("**GIOCATORE**", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_tag")
    if gt:
        v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
        v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame(); v_v = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
        st.markdown(f'<div class="cut-box" style="border: 3px solid #ff4b4b;"><h3>💰 **RIMBORSO (60%): {round((v_p + v_v) * 0.6)}**</h3></div>', unsafe_allow_html=True)

# TAB RIMBORSO CESSIONI
with t[6]:
    st.subheader("🚀 **GESTIONE MOVIMENTI GENNAIO**")
    with st.expander("➕ AGGIUNGI GIOCATORE"):
        scelta = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI IN LISTA"):
            if scelta != "" and scelta not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == scelta].iloc[0]
                v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(scelta)] if f_vn is not None else pd.DataFrame()
                vv = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
                s, q = info['Prezzo_N'], info['Quotazione']; rb = (s + q) * 0.5
                nuova = pd.DataFrame([{"GIOCATORE": scelta, "SQUADRA": info['Squadra_N'], "SPESA": s, "QUOT": q, "RIMB_BASE": rb, "VINCOLO": vv, "TOTALE": rb+vv, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()

    if not df_mercato.empty:
        st.write("---"); h1, h2, h3, h4, h5, h6 = st.columns([2, 1, 1, 2, 1, 1])
        h1.write("**GIOCATORE**"); h2.write("**SPESA**"); h3.write("**QUOT**"); h4.write("**DETTAGLIO**"); h5.write("**TOTALE**"); h6.write("**STATO**")
        for i, row in df_mercato.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1, 2, 1, 1])
            with c1: st.markdown(f"**{row['GIOCATORE']}**<br><small>{row['SQUADRA']}</small>", unsafe_allow_html=True)
            with c2: st.write(f"{row['SPESA']:g}")
            with c3: st.write(f"{row['QUOT']:g}")
            with c4: st.markdown(f"<span class='info-small'>50%: {row['RIMB_BASE']:g} + Vinc: {row['VINCOLO']:g}</span>", unsafe_allow_html=True)
            with c5: st.write(f"**{row['TOTALE']:g}**")
            with c6:
                cl = "status-ufficiale" if row['STATO'] == "UFFICIALE" else "status-probabile"
                st.markdown(f"<span class='{cl}'>{row['STATO']}</span>", unsafe_allow_html=True)
                s1, s2 = st.columns(2)
                if row['STATO'] == "PROBABILE" and s1.button("✅", key=f"u_{i}"): df_mercato.at[i, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if s2.button("🗑️", key=f"d_{i}"): df_mercato = df_mercato.drop(i); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
        
        st.write("---"); st.markdown("### 💰 RIEPILOGO RIMBORSI")
        sq_stats = df_mercato.groupby(['SQUADRA', 'STATO'])['TOTALE'].sum().unstack(fill_value=0)
        if 'UFFICIALE' not in sq_stats.columns: sq_stats['UFFICIALE'] = 0
        if 'PROBABILE' not in sq_stats.columns: sq_stats['PROBABILE'] = 0
        sq_stats['TOT_GEN'] = sq_stats['UFFICIALE'] + sq_stats['PROBABILE']; sq_stats = sq_stats.sort_values('TOT_GEN', ascending=False)
        cols_riep = st.columns(4)
        for idx, (squadra, data) in enumerate(sq_stats.iterrows()):
            with cols_riep[idx % 4]:
                st.markdown(f'<div class="refund-box"><small>{squadra}</small><br><b>+{data["TOT_GEN"]:g}</b><br><hr style="margin:5px 0; border:0; border-top:1px solid #ccc;"><span class="text-ufficiale">Uff: {data["UFFICIALE"]:g}</span><br><span class="text-probabile">Prob: {data["PROBABILE"]:g}</span></div>', unsafe_allow_html=True)
