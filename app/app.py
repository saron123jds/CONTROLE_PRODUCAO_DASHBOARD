from __future__ import annotations
import streamlit as st
import plotly.express as px
import pandas as pd
from pathlib import Path

from lib.settings import ADMIN_PASSWORD, DATA_CURRENT_CSV, DATA_SAMPLE_CSV, DB_PATH, DEFAULT_WORKING_DAYS
from lib.db import connect, init_db, get_config, set_config
from lib.data import load_dataset, save_uploaded_to_current
from lib.kpis import (
    kpi_cards,
    prod_por_dia,
    prod_por_semana,
    top_processos,
    top_responsaveis,
    atrasos_por_colecao,
    top_referencias,
)

st.set_page_config(page_title="Controle de Produção", page_icon="📊", layout="wide")

@st.cache_data(show_spinner=False)
def _load(path: str) -> pd.DataFrame:
    return load_dataset(path)

def get_data_path() -> str:
    p = Path(DATA_CURRENT_CSV)
    if p.exists():
        return str(p)
    return DATA_SAMPLE_CSV

def sidebar_import():
    st.sidebar.markdown("### 📥 Importar planilha")
    up = st.sidebar.file_uploader("Envie CSV ou Excel", type=["csv","xlsx","xls"])
    if up is not None:
        out = save_uploaded_to_current(up.getvalue(), up.name, DATA_CURRENT_CSV)
        st.cache_data.clear()
        st.sidebar.success(f"Arquivo importado: {out}")

def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown("### 🎛️ Filtros")

    if "NOME_COLECAO" in df.columns:
        colecoes = sorted([c for c in df["NOME_COLECAO"].dropna().unique().tolist()])
        sel_col = st.sidebar.multiselect("Coleção", colecoes, default=colecoes[:1] if len(colecoes) else [])
        if sel_col:
            df = df[df["NOME_COLECAO"].isin(sel_col)]

    if "NOME_PROCESSO" in df.columns:
        processos = sorted([p for p in df["NOME_PROCESSO"].dropna().unique().tolist()])
        sel_proc = st.sidebar.multiselect("Processo", processos, default=processos[:1] if len(processos) else [])
        if sel_proc:
            df = df[df["NOME_PROCESSO"].isin(sel_proc)]

    if "STATUS_PRODUCAO" in df.columns:
        status = sorted([s for s in df["STATUS_PRODUCAO"].dropna().unique().tolist()])
        sel_status = st.sidebar.multiselect("Status Produção", status, default=status)
        if sel_status:
            df = df[df["STATUS_PRODUCAO"].isin(sel_status)]

    if "REFERENCIA_BASE" in df.columns:
        referencias = sorted([r for r in df["REFERENCIA_BASE"].dropna().unique().tolist()])
        sel_refs = st.sidebar.multiselect("Referência (base)", referencias)
        if sel_refs:
            df = df[df["REFERENCIA_BASE"].isin(sel_refs)]

    if "DATA_BASE" in df.columns and df["DATA_BASE"].notna().any():
        dmin = df["DATA_BASE"].min()
        dmax = df["DATA_BASE"].max()
        d1, d2 = st.sidebar.date_input("Período", value=(dmin.date(), dmax.date()))
        df = df[(df["DATA_BASE"].dt.date >= d1) & (df["DATA_BASE"].dt.date <= d2)]

    return df

