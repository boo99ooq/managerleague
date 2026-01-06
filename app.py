import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# --- FUNZIONI DI CARICAMENTO ROBUSTE ---
def carica_dati(file):
    if file is None: return None
    try:
        # Prova a leggere prima con virgola, poi con punto e virgola
        file.seek(0)
        df = pd.read_csv(file, sep=None, engine='python', encoding='utf-8-sig')
        
        # Pulizia base: togli spazi dai nomi delle colonne
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
        return None

# --- INTERFACCIA ---
st.title("⚽ Centro Direzionale Fantalega")

st.sidebar.header("📂 Caricamento Dati")
file_rose = st.sidebar.file_uploader("1. Carica nuove rose muynov25.csv", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica vincoli 26.csv", type="csv")

df_rose = carica_dati(file_rose)
df_vincoli = carica_dati(file_vincoli)

if df_rose is not None:
    # Debug: Mostra le colonne trovate se non vedi nulla
    if st.sidebar.checkbox("Mostra nomi colonne"):
        st.sidebar.write("Colonne Rose:", list(df_rose.columns))
    
    # Adattamento nomi colonne (Gestisce maiuscole/minuscole)
    df_rose.columns = [c.capitalize() for c in df_rose.columns]
    
    # Filtro per evitare righe vuote
    df_rose = df_rose.dropna(subset=['Nome']) if 'Nome' in df_rose.columns else df_rose

    tabs = st.tabs(["📊 Riepilogo", "📈 Analisi", "🏃 Rose", "🏆 Top 20"])

    with tabs[0]:
        st.subheader("Situazione Economica")
        if 'Fantasquadra' in df_rose.columns and 'Prezzo' in df_rose.columns:
            df_rose['Prezzo'] = pd.to_numeric(df_rose['Prezzo'], errors='coerce').fillna(0)
            resoconto = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
            st.dataframe(resoconto, use_container_width=True)
        else:
            st.warning("Verifica che nel CSV ci siano le colonne 'Fantasquadra' e 'Prezzo'")

    with tabs[2]:
        if 'Fantasquadra' in df_rose.columns:
            squadra = st.selectbox("Seleziona Squadra", df_rose['Fantasquadra'].unique())
            st.table(df_rose[df_rose['Fantasquadra'] == squadra])

    with tabs[3]:
        st.subheader("💎 I 20 più costosi")
        if 'Prezzo' in df_rose.columns:
            top20 = df_rose.sort_values(by='Prezzo', ascending=False).head(20)
            st.dataframe(top20, use_container_width=True)

else:
    st.info("👋 Benvenuto! Carica i file CSV dalla barra laterale per visualizzare i dati della Lega.")
