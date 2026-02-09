import streamlit as st
import pandas as pd
import numpy as np

# Configurazione pagina
st.set_page_config(page_title="Monitoraggio Resa FV", layout="wide")

def load_irraggiamento():
    # Carica il file locale irraggiamento.csv
    # Il file ha le prime due righe sporche e usa il punto e virgola
    df = pd.read_csv('irraggiamento.csv', sep=';', encoding='latin-1', skiprows=2)
    df.columns = ['Prov', 'Comune', 'Irr_1kW']
    
    # Pulizia: rimuove righe senza comune e converte i numeri (es. 1.606,70 -> 1606.70)
    df = df.dropna(subset=['Comune', 'Irr_1kW'])
    df['Irr_1kW'] = df['Irr_1kW'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    return df

def get_color(loss_pct):
    """Restituisce lo stile CSS basato sulla percentuale di perdita rispetto al target"""
    if loss_pct < 5:
        return 'background-color: green; color: white'
    elif 5 <= loss_pct < 10:
        return 'background-color: yellow; color: black'
    elif 10 <= loss_pct < 15:
        return 'background-color: orange; color: black'
    elif 15 <= loss_pct < 20:
        return 'background-color: red; color: white'
    elif 20 <= loss_pct < 25:
        return 'background-color: purple; color: white'
    else:
        return 'background-color: black; color: white'

# --- INTERFACCIA LATERALE ---
st.sidebar.header("Configurazione")
try:
    df_irr = load_irraggiamento()
    comune_scelto = st.sidebar.selectbox("Seleziona il Comune dell'impianto", options=sorted(df_irr['Comune'].unique()))
    
    # Valore di irraggiamento (kWh prodotti attesi per 1 kWp)
    irr_specifico = df_irr[df_irr['Comune'] == comune_scelto]['Irr_1kW'].values[0]
    st.sidebar.info(f"Resa teorica comune: {irr_specifico:.2f} kWh/kWp")
except Exception as e:
    st.sidebar.error(f"Errore caricamento irraggiamento.csv: {e}")

# --- CARICAMENTO DATI PRODUZIONE ---
st.title("Analisi Efficienza Impianto Fotovoltaico")
uploaded_file = st.file_uploader("Carica il file Excel/CSV degli incentivi GSE", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Lettura file produzione
        if uploaded_file.name.endswith('.csv'):
            df_prod = pd.read_csv(uploaded_file)
        else:
            df_prod = pd.read_excel(uploaded_file)
        
        # Estrazione potenza (si assume costante nel file)
        potenza_impianto = float(df_prod['POTENZA IMPIANTO'].iloc[0])
        
        # Calcolo Target Annuale Teorico
        target_annuo_impianto = irr_specifico * potenza_impianto
        
        # Aggregazione produzione per anno
        # Rimuoviamo eventuali valori non numerici o negativi se presenti
        df_prod['ENERGIA'] = pd.to_numeric(df_prod['ENERGIA'], errors='coerce').fillna(0)
        report = df_prod.groupby('ANNO RIFERIMENTO')['ENERGIA'].sum().reset_index()
        report.columns = ['Anno', 'Energia Reale (kWh)']
        
        # Calcolo scostamenti
        report['Target Atteso (kWh)'] = target_annuo_impianto
        report['Produzione %'] = (report['Energia Reale (kWh)'] / target_annuo_impianto) * 100
        report['Perdita %'] = 100 - report['Produzione %']
        
        st.subheader(f"Risultati per Impianto da {potenza_impianto} kWp a {comune_scelto}")
        
        # Applicazione formattazione condizionale
        def apply_style(row):
            color = get_color(row['Perdita %'])
            return [color] * len(row)

        styled_df = report.style.apply(apply_style, axis=1).format({
            'Energia Reale (kWh)': '{:.2f}',
            'Target Atteso (kWh)': '{:.2f}',
            'Produzione %': '{:.2f}%',
            'Perdita %': '{:.2f}%'
        })
        
        st.table(styled_df)
        
        # Riepilogo metriche
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Potenza Impianto", f"{potenza_impianto} kWp")
        with col2:
            st.metric("Target Annuo Stimato", f"{target_annuo_impianto:.2f} kWh")

    except Exception as e:
        st.error(f"Errore durante l'elaborazione del file: {e}")
else:
    st.warning("Carica un file per visualizzare l'analisi.")
