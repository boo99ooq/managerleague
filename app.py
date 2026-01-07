import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Budget e Mappature
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "NICHO:79": "NICHOLAS"}

def cv(v):
    if pd.isna(v): return 0.0
    try:
        s = str(v).replace('"', '').replace(',', '.').strip()
        return float(s) if s != "" else 0.0
    except: return 0.0

def normalize_text(s):
    if pd.isna(s): return ""
    s = str(s).upper().replace('Ó', 'O').replace('Í', 'I').replace('Á', 'A').replace('Ú', 'U').replace('É', 'E').replace('È', 'E')
    return s.replace('.', '').replace('*', '').replace('"', '').replace('-', ' ').strip()

def clean_name(s):
    s = normalize_text(s).split(':')[0]
    return map_n.get(s, s)

def get_match_key(s):
    """Estrae la parola più lunga (il cognome) per facilitare il match"""
    parts = normalize_text(s).split()
    if not parts: return ""
    # Prendiamo la parola più lunga, solitamente è il cognome (es: MARTINEZ vs L)
    return max(parts, key=len)

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO DATI
f_sc, f_pt, f_rs, f_vn, f_qt = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv"), ld("quotazioni.csv")

# 3. ELABORAZIONE QUOTAZIONI (R, Nome, Qt.A)
if f_qt is not None:
    f_qt = f_qt.rename(columns={'R': 'Ruolo_QT', 'Nome': 'Nome_QT', 'Qt.A': 'Quotazione'})
    f_qt['MatchKey'] = f_qt['Nome_QT'].apply(get_match_key)
    f_qt['Quotazione'] = f_qt['Quotazione'].apply(cv)
    # Mappatura ruoli abbreviati
    r_map = {'P':'PORTIERE', 'D':'DIFENSORE', 'C':'CENTROCAMPISTA', 'A':'ATTACCANTE'}
    f_qt['Ruolo_QT_Clean'] = f_qt['Ruolo_QT'].apply(lambda x: r_map.get(str(x).upper().strip(), str(x).upper().strip()))

# 4. ELABORAZIONE ROSE E UNIONE
if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Ruolo'] = f_rs['Ruolo'].apply(normalize_text)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    f_rs['MatchKey'] = f_rs['Nome'].apply(get_match_key)
    
    if f_qt is not None:
        # Uniamo le rose con le quotazioni su Cognome e Ruolo
        f_rs = pd.merge(f_rs, f_qt[['MatchKey', 'Ruolo_QT_Clean', 'Quotazione']], 
                        left_on=['MatchKey', 'Ruolo'], right_on=['MatchKey', 'Ruolo_QT_Clean'], 
                        how='left').drop('Ruolo_QT_Clean', axis=1)
        f_rs['Quotazione'] = f_rs['Quotazione'].fillna(0)
        f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']
    else:
        f_rs['Quotazione'], f_rs['Plusvalenza'] = 0.0, 0.0

# 5. ELABORAZIONE VINCOLI (FIX ERRORE SOMMA)
if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_name)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn[v_cols].sum(axis=1)

def style_rose(row):
    r = str(row["Ruolo"]).upper()
    bg = "#FFFFFF"
    if 'PORTIERE' in r or r == 'P': bg = '#E3F2FD'
    elif 'DIFENSORE' in r or r == 'D': bg = '#E8F5E9'
    elif 'CENTROCAMPISTA' in r or r == 'C': bg = '#FFFDE7'
    elif 'ATTACCANTE' in r or r == 'A': bg = '#FFEBEE'
    return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)

# 6. TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1:
            st.subheader("🔥 Scontri")
            st.dataframe(f_sc.style.set_properties(**{'font-weight': 'bold'}), hide_index=True, use_container_width=True)
    if f_pt is not None:
        with c2:
            st.subheader("🎯 Punti")
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens').set_properties(**{'font-weight': 'bold'}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 Bilancio Globale")
        eco = f_rs.groupby('Fantasquadra').agg({'Prezzo': 'sum', 'Quotazione': 'sum'}).reset_index()
        eco.columns = ['Fantasquadra', 'Investimento', 'Valore Mercato']
        eco['Crediti Disponibili'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        
        if f_vn is not None:
            v_sum = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index()
            v_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, v_sum, on='Fantasquadra', how='left').fillna(0)
        else: eco['Vincoli'] = 0
        
        eco['Patrimonio'] = eco['Valore Mercato'] + eco['Crediti Disponibili'] + eco['Vincoli']
        st.dataframe(eco.sort_values('Patrimonio', ascending=False).style.background_gradient(subset=['Valore Mercato'], cmap='Greens').format({c: "{:g}" for c in eco.columns if c != 'Fantasquadra'}).set_properties(**{'font-weight': 'bold'}), hide_index=True, use_container_width=True)

with t[3]: # ROSE
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        sq = st.selectbox("Seleziona Squadra:", sq_l, key="rose_sel")
        df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione', 'Plusvalenza']].copy()
        st.dataframe(df_sq.style.apply(style_rose, axis=1).background_gradient(subset=['Plusvalenza'], cmap='RdYlGn').format({"Prezzo": "{:g}", "Quotazione": "{:g}", "Plusvalenza": "{:+g}"}), hide_index=True, use_container_width=True)
        st.metric("Plusvalenza Totale Rosa", f"{df_sq['Plusvalenza'].sum():+g}")

with t[5]: # SCAMBI
    st.subheader("🔄 Simulatore Scambi Meritocratico")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        def get_val(n):
            row = f_rs[f_rs['Nome'] == n].iloc[0]
            p = row['Prezzo']
            v = f_vn[f_vn['Giocatore'] == n]['Spesa Complessiva'].values[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0.0
            return p, v
        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sq_l, key="sa_f")
            ga = st.multiselect("Cede da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga_f")
            va = sum([get_val(x)[0] + get_val(x)[1] for x in ga]) if ga else 0
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sq_l if s != sa], key="sb_f")
            gb = st.multiselect("Cede da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb_f")
            vb = sum([get_val(x)[0] + get_val(x)[1] for x in gb]) if gb else 0
        if ga and gb:
            tot = va + vb
            target = tot / 2
            ca, cb = target/va if va > 0 else 1, target/vb if vb > 0 else 1
            st.write("---")
            st.markdown(f"### 🤝 Punto di Incontro: **{target:g}**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**A {sb}:**")
                for n in ga:
                    p, v = get_val(n)
                    nv = round((p+v)*ca)
                    st.success(f"{n}: **{nv}** (Cart: {nv-v} + Vinc: {v})")
            with col_b:
                st.write(f"**A {sa}:**")
                for n in gb:
                    p, v = get_val(n)
                    nv = round((p+v)*cb)
                    st.success(f"{n}: **{nv}** (Cart: {nv-v} + Vinc: {v})")
