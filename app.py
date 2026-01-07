import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lega Manager", layout="wide")
st.title("⚽ Centro Direzionale Fantalega")

# 1. CARICAMENTO FILE (Logica ultra-semplice)
def load_csv(filename):
    if not os.path.exists(filename):
        return None
    try:
        # Prova a leggere il file forzando il separatore corretto
        df = pd.read_csv(filename, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return None

f_sc = load_csv("scontridiretti.csv")
f_pt = load_csv("classificapunti.csv")
f_rs = load_csv("rose_complete.csv")
f_vn = load_csv("vincoli.csv")

# Dizionario Budget
bg = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 2. CREAZIONE TAB
tab_names = []
if f_sc is not None or f_pt is not None: tab_names.append("🏆 Classifiche")
if f_rs is not None: tab_names.extend(["💰 Budget", "🧠 Strategia", "🏃 Rose"])
if f_vn is not None: tab_names.append("📅 Vincoli")

if not tab_names:
    st.warning("⚠️ Nessun file CSV trovato. Assicurati che rose_complete.csv e vincoli.csv siano su GitHub.")
else:
    t = st.tabs(tab_names)
    idx = 0

    # --- CLASSIFICHE ---
    if f_sc is not None or f_pt is not None:
        with t[idx]:
            c1, c2 = st.columns(2)
            if f_sc is not None:
                with c1: st.subheader("🔥 Scontri"); st.dataframe(f_sc, hide_index=True)
            if f_pt is not None:
                with c2: st.subheader("🎯 Punti"); st.dataframe(f_pt, hide_index=True)
        idx += 1

    # --- ROSE / BUDGET / STRATEGIA ---
    if f_rs is not None:
        # Usa le posizioni se i nomi colonna saltano: 0=Squadra, 1=Giocatore, 2=Ruolo, Ultima=Prezzo
        c = f_rs.columns
        f_rs[c[-1]] = pd.to_numeric(f_rs[c[-1]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
        
        with t[idx]: # Budget
            st.subheader("💰 Bilancio")
            e = f_rs.groupby(c[0])[c[-1]].sum().reset_index()
            e['Extra'] = e[c[0]].str.upper().map(bg).fillna(0)
            e['Totale'] = (e[c[-1]] + e['Extra']).astype(int)
            st.dataframe(e.sort_values('Totale', ascending=False), hide_index=True)
        
        with t[idx+1]: # Strategia
            st.subheader("🧠 Ruoli")
            piv = f_rs.pivot_table(index=c[0], columns=c[2], values=c[1], aggfunc='count').fillna(0).astype(int)
            st.dataframe(piv)

        with t[idx+2]: # Rose
            sq = st.selectbox("Seleziona Squadra:", sorted(f_rs[c[0]].unique()))
            res = f_rs[f_rs[c[0]] == sq][[c[2], c[1], c[-1]]].sort_values(c[-1], ascending=False)
            st.dataframe(res, hide_index=True)
        idx += 3

    # --- VINCOLI (Layout originale richiesto) ---
    if f_vn is not None:
        with t[idx]:
            st.subheader("📅 Vincoli")
            v = f_vn.columns
            f_vn[v[2]] = pd.to_numeric(f_vn[v[2]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("**Crediti Impegnati**")
                deb = f_vn.groupby(v[0])[v[2]].sum().reset_index().sort_values(v[2], ascending=False)
                st.dataframe(deb, hide_index=True)
            with c2:
                st.write("**Dettaglio Giocatori**")
                sel = st.selectbox("Scegli Squadra:", sorted(f_vn[v[0]].unique()), key="v_sel")
                det = f_vn[f_vn[v[0]] == sel][[v[1], v[2], v[-1]]].copy()
                st.dataframe(det, hide_index=True)
