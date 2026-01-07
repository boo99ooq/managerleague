import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("⚽ Centro Direzionale Fantalega")

# 1. FUNZIONE CARICAMENTO BASE (Quella che funzionava all'inizio)
def load_data(file_name):
    if os.path.exists(file_name):
        try:
            # Legge il file e basta, senza filtri strani
            df = pd.read_csv(file_name, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            return df
        except:
            return None
    return None

# Caricamento file
f_sc = load_data("scontridiretti.csv")
f_pt = load_data("classificapunti.csv")
f_rs = load_data("rose_complete.csv")
f_vn = load_data("vincoli.csv")

# Dizionario Budget
budget_fisso = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 2. CREAZIONE DELLE PAGINE
# Se non vede le tab, l'errore è nei nomi dei file su GitHub
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

with tab1:
    st.header("Classifiche")
    col1, col2 = st.columns(2)
    if f_sc is not None:
        with col1: st.write("Scontri"); st.dataframe(f_sc, hide_index=True)
    if f_pt is not None:
        with col2: st.write("Punti"); st.dataframe(f_pt, hide_index=True)

with tab2:
    st.header("Bilancio Economico")
    if f_rs is not None:
        # Assumiamo: 0:Squadra, 3:Prezzo (o ultima colonna)
        c = f_rs.columns
        f_rs[c[-1]] = pd.to_numeric(f_rs[c[-1]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
        bilancio = f_rs.groupby(c[0])[c[-1]].sum().reset_index()
        bilancio['Extra'] = bilancio[c[0]].str.upper().map(budget_fisso).fillna(0)
        bilancio['Totale'] = (bilancio[c[-1]] + bilancio['Extra']).astype(int)
        st.dataframe(bilancio.sort_values('Totale', ascending=False), hide_index=True)

with tab3:
    st.header("Analisi Ruoli")
    if f_rs is not None:
        c = f_rs.columns
        pivot = f_rs.pivot_table(index=c[0], columns=c[2], values=c[1], aggfunc='count').fillna(0).astype(int)
        st.dataframe(pivot)

with tab4:
    st.header("Rose Complete")
    if f_rs is not None:
        c = f_rs.columns
        lista_sq = sorted(f_rs[c[0]].unique())
        scelta = st.selectbox("Seleziona Squadra", lista_sq)
        mostra = f_rs[f_rs[c[0]] == scelta][[c[2], c[1], c[-1]]].sort_values(c[-1], ascending=False)
        st.dataframe(mostra, hide_index=True)

with tab5:
    st.header("Vincoli")
    if f_vn is not None:
        v = f_vn.columns
        # Pulizia numeri
        f_vn[v[2]] = pd.to_numeric(f_vn[v[2]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
        
        c_v1, c_v2 = st.columns([1, 2])
        with c_v1:
            st.write("Somma per Squadra")
            riepilogo = f_vn.groupby(v[0])[v[2]].sum().reset_index().sort_values(v[2], ascending=False)
            st.dataframe(riepilogo, hide_index=True)
        with c_v2:
            st.write("Dettaglio Giocatori")
            sq_v = st.selectbox("Scegli Squadra", sorted(f_vn[v[0]].unique()), key="vin")
            dettaglio = f_vn[f_vn[v[0]] == sq_v][[v[1], v[2], v[-1]]]
            st.dataframe(dettaglio, hide_index=True)
