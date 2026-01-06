import streamlit as st
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.title("⚽ La mia Fantalega Manageriale")

# 2. Caricamento file nella barra laterale
st.sidebar.header("Gestione Dati")
file_caricato = st.sidebar.file_uploader("Carica il file delle rose", type="csv")

if file_caricato is not None:
    try:
        # Lettura del file (gestisce vari separatori automaticamente)
        file_caricato.seek(0)
        df = pd.read_csv(file_caricato, sep=None, engine='python', encoding='latin-1')
        
        # PULIZIA DATI
        df = df.dropna(how='all').reset_index(drop=True)
        df.columns = df.columns.str.strip()
        
        # Mappatura colonne (per gestire minuscole/maiuscole)
        mappa_colonne = {
            'ruolo': 'Ruolo',
            'Calciatore': 'Calciatore',
            'prezzo': 'Prezzo',
            'Fantasquadra': 'Fantasquadra'
        }
        df = df.rename(columns=mappa_colonne)

        # Convertiamo il Prezzo in numero
        if 'Prezzo' in df.columns:
            df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce').fillna(0)

        # Creazione delle Tab
        tab1, tab2 = st.tabs(["📊 Valore Rose", "🏃 Dettaglio Rose"])

        with tab1:
            st.subheader("Valore Complessivo delle Rose")
            
            # Calcoliamo solo il valore totale speso per ogni squadra
            analisi_economica = df.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
            analisi_economica.columns = ['Fantasquadra', 'Valore Totale Rosa']
            
            # Grafico e Tabella
            col_graf, col_tab = st.columns([2, 1])
            with col_graf:
                # Mostra un grafico a barre del valore delle rose
                st.bar_chart(data=analisi_economica, x='Fantasquadra', y='Valore Totale Rosa')
            with col_tab:
                # Tabella ordinata dal valore più alto al più basso
                st.dataframe(
                    analisi_economica.sort_values(by='Valore Totale Rosa', ascending=False), 
                    hide_index=True,
                    use_container_width=True
                )

        with tab2:
            squadre_disponibili = [s for s in df['Fantasquadra'].unique() if pd.notna(s)]
            scelta = st.selectbox("Scegli una Fantasquadra:", squadre_disponibili)
            
            # Filtriamo la rosa della squadra scelta
            rosa_squadra = df[df['Fantasquadra'] == scelta]
            
            # ORDINE COLONNE: Ruolo per primo
            ordine_visualizzazione = ['Ruolo', 'Calciatore', 'Prezzo']
            
            st.write(f"**Giocatori totali in lista:** {len(rosa_squadra.dropna(subset=['Calciatore']))}")
            
            # Mostriamo la tabella con il ruolo in prima posizione
            st.dataframe(
                rosa_squadra[ordine_visualizzazione].sort_values(by='Ruolo'), 
                use_container_width=True, 
                hide_index=True
            )

    except Exception as e:
        st.error(f"Errore durante la lettura del file: {e}")
else:
    st.info("👋 Benvenuto! Carica il file delle rose per visualizzare l'analisi della lega.")