def goals_block(conn, df_filtered: pd.DataFrame):
    st.markdown("### 🎯 Meta x Realizado (Semana)")
    # meta por coleção (se filtro de coleção selecionado)
    colecao = None
    if "NOME_COLECAO" in df_filtered.columns:
        u = df_filtered["NOME_COLECAO"].dropna().unique().tolist()
        if len(u) == 1:
            colecao = u[0]

    meta_geral = int(get_config(conn, "meta_semanal_geral", "0") or "0")
    meta_colecao = None
    if colecao:
        meta_colecao = int(get_config(conn, f"meta_semanal::{colecao}", str(meta_geral)) or str(meta_geral))

    meta = meta_colecao if (meta_colecao is not None) else meta_geral

    sem = prod_por_semana(df_filtered)
    if sem.empty:
        st.info("Sem dados de semana para calcular Meta x Realizado.")
        return

    sem_atual = sem.iloc[-1]["ANO_SEMANA"]
    realizado = int(sem.iloc[-1]["QTDE_PRODUCAO"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Semana (ISO)", str(sem_atual))
    col2.metric("Realizado (peças)", f"{realizado:,}".replace(",", "."))
    col3.metric("Meta semanal (peças)", f"{meta:,}".replace(",", "."))

    if meta > 0:
        pct = min(1.0, realizado / meta)
        st.progress(pct)
        st.caption(f"{pct*100:.1f}% da meta semanal")

def referencias_agrupadas(df: pd.DataFrame) -> pd.DataFrame:
    if "REFERENCIA_BASE" not in df.columns or "QTDE_PRODUCAO" not in df.columns:
        return pd.DataFrame(columns=["REFERENCIA_BASE","TOTAL_PECAS"])

    tmp = df.copy()
    for col in ["NOME_PROCESSO", "NOME_COLECAO", "REFERENCIA_PRODUTO"]:
        if col not in tmp.columns:
            tmp[col] = pd.NA

    def _join_refs(vals: pd.Series) -> str:
        uniq = sorted({v for v in vals.dropna().astype(str).tolist()})
        if not uniq:
            return "—"
        preview = uniq[:5]
        suffix = "..." if len(uniq) > 5 else ""
        return ", ".join(preview) + suffix

    agg = (
        tmp.dropna(subset=["REFERENCIA_BASE"])
        .groupby("REFERENCIA_BASE", as_index=False)
        .agg(
            TOTAL_PECAS=("QTDE_PRODUCAO", "sum"),
            QTD_PROCESSOS=("NOME_PROCESSO", "nunique"),
            QTD_COLECOES=("NOME_COLECAO", "nunique"),
            REFERENCIAS=("REFERENCIA_PRODUTO", _join_refs),
        )
        .sort_values("TOTAL_PECAS", ascending=False)
    )
    return agg

def main():
    # DB init
    conn = connect(DB_PATH)
    init_db(conn)

    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; }
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e6e6e6;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        section[data-testid="stSidebar"] > div { padding-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("📊 Controle de Produção")
    sidebar_import()

    data_path = get_data_path()
    df = _load(data_path)

    st.title("Controle de Produção")
    st.caption(f"Arquivo em uso: `{data_path}` | Linhas: {len(df):,}".replace(",", "."))

    df_f = sidebar_filters(df)

    with st.expander("Resumo dos filtros aplicados", expanded=False):
        st.write(f"Linhas após filtros: {len(df_f):,}".replace(",", "."))
        if "NOME_COLECAO" in df_f.columns:
            st.write(f"Coleções: {df_f['NOME_COLECAO'].nunique():,}".replace(",", "."))
        if "REFERENCIA_BASE" in df_f.columns:
            st.write(f"Referências base: {df_f['REFERENCIA_BASE'].nunique():,}".replace(",", "."))

    tab_geral, tab_proc, tab_resp, tab_ref, tab_dados = st.tabs(
        ["Visão geral", "Processos", "Responsáveis", "Referências", "Dados"]
    )

    with tab_geral:
        cards = kpi_cards(df_f)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total (peças)", f"{cards['total']:,}".replace(",", "."))
        if cards["concl"] is not None:
            c2.metric("Concluído (peças)", f"{cards['concl']:,}".replace(",", "."))
        else:
            c2.metric("Concluído", "—")
        if cards["atraso"] is not None:
            c3.metric("Em atraso (peças)", f"{cards['atraso']:,}".replace(",", "."))
        else:
            c3.metric("Em atraso", "—")
        c4.metric("Lead time médio (dias)", f"{cards['lead_medio']:.1f}" if cards["lead_medio"] is not None else "—")
        c5.metric("Dias conclusão médio", f"{cards['dias_conc_medio']:.1f}" if cards["dias_conc_medio"] is not None else "—")

        goals_block(conn, df_f)

        st.markdown("### 📈 Produção por dia")
        d = prod_por_dia(df_f)
        if not d.empty:
            fig = px.line(d, x="DATA", y="QTDE_PRODUCAO", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não foi possível gerar produção por dia (faltam DATA_BASE/QTDE_PRODUCAO).")

        st.markdown("### ⏰ Atrasos por coleção")
        ac = atrasos_por_colecao(df_f)
        if not ac.empty:
            fig = px.bar(ac.head(20), x="QTDE_ATRASO", y="NOME_COLECAO", orientation="h")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de atraso por coleção (ou não existe STATUS_VENCIMENTO).")

    with tab_proc:
        st.markdown("### 🧩 Top processos (por volume)")
        tp = top_processos(df_f, n=12)
        if not tp.empty:
            fig = px.bar(tp, x="QTDE_PRODUCAO", y="NOME_PROCESSO", orientation="h")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de processo.")

    with tab_resp:
        st.markdown("### 👥 Top responsáveis (por volume)")
        tr = top_responsaveis(df_f, n=12)
        if not tr.empty:
            fig = px.bar(tr, x="QTDE_PRODUCAO", y="RESPONSAVEL", orientation="h")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de responsável.")

    with tab_ref:
        st.markdown("### 🔖 Referências agrupadas")
        trf = top_referencias(df_f, n=15)
        if not trf.empty:
            fig = px.bar(trf, x="QTDE_PRODUCAO", y="REFERENCIA_BASE", orientation="h")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de referência para agrupar.")

        st.markdown("### 🧾 Detalhe por referência base")
        ref_table = referencias_agrupadas(df_f)
        if not ref_table.empty:
            st.dataframe(ref_table.head(2000), use_container_width=True)
        else:
            st.info("Sem dados de referência para detalhar.")

    with tab_dados:
        st.markdown("### 🧾 Tabela filtrada")
        st.dataframe(df_f.head(2000), use_container_width=True)

if __name__ == "__main__":
    main()
