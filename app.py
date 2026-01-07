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

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "NICHO:79": "NICHOLAS"}

def cv(v):
    if pd.isna(v): return 0.0
    try:
        s = str(v).replace('"', '').replace(',', '.').strip()
        return float(s) if s != "" else 0.0
    except: return 0.0

def clean_name(s):
    if pd.isna(s) or str(s).strip().upper() == "NONE" or str(s).strip() == "": return "SKIP"
    s = str(s).split(':')[0].replace('*', '').replace('"', '').strip().upper()
    return map_n.get(s, s)

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skiprows=1)
            df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO E PULIZIA
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)

if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_name)
    for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if c in f_vn.columns: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn.get('Costo 2026-27', 0) + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)

# TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

# ... (Le prime 5 tab rimangono invariate) ...

with t[5]:
    st.subheader("🔄 Scambi: Meritocrazia su Prezzo + Vincoli Invariati")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        
        def get_details(lista_nomi):
            dati = []
            for n in lista_nomi:
                p = f_rs[f_rs['Nome'] == n]['Prezzo'].values[0]
                v = f_vn[f_vn['Giocatore'] == n]['Spesa Complessiva'].values[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0.0
                dati.append({'Giocatore': n, 'Prezzo Cartellino': p, 'Valore Vincolo': v, 'Totale': p + v})
            return pd.DataFrame(dati)

        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sq_l, key="sa_vinc")
            ga_list = st.multiselect("Cede da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga_vinc")
            df_a = get_details(ga_list)
            if not df_a.empty: st.dataframe(df_a, hide_index=True)

        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sq_l if s != sa], key="sb_vinc")
            gb_list = st.multiselect("Cede da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb_vinc")
            df_b = get_details(gb_list)
            if not df_b.empty: st.dataframe(df_b, hide_index=True)

        if not df_a.empty and not df_b.empty:
            st.write("---")
            val_a_pre, val_b_pre = df_a['Totale'].sum(), df_b['Totale'].sum()
            punto_pareggio = (val_a_pre + val_b_pre) / 2
            
            # Calcolo coefficienti meritocratici basati sul valore totale iniziale
            coeff_a = punto_pareggio / val_a_pre if val_a_pre > 0 else 1
            coeff_b = punto_pareggio / val_b_pre if val_b_pre > 0 else 1

            st.markdown(f"### 🤝 Esito Scambio (Vincoli Ereditati)")
            r1, r2 = st.columns(2)
            
            vals_a_post, vals_b_post = [], []

            with r1:
                st.write(f"**Vanno a {sb} (da {sa}):**")
                for _, r in df_a.iterrows():
                    # Il nuovo valore totale è proporzionale, ma il vincolo resta fisso
                    nuovo_totale = round(r['Totale'] * coeff_a)
                    nuovo_cartellino = nuovo_totale - r['Valore Vincolo']
                    vals_a_post.append(nuovo_totale)
                    st.success(f"🔹 **{r['Giocatore']}**\n\nNuovo Totale: **{nuovo_totale}** \n*(Cartellino: {nuovo_cartellino} + Vincolo: {r['Valore Vincolo']:g})*")
            
            with r2:
                st.write(f"**Vanno a {sa} (da {sb}):**")
                for _, r in df_b.iterrows():
                    nuovo_totale = round(r['Totale'] * coeff_b)
                    nuovo_cartellino = nuovo_totale - r['Valore Vincolo']
                    vals_b_post.append(nuovo_totale)
                    st.success(f"🔸 **{r['Giocatore']}**\n\nNuovo Totale: **{nuovo_totale}** \n*(Cartellino: {nuovo_cartellino} + Vincolo: {r['Valore Vincolo']:g})*")

            st.write("---")
            # Riepilogo finale per conferma
            val_a_post, val_b_post = sum(vals_b_post), sum(vals_a_post)
            comp = pd.DataFrame({
                "Squadra": [sa, sb],
                "Valore Rosa Ante": [val_a_pre, val_b_pre],
                "Valore Rosa Post": [val_a_post, val_b_post],
                "Bilancio Netto": [val_a_post - val_a_pre, val_b_post - val_b_pre]
            })
            st.table(comp)
            st.caption("Nota: Il valore del vincolo è rimasto invariato rispetto ai file originali. È cambiato solo il valore del cartellino per bilanciare lo scambio.")
