import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS DEFINITIVO: Neretto 900 su tutto, widget e tabelle inclusi
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame, td, th, p, div, span, label, input { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
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

# --- DB MERCATO CESSIONI ---
if os.path.exists(FILE_DB):
    df_mercato = pd.read_csv(FILE_DB)
else:
    df_mercato = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"])

rimborsi_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            df = f_pt[['Posizione','Giocatore','Punti Totali']].copy()
            df['Punti Totali'] = df['Punti Totali'].apply(to_num)
            st.dataframe(df.sort_values('Posizione').style.set_properties(**{'font-weight': '900'}).background_gradient(subset=['Punti Totali'], cmap='YlGn').format({"Punti Totali":"{:g}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI")
            df = f_sc[['Posizione','Giocatore','Punti','Gol Fatti','Gol Subiti']].copy()
            for col in ['Punti','Gol Fatti','Gol Subiti']: df[col] = df[col].apply(to_num)
            df['DR'] = df['Gol Fatti'] - df['Gol Subiti']
            st.dataframe(df.sort_values('Posizione').style.set_properties(**{'font-weight': '900'}).background_gradient(subset=['Punti'], cmap='Blues').format({c: "{:g}" for c in df.columns if c != 'Giocatore'}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 BUDGET DINAMICO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISP'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_tot).fillna(0)
        sel = st.multiselect("**FILTRA VOCI:**", ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISP', 'RECUPERO'], default=['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISP', 'RECUPERO'])
        bu['TOTALE'] = bu[sel].sum(axis=1)
        st.dataframe(bu[['Squadra_N'] + sel + ['TOTALE']].sort_values("TOTALE", ascending=False).style.set_properties(**{'font-weight': '900'}).background_gradient(cmap='YlOrRd', subset=['TOTALE']).format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}), hide_index=True, use_container_width=True)

with t[2]: # ROSE + RICERCA VELOCE
    if f_rs is not None:
        st.subheader("🏃 GESTIONE ROSE")
        c_r1, c_r2 = st.columns([1, 2])
        with c_r1: sq_sel = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()))
        with c_r2: cerca_gioc = st.text_input("🔍 **RICERCA VELOCE CALCIATORE (TUTTA LA LEGA)**", "").upper()
        df_disp = f_rs[f_rs['Nome'].str.contains(cerca_gioc, na=False)] if cerca_gioc else f_rs[f_rs['Squadra_N'] == sq_sel]
        st.dataframe(df_disp[['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].style.set_properties(**{'font-weight': '900'}).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 VINCOLI ATTIVI")
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.set_properties(**{'font-weight': '900'}).format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 SIMULATORE SCAMBI")
    if f_rs is not None:
        s1, s2 = st.columns(2); sq_list = sorted(f_rs['Squadra_N'].unique())
        with s1: sa = st.selectbox("SQUADRA A", sq_list, key="sa"); ga = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga")
        with s2: sb = st.selectbox("SQUADRA B", [s for s in sq_list if s!=sa], key="sb"); gb = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb")
        if ga and gb:
            def get_val(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vm = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
                return {'t': p+v, 'v': v}
            da, db = {n: get_val(n) for n in ga}, {n: get_val(n) for n in gb}
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values()); nt = round((ta+tb)/2)
            gap = ta - tb; col_g = "#d32f2f" if gap > 0 else "#2e7d32" if gap < 0 else "#333"
            st.markdown(f'<div class="punto-incontro-box"><b style="color:{col_g};font-size:1.2em;">GAP: {gap:g}</b><br><small>Media Scambio: {nt:g}</small></div>', unsafe_allow_html=True)
            res1, res2 = st.columns(2)
            with res1:
                for n, i in db.items():
                    nt_i = round((i['t']/tb)*nt) if tb>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#e3f2fd; border:3px solid #1e88e5;"><b>{n}</b><br>VAL: {max(0, nt_i-int(i["v"])):g} + {i["v"]:g} (VINC)</div>', unsafe_allow_html=True)
            with res2:
                for n, i in da.items():
                    nt_i = round((i['t']/ta)*nt) if ta>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#fbe9e7; border:3px solid #e53935;"><b>{n}</b><br>VAL: {max(0, nt_i-int(i["v"])):g} + {i["v"]:g} (VINC)</div>', unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ TAGLI GOLDEN")
    if f_rs is not None:
        st_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_t")
        gt_t = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == st_t]['Nome'].tolist(), key="gt_t")
        if gt_t:
            v_asta = f_rs[(f_rs['Squadra_N'] == st_t) & (f_rs['Nome'] == gt_t)]['Prezzo_N'].iloc[0]
            vm_t = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt_t)] if f_vn is not None else pd.DataFrame()
            v_vinc = vm_t['Tot_Vincolo'].iloc[0] if not vm_t.empty else 0
            rimb = round((v_asta + v_vinc) * 0.6)
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt_t}</div><div class="cut-refund-value">RIMBORSO: {rimb:g} CREDITI</div><br><br>ASTA: {v_asta:g} | VINCOLI: {v_vinc:g}</div>''', unsafe_allow_html=True)

with t[6]: # MERCATO
    st.subheader("🚀 MERCATO GENNAIO")
    with st.expander("➕ AGGIUNGI CESSIONE ESTERA"):
        sc_m = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI IN LISTA"):
            if sc_m != "" and sc_m not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == sc_m].iloc[0]
                vm_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(sc_m)] if f_vn is not None else pd.DataFrame()
                vv_m = vm_m['Tot_Vincolo'].iloc[0] if not vm_m.empty else 0
                s, q = info['Prezzo_N'], info['Quotazione']; rb = (s + q) * 0.5
                nuova = pd.DataFrame([{"GIOCATORE": sc_m, "SQUADRA": info['Squadra_N'], "SPESA": s, "QUOT": q, "RIMB_BASE": rb, "VINCOLO": vv_m, "TOTALE": rb+vv_m, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    if not df_mercato.empty:
        st.write("---")
        for idx, row in df_mercato.iterrows():
            mc1, mc2, mc3, mc4, mc5, mc6 = st.columns([2, 1, 1, 2, 1, 1])
            with mc1: st.markdown(f"**{row['GIOCATORE']}**<br><small>{row['SQUADRA']}</small>", unsafe_allow_html=True)
            with mc2: st.write(f"{row['SPESA']:g}")
            with mc3: st.write(f"{row['QUOT']:g}")
            with mc4: st.markdown(f"<small>50%:{row['RIMB_BASE']:g}+V:{row['VINCOLO']:g}</small>", unsafe_allow_html=True)
            with mc5: st.write(f"**{row['TOTALE']:g}**")
            with mc6:
                st.markdown(f"<span class='{'text-ufficiale' if row['STATO']=='UFFICIALE' else 'text-probabile'}'>{row['STATO']}</span>", unsafe_allow_html=True)
                msc1, msc2 = st.columns(2)
                if row['STATO'] == "PROBABILE" and msc1.button("✅", key=f"u_{idx}"): df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if msc2.button("🗑️", key=f"d_{idx}"): df_mercato = df_mercato.drop(idx); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
