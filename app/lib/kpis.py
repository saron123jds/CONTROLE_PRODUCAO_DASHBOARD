from __future__ import annotations
import pandas as pd
import numpy as np

def kpi_cards(df: pd.DataFrame) -> dict:
    total = int(df["QTDE_PRODUCAO"].sum()) if "QTDE_PRODUCAO" in df.columns else len(df)
    concl = int(df.query("STATUS_PRODUCAO == 'CONCLUIDO'")["QTDE_PRODUCAO"].sum()) if "STATUS_PRODUCAO" in df.columns and "QTDE_PRODUCAO" in df.columns else None
    atraso = int(df.query("STATUS_VENCIMENTO == 'EM ATRASO'")["QTDE_PRODUCAO"].sum()) if "STATUS_VENCIMENTO" in df.columns and "QTDE_PRODUCAO" in df.columns else None

    lead_medio = float(df["LEAD_DIAS"].dropna().mean()) if "LEAD_DIAS" in df.columns else None
    dias_conc_medio = float(df["DIAS_CONCLUSAO"].dropna().mean()) if "DIAS_CONCLUSAO" in df.columns else None

    return {
        "total": total,
        "concl": concl,
        "atraso": atraso,
        "lead_medio": lead_medio,
        "dias_conc_medio": dias_conc_medio,
    }

def prod_por_dia(df: pd.DataFrame) -> pd.DataFrame:
    if "DATA_BASE" not in df.columns or "QTDE_PRODUCAO" not in df.columns:
        return pd.DataFrame(columns=["DATA_BASE","QTDE_PRODUCAO"])
    g = df.dropna(subset=["DATA_BASE"]).groupby(df["DATA_BASE"].dt.date, as_index=False)["QTDE_PRODUCAO"].sum()
    g.rename(columns={"DATA_BASE":"DATA"}, inplace=True)
    g["DATA"] = pd.to_datetime(g["DATA"])
    return g.sort_values("DATA")

def prod_por_semana(df: pd.DataFrame) -> pd.DataFrame:
    if "ANO_SEMANA" not in df.columns or "QTDE_PRODUCAO" not in df.columns:
        return pd.DataFrame(columns=["ANO_SEMANA","QTDE_PRODUCAO"])
    g = df.dropna(subset=["ANO_SEMANA"]).groupby("ANO_SEMANA", as_index=False)["QTDE_PRODUCAO"].sum()
    return g.sort_values("ANO_SEMANA")

def top_processos(df: pd.DataFrame, n: int=10) -> pd.DataFrame:
    if "NOME_PROCESSO" not in df.columns or "QTDE_PRODUCAO" not in df.columns:
        return pd.DataFrame(columns=["NOME_PROCESSO","QTDE_PRODUCAO"])
    g = df.groupby("NOME_PROCESSO", as_index=False)["QTDE_PRODUCAO"].sum().sort_values("QTDE_PRODUCAO", ascending=False).head(n)
    return g

def top_responsaveis(df: pd.DataFrame, n: int=10) -> pd.DataFrame:
    if "RESPONSAVEL" not in df.columns or "QTDE_PRODUCAO" not in df.columns:
        return pd.DataFrame(columns=["RESPONSAVEL","QTDE_PRODUCAO"])
    g = df.groupby("RESPONSAVEL", as_index=False)["QTDE_PRODUCAO"].sum().sort_values("QTDE_PRODUCAO", ascending=False).head(n)
    return g

def atrasos_por_colecao(df: pd.DataFrame) -> pd.DataFrame:
    if "STATUS_VENCIMENTO" not in df.columns or "QTDE_PRODUCAO" not in df.columns or "NOME_COLECAO" not in df.columns:
        return pd.DataFrame(columns=["NOME_COLECAO","QTDE_ATRASO"])
    g = df.query("STATUS_VENCIMENTO == 'EM ATRASO'").groupby("NOME_COLECAO", as_index=False)["QTDE_PRODUCAO"].sum()
    g.rename(columns={"QTDE_PRODUCAO":"QTDE_ATRASO"}, inplace=True)
    return g.sort_values("QTDE_ATRASO", ascending=False)
