from __future__ import annotations
import streamlit as st
import plotly.express as px
import pandas as pd
from pathlib import Path
from lib.settings import DATA_CURRENT_CSV, DATA_SAMPLE_CSV
from lib.data import load_dataset

st.set_page_config(page_title="Detalhes", page_icon="🔎", layout="wide")

@st.cache_data(show_spinner=False)
def _load(path: str) -> pd.DataFrame:
    return load_dataset(path)

def get_data_path() -> str:
    p = Path(DATA_CURRENT_CSV)
    if p.exists():
        return str(p)
    return DATA_SAMPLE_CSV

st.title("🔎 Detalhes e Análises")

df = _load(get_data_path())

st.markdown("### Distribuição de lead time (dias)")
if "LEAD_DIAS" in df.columns and df["LEAD_DIAS"].notna().any():
    f = df["LEAD_DIAS"].dropna()
    fig = px.histogram(f, nbins=50)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sem coluna LEAD_DIAS (ou datas insuficientes).")

st.markdown("### Lead time médio por processo")
if "LEAD_DIAS" in df.columns and "NOME_PROCESSO" in df.columns:
    g = df.dropna(subset=["LEAD_DIAS"]).groupby("NOME_PROCESSO", as_index=False)["LEAD_DIAS"].mean().sort_values("LEAD_DIAS", ascending=False).head(25)
    fig = px.bar(g, x="LEAD_DIAS", y="NOME_PROCESSO", orientation="h")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sem colunas para lead time por processo.")

st.markdown("### Dados brutos (amostra)")
st.dataframe(df.sample(min(2000, len(df))), use_container_width=True)
