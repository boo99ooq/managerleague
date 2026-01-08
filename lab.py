import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS DEFINITIVO (Grassetto estremo 900 su tutto, card e box originali)
st.markdown("""
<style>
    /* ... qui ci sono i tuoi stili esistenti (es. .player-card, .patrimonio-box) ... */
    /* NON cancellarli, vai semplicemente a capo dopo l'ultima parentesi graffa } */

    .refund-box-pastello {
        padding: 15px;
        border-radius: 12px;
        border: 3px solid #333;
        text-align: center;
        min-height: 130px;
        box-shadow: 4px 4px 0px #333;
        margin-bottom: 15px;
    }

    /* Palette Colori Pastello */
    .bg-azzurro { background-color: #E3F2FD !important; }
    .bg-verde   { background-color: #E8F5E9 !important; }
    .bg-rosa    { background-color: #FCE4EC !important; }
    .bg-giallo  { background-color: #FFFDE7 !important; }
    .bg-arancio { background-color: #FFF3E0 !important; }
    .bg-viola   { background-color: #F3E5F5 !important; }
</style>
""", unsafe_allow_html=True) # <-- Assicurati che le virgolette e la parentesi chiudano quist.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .cut-player-name { font-size: 3.5em; color: #d32f2f; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 2px solid #333; text-align: center; min-height: 125px; }
    .status-ufficiale { color: #ffffff !important; background-color: #2e7d32; padding: 4px 10px; border-radius: 6px; }
    .status-probabile { color: #ffffff !important; background-color: #ed6c02; padding: 4px 10px; border-radius: 6px; }
    .text-ufficiale { color: #2e7d32; } .text-probabile { color: #ed6c02; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def bold_df(df):
    return df.style.set_properties(**{'font-weight': '900', 'color': 'black'})

def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
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
    if f_qt is not None: f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_mercato = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA CALCIATORE**")
    if f_rs is not None:
        cerca_side = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in cerca_side:
            d_g = f_rs[f_rs['Nome'] == n].iloc[0]
            v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(n)] if f_vn is not None else pd.DataFrame()
            vv = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
            r = str(d_g['Ruolo']).upper()
            bg_c = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'''<div class="player-card" style="background-color:{bg_c};"><b>{n}</b> ({d_g['Squadra_N']})<br>ASTA: {int(d_g['Prezzo_N'])} | VINC: {int(vv)}<br>QUOT: {int(d_g['Quotazione'])}</div>''', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num) if 'Media' in f_pt.columns else 0.0
            st.dataframe(bold_df(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione')).background_gradient(subset=['P_N','FM'], cmap='YlGn').format({"P_N":"{:g}", "FM":"{:.2f}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            for col in ['Punti', 'Gol Fatti', 'Gol Subiti']: f_sc[col] = f_sc[col].apply(to_num)
            f_sc['DR'] = f_sc['Gol Fatti'] - f_sc['Gol Subiti']
            st.dataframe(bold_df(f_sc[['Posizione','Giocatore','Punti','Gol Fatti','Gol Subiti','DR']].sort_values('Posizione')).background_gradient(subset=['Punti'], cmap='Blues').format({c: "{:g}" for c in ['Punti','Gol Fatti','Gol Subiti','DR']}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['MERCATO'] = bu['Squadra_N'].map(rimborsi_mercato).fillna(0)
        sel = st.multiselect("**FILTRA VOCI PATRIMONIO:**", ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'MERCATO'], default=['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'MERCATO'])
        bu['TOTALE'] = bu[sel].sum(axis=1) if sel else 0
        num_cols = bu.select_dtypes(include=['number']).columns
        st.dataframe(bold_df(bu[['Squadra_N'] + sel + ['TOTALE']].sort_values('TOTALE', ascending=False)).background_gradient(cmap='YlOrRd', subset=['TOTALE']).format({c: "{:g}" for c in num_cols}), hide_index=True, use_container_width=True)

with t[2]: # ROSE (RIPRISTINATA)
    if f_rs is not None:
        st.subheader("🏃 GESTIONE ROSE")
        cr1, cr2 = st.columns([1, 2])
        with cr1: sq_r = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_rs['Squadra_N'].unique()), key="sq_rose_final")
        with cr2: cerca_r = st.text_input("🔍 **CERCA GIOCATORE**", "").upper()
        df_r = f_rs.copy()
        if sq_r != "TUTTE": df_r = df_r[df_r['Squadra_N'] == sq_r]
        if cerca_r: df_r = df_r[df_r['Nome'].str.upper().str.contains(cerca_r, na=False)]
        
        def color_ruolo(val):
            v = str(val).upper()
            if 'POR' in v: return 'background-color: #FCE4EC'
            if 'DIF' in v: return 'background-color: #E8F5E9'
            if 'CEN' in v: return 'background-color: #E3F2FD'
            if 'ATT' in v: return 'background-color: #FFFDE7'
            return ''
        st.dataframe(bold_df(df_r[['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]).applymap(color_ruolo, subset=['Ruolo']).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI ATTIVI")
        sq_v = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()), key="v_fil_fin")
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(bold_df(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False)).format({"Tot_Vincolo":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 SCAMBI GOLDEN")
    if f_rs is not None:
        s1, s2 = st.columns(2)
        with s1: sa = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sa"); ga = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist())
        with s2: sb = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sa], key="sb"); gb = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist())
        if ga and gb:
            def gv(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vm = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
                return {'t': p+v, 'v': v}
            da, db = {n: gv(n) for n in ga}, {n: gv(n) for n in gb}
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values()); nt = round((ta+tb)/2); gap = ta-tb
            st.markdown(f'<div class="punto-incontro-box">GAP: {gap:g} | MEDIA: {nt:g}</div>', unsafe_allow_html=True)
            ra, rb = st.columns(2)
            with ra:
                for n, i in db.items():
                    ni = round((i['t']/tb)*nt) if tb>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#e3f2fd; border:3px solid #1e88e5;"><b>{n}</b><br><small>VAL: {max(0, ni-int(i["v"])):g} + {i["v"]:g} (V) | ANTE: {i["t"]:g}</small></div>', unsafe_allow_html=True)
            with rb:
                for n, i in da.items():
                    ni = round((i['t']/ta)*nt) if ta>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#fbe9e7; border:3px solid #e53935;"><b>{n}</b><br><small>VAL: {max(0, ni-int(i["v"])):g} + {i["v"]:g} (V) | ANTE: {i["t"]:g}</small></div>', unsafe_allow_html=True)
            pa = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
            pb = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb, 0)
            diff = nt - ta
            cp1, cp2 = st.columns(2)
            cp1.markdown(f'<div class="patrimonio-box">NUOVO {sa}<br><h2>{int(pa+diff)}</h2><small>PRIMA: {int(pa)}</small></div>', unsafe_allow_html=True)
            cp2.markdown(f'<div class="patrimonio-box">NUOVO {sb}<br><h2>{int(pb-diff)}</h2><small>PRIMA: {int(pb)}</small></div>', unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ TAGLI GOLDEN")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_tag_p")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
        if gt:
            v_a = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            vm = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame()
            vv = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2.2em; color:#2e7d32;">RIMBORSO: {round((v_a+vv)*0.6):g}</div><br>ASTA: {v_a:g} | VINCOLI: {vv:g}</div>''', unsafe_allow_html=True)

with t[6]: # MERCATO
    st.subheader("🚀 MERCATO GENNAIO")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI"):
            if sc != "" and sc not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == sc].iloc[0]; vm_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(sc)] if f_vn is not None else pd.DataFrame()
                vv = vm_m['Tot_Vincolo'].iloc[0] if not vm_m.empty else 0
                nuova = pd.DataFrame([{"GIOCATORE": sc, "SQUADRA": info['Squadra_N'], "TOTALE": ((info['Prezzo_N'] + info['Quotazione'])*0.5)+vv, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    if not df_mercato.empty:
        for idx, row in df_mercato.iterrows():
            mc1, mc2, mc3, mc4 = st.columns([2, 1, 1, 1])
            with mc1: st.write(f"**{row['GIOCATORE']}** ({row['SQUADRA']})")
            with mc2: st.write(f"TOT: {row['TOTALE']:g}")
            with mc3: st.markdown(f"<span class=\"{'status-ufficiale' if row['STATO']=='UFFICIALE' else 'status-probabile'}\">{row['STATO']}</span>", unsafe_allow_html=True)
            with mc4:
                if row['STATO'] == "PROBABILE" and st.button("✅", key=f"u_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if st.button("🗑️", key=f"d_{idx}"):
                    df_mercato = df_mercato.drop(idx).to_csv(FILE_DB, index=False); st.rerun()
        st.write("---")
        sq_m = df_mercato.groupby(['SQUADRA', 'STATO'])['TOTALE'].sum().unstack(fill_value=0)
        if 'UFFICIALE' not in sq_m.columns: sq_m['UFFICIALE'] = 0
        if 'PROBABILE' not in sq_m.columns: sq_m['PROBABILE'] = 0
        sq_m['TOT_GEN'] = sq_m['UFFICIALE'] + sq_m['PROBABILE']
        cols_m = st.columns(4)
        for i, (sq_n, data) in enumerate(sq_m.sort_values('TOT_GEN', ascending=False).iterrows()):
            with cols_m[i % 4]:
                st.markdown(f'<div class="refund-box"><small>{sq_n}</small><br><b>+{data["TOT_GEN"]:g}</b><br><hr style="margin:5px 0; border:0; border-top:1px solid #ddd;"><span class="text-ufficiale">Uff: {data["UFFICIALE"]:g}</span><br><span class="text-probabile">Prob: {data["PROBABILE"]:g}</span></div>', unsafe_allow_html=True)
