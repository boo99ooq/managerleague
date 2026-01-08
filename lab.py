# --- CSS AGGIORNATO PER IL PUNTO DI INCONTRO RISTRETTO ---
st.markdown("""
<style>
    .punto-incontro-wrapper {
        display: flex;
        justify-content: center;
        margin: 10px 0;
    }
    .punto-incontro-box {
        background-color: #fff3e0;
        padding: 8px 25px;
        border-radius: 12px;
        border: 3px solid #ff9800;
        text-align: center;
        width: fit-content;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stat-label { font-size: 0.8em; color: #555; font-weight: 400 !important; }
</style>
""", unsafe_allow_html=True)

# --- LOGICA TAB SCAMBI ---
with t[4]: 
    st.subheader("🔄 **SIMULATORE SCAMBI GOLDEN**")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        lista_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        with c1: 
            sa = st.selectbox("**SQUADRA A**", lista_sq, key="sa_f")
            ga = st.multiselect("**ESCONO DA A**", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
        with c2: 
            sb = st.selectbox("**SQUADRA B**", [s for s in lista_sq if s != sa], key="sb_f")
            gb = st.multiselect("**ESCONO DA B**", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
        
        if ga and gb:
            def get_i(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0] if n in f_rs['Nome'].values else 0
                v_row = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = v_row['Tot_Vincolo'].iloc[0] if not v_row.empty else 0
                return {'t': p + v, 'p': p, 'v': v}
            
            p_a_v = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
            p_b_v = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb, 0)
            
            dict_a = {n: get_i(n) for n in ga}; dict_b = {n: get_i(n) for n in gb}
            tot_a, tot_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values())
            nuovo_tot = round((tot_a + tot_b) / 2)
            
            # --- PUNTO DI INCONTRO RISTRETTO E CENTRALE ---
            gap = tot_a - tot_b
            color_gap = "#d32f2f" if gap > 0 else "#2e7d32" if gap < 0 else "#333"
            testo_gap = f"GAP: +{int(gap)} (A > B)" if gap > 0 else f"GAP: +{int(abs(gap))} (B > A)" if gap < 0 else "EQUILIBRIO PERFETTO"
            
            st.markdown(f'''
                <div class="punto-incontro-wrapper">
                    <div class="punto-incontro-box">
                        <span style="font-size: 0.75em; color: #666; text-transform: uppercase;">Punto di Incontro</span><br>
                        <b style="font-size: 1.2em; color: {color_gap};">{testo_gap}</b><br>
                        <span style="font-size: 0.85em;">Media: {nuovo_tot}</span>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

            # --- RISULTATI SCAMBIO ---
            res_a, res_b = st.columns(2)
            with res_a:
                st.write(f"👉 **Ricevuti da {sa}**")
                for n, i in dict_b.items():
                    peso = i['t']/tot_b if tot_b > 0 else 1/len(gb)
                    nuovo_t = round(peso*nuovo_tot)
                    incidenza = (i['t']/p_b_v)*100 if p_b_v > 0 else 0
                    st.markdown(f'''<div class="player-card" style="background-color: #e3f2fd; border: 3px solid #1e88e5;">
                        <b>{n}</b><br><span class="stat-label">VAL REALE:</span> <b>{max(0, nuovo_t-int(i['v']))}</b> <span class="stat-label">+ VINC:</span> <b>{int(i['v'])}</b><br>
                        <hr style="margin:5px 0; border:0; border-top: 1px solid #1e88e5;">
                        <span class="stat-label">PESO PATR:</span> <b>{incidenza:.1f}%</b> | <span class="stat-label">ANTE:</span> <b>{int(i['t'])}</b>
                    </div>''', unsafe_allow_html=True)
            with res_b:
                st.write(f"👉 **Ricevuti da {sb}**")
                for n, i in dict_a.items():
                    peso = i['t']/tot_a if tot_a > 0 else 1/len(ga)
                    nuovo_t = round(peso*nuovo_tot)
                    incidenza = (i['t']/p_a_v)*100 if p_a_v > 0 else 0
                    st.markdown(f'''<div class="player-card" style="background-color: #fbe9e7; border: 3px solid #e53935;">
                        <b>{n}</b><br><span class="stat-label">VAL REALE:</span> <b>{max(0, nuovo_t-int(i['v']))}</b> <span class="stat-label">+ VINC:</span> <b>{int(i['v'])}</b><br>
                        <hr style="margin:5px 0; border:0; border-top: 1px solid #e53935;">
                        <span class="stat-label">PESO PATR:</span> <b>{incidenza:.1f}%</b> | <span class="stat-label">ANTE:</span> <b>{int(i['t'])}</b>
                    </div>''', unsafe_allow_html=True)
            
            # Patrimoni post-scambio
            diff = nuovo_tot - tot_a
            col_p1, col_p2 = st.columns(2)
            col_p1.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2>{int(p_a_v + diff)}</h2><small>PRIMA: {int(p_a_v)} | VAR: {int(diff):+d}</small></div>', unsafe_allow_html=True)
            col_p2.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2>{int(p_b_v - diff)}</h2><small>PRIMA: {int(p_b_v)} | VAR: {int(-diff):+d}</small></div>', unsafe_allow_html=True)
