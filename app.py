import streamlit as st
import pandas as pd
import os

# 1. SETUP BASE
st.set_page_config(page_title="Lega Manager", layout="wide")
st.title("⚽ Centro Direzionale Fantalega")

# Configurazione Budget (Dizionario originale)
bg_extra = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 2. FUNZIONE DI CARICAMENTO SEMPLICE (Senza filtri strani)
def load_data(name):
    actual_file = next((f for f in os.listdir(".") if f.lower() == name.lower()), None)
    if actual_file:
        try:
            # Legge il file rilevando automaticamente se c'è , o ;
            df = pd.read_csv(actual_file, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except:
            return None
    return None

# Caricamento dei 4 file
f_sc = load_data("scontridiretti.csv")
f_pt = load_data("classificapunti.csv")
f_rs = load_data("rose_complete.csv")
f_vn = load_data("vincoli.csv")

# 3. CREAZIONE TAB (Appaiono solo se il file esiste)
tabs_to_create = []
if f_sc is not None or f_pt is not None: tabs_to_create.append("🏆 Classifiche")
if f_rs is not None: tabs_to_create.extend(["💰 Budget", "🧠 Strategia", "🏃 Rose"])
if f_vn is not None: tabs_to_create.append("📅 Vincoli")

if not tabs_to_create:
    st.error("⚠️ Attenzione: Non trovo i file CSV su GitHub. Verifica i nomi dei file!")
else:
    t = st.tabs(tabs_to_create)
    idx = 0

    # --- TAB CLASSIFICHE ---
    if f_sc is not None or f_pt is not None:
        with t[idx]:
            c1, c2 = st.columns(2)
            if f_sc is not None:
                with c1:
                    st.subheader("🔥 Scontri Diretti")
                    st.dataframe(f_sc, hide_index=True, use_container_width=True)
            if f_pt is not None:
                with c2:
                    st.subheader("🎯 Classifica Punti")
                    st.dataframe(f_pt, hide_index=True, use_container_width=True)
        idx += 1

    # --- TAB ROSE / BUDGET / STRATEGIA ---
    if f_rs is not None:
        c = f_rs.columns # 0:Squadra, 1:Nome, 2:Ruolo, 3:Prezzo
        # Pulizia prezzo (prende l'ultima colonna e la rende numero)
        f_rs[c[-1]] = pd.to_numeric(f_rs[c[-1]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)

        with t[idx]: # BUDGET
            st.subheader("💰 Bilancio Crediti")
            spesa = f_rs.groupby(c[0])[c[-1]].sum().reset_index()
            spesa['Extra'] = spesa[c[0]].str.upper().map(bg_extra).fillna(0)
            spesa['Totale'] = (spesa[c[-1]] + spesa['Extra']).astype(int)
            st.dataframe(spesa.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
        
        with t[idx+1]: # STRATEGIA
            st.subheader("🧠 Distribuzione Ruoli")
            pivot = f_rs.pivot_table(index=c[0], columns=c[2], values=c[1], aggfunc='count').fillna(0).astype(int)
            st.dataframe(pivot, use_container_width=True)

        with t[idx+2]: # ROSE
            st.subheader("🏃 Rose Squadre")
            squadre = sorted(f_rs[c[0]].unique())
            sel_sq = st.selectbox("Seleziona Squadra:", squadre)
            rosa = f_rs[f_rs[c[0]] == sel_sq][[c[2], c[1], c[-1]]].sort_values(c[-1], ascending=False)
            st.dataframe(rosa, hide_index=True, use_container_width=True)
        idx += 3

    # --- TAB VINCOLI (Layout pulito richiesto) ---
    if f_vn is not None:
        with t[idx]:
            st.subheader("📅 Gestione Vincoli")
            v = f_vn.columns # 0:Squadra, 1:Nome, 2:Costo, 3:Anni
            f_vn[v[2]] = pd.to_numeric(f_vn[v[2]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
            
            v_c1, v_c2 = st.columns([1, 2])
            with v_c1:
                st.write("**Crediti Impegnati**")
                debiti = f_vn.groupby(v[0])[v[2]].sum().reset_index().sort_values(v[2], ascending=False)
                st.dataframe(debiti, hide_index=True, use_container_width=True)
            with v_c2:
                st.write("**Dettaglio Giocatori**")
                sel_v = st.selectbox("Visualizza Squadra:", sorted(f_vn[v[0]].unique()), key="v_sel")
                det = f_vn[f_vn[v[0]] == sel_v][[v[1], v[2], v[-1]]].copy()
                st.dataframe(det, hide_index=True, use_container_width=True)
