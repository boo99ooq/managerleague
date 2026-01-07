import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="Fantalega")
st.title("⚽ Centro Direzionale")

# Budget Extra
bg = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

def load_clean(name):
    """Cerca il file e lo pulisce da righe sporche (asterischi, titoli, ecc.)"""
    for f in os.listdir("."):
        if f.lower() == name.lower():
            try:
                df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig')
                # Rimuove righe che contengono troppi asterischi o sono riepiloghi
                df = df[~df.iloc[:, 0].astype(str).str.contains(r'\*|Riepilogo|SQUADRA', na=False, case=False)]
                df = df.dropna(how='all').dropna(axis=1, how='all')
                df.columns = [str(c).strip().upper() for c in df.columns]
                # Pulisce ogni cella da asterischi residui
                df = df.apply(lambda x: x.astype(str).str.replace('*', '', regex=False).str.strip())
                return df
            except: return None
    return None

def sc(obj):
    """Centra il testo nelle tabelle"""
    s = obj if hasattr(obj, 'style') == False else obj.style
    return s.set_properties(**{'text-align':'center'}).set_table_styles([dict(selector='th', props=[('text-align','center')])])

# Caricamento
f_sc = load_clean("scontridiretti.csv")
f_pt = load_clean("classificapunti.csv")
f_rs = load_clean("rose_complete.csv")
f_vn = load_clean("vincoli.csv")

# Sidebar Status
st.sidebar.write("### 📂 Status File")
st.sidebar.write("Rose:", "✅" if f_rs is not None else "❌")
st.sidebar.write("Vincoli:", "✅" if f_vn is not None else "❌")

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

# --- CLASSIFICHE ---
with t[0]:
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1: st.subheader("🔥 Scontri"); st.dataframe(sc(f_sc), hide_index=True)
    if f_pt is not None:
        with c2: st.subheader("🎯 Punti"); st.dataframe(sc(f_pt), hide_index=True)

# --- ROSE / BUDGET / STRATEGIA ---
if f_rs is not None and len(f_rs.columns) >= 3:
    c = f_rs.columns
    f_rs[c[-1]] = pd.to_numeric(f_rs[c[-1]].str.replace(',','.'), errors='coerce').fillna(0)
    
    with t[1]: # Budget
        e = f_rs.groupby(c[0])[c[-1]].sum().reset_index()
        e['EXTRA'] = e[c[0]].str.upper().map(bg).fillna(0)
        e['TOTALE'] = (e[c[-1]] + e['EXTRA']).astype(int)
        st.dataframe(sc(e.sort_values('TOTALE', ascending=False)), hide_index=True)
    
    with t[2]: # Strategia
        piv = f_rs.pivot_table(index=c[0], columns=c[2], values=c[1], aggfunc='count').fillna(0).astype(int)
        st.dataframe(sc(piv))

    with t[3]: # Rose
        sq = st.selectbox("Squadra:", sorted(f_rs[c[0]].unique()), key="sq_rose")
        d_sq = f_rs[f_rs[c[0]] == sq][[c[2], c[1], c[-1]]].sort_values(c[-1], ascending=False)
        st.dataframe(sc(d_sq.style.background_gradient(subset=[c[-1]], cmap='Greens')), hide_index=True)

# --- VINCOLI (Layout richiesto) ---
if f_vn is not None and len(f_vn.columns) >= 3:
    with t[4]:
        v = f_vn.columns
        # Assicuriamoci che Costo e Anni siano numeri
        f_vn[v[2]] = pd.to_numeric(f_vn[v[2]].str.replace(',','.'), errors='coerce').fillna(0)
        f_vn[v[-1]] = pd.to_numeric(f_vn[v[-1]], errors='coerce').fillna(0).astype(int)

        v_col1, v_col2 = st.columns([1, 2])
        
        with v_col1:
            st.write("### 💰 Crediti Impegnati")
            deb = f_vn.groupby(v[0])[v[2]].sum().reset_index().sort_values(v[2], ascending=False)
            st.dataframe(sc(deb), hide_index=True, use_container_width=True)
        
        with v_col2:
            st.write("### 🏃 Dettaglio Giocatori")
            sv = st.selectbox("Seleziona Squadra:", sorted(f_vn[v[0]].unique()), key="v_s")
            det = f_vn[f_vn[v[0]] == sv][[v[1], v[2], v[-1]]].copy()
            # Colore rosso se scade tra 1 anno
            st_v = det.sort_values(v[-1]).style.map(lambda x: 'background-color:#ffcdd2' if x==1 else '', subset=[v[-1]])
            st.dataframe(sc(st_v), hide_index=True, use_container_width=True)
