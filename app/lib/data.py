from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional

DATE_COLS = ["EMISSAO_PRODUCAO","VENCIMENTO_PRODUCAO","CONCLUSAO_PRODUCAO"]

def _parse_date(s: pd.Series) -> pd.Series:
    # dados estão em dd/mm/yyyy
    return pd.to_datetime(s, errors="coerce", dayfirst=True)

def _normalize_reference(s: pd.Series) -> pd.Series:
    raw = s.astype(str).str.strip()
    raw = raw.replace({"nan": np.nan, "None": np.nan, "": np.nan})
    raw = raw.str.replace(r"\s+", "", regex=True)
    base = raw.str.split(".").str[0]
    base = base.replace({"nan": np.nan, "None": np.nan, "": np.nan})
    return base

def load_dataset(path_csv: str) -> pd.DataFrame:
    p = Path(path_csv)
    if not p.exists():
        raise FileNotFoundError(str(p))

    # tenta utf-8, se falhar usa latin1
    try:
        df = pd.read_csv(p, encoding="utf-8", sep=None, engine="python")
    except Exception:
        df = pd.read_csv(p, encoding="latin1", sep=None, engine="python")

    # limpa colunas unnamed
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed", case=False, na=False)]

    # normaliza tipos
    if "QTDE_PRODUCAO" in df.columns:
        df["QTDE_PRODUCAO"] = pd.to_numeric(df["QTDE_PRODUCAO"], errors="coerce").fillna(0).astype(int)

    if "DIAS_CONCLUSAO" in df.columns:
        df["DIAS_CONCLUSAO"] = pd.to_numeric(df["DIAS_CONCLUSAO"], errors="coerce")

    for c in DATE_COLS:
        if c in df.columns:
            df[c] = _parse_date(df[c])

    # cria colunas auxiliares
    if "CONCLUSAO_PRODUCAO" in df.columns and df["CONCLUSAO_PRODUCAO"].notna().any():
        df["DATA_BASE"] = df["CONCLUSAO_PRODUCAO"]
    elif "EMISSAO_PRODUCAO" in df.columns and df["EMISSAO_PRODUCAO"].notna().any():
        df["DATA_BASE"] = df["EMISSAO_PRODUCAO"]
    else:
        df["DATA_BASE"] = pd.NaT

    if "REFERENCIA_PRODUTO" in df.columns:
        df["REFERENCIA_BASE"] = _normalize_reference(df["REFERENCIA_PRODUTO"])

    df["ANO"] = df["DATA_BASE"].dt.year
    df["MES"] = df["DATA_BASE"].dt.to_period("M").astype(str)
    df["SEMANA_ISO"] = df["DATA_BASE"].dt.isocalendar().week.astype("Int64")
    df["ANO_SEMANA"] = df["DATA_BASE"].dt.isocalendar().year.astype("Int64").astype(str) + "-W" + df["SEMANA_ISO"].astype(str)

    # lead time (dias) entre emissão e conclusão
    if "EMISSAO_PRODUCAO" in df.columns and "CONCLUSAO_PRODUCAO" in df.columns:
        df["LEAD_DIAS"] = (df["CONCLUSAO_PRODUCAO"] - df["EMISSAO_PRODUCAO"]).dt.days

    return df

def save_uploaded_to_current(uploaded_bytes: bytes, filename: str, out_path_csv: str) -> str:
    out = Path(out_path_csv)
    out.parent.mkdir(parents=True, exist_ok=True)

    # se for excel, converte pra csv
    lower = filename.lower()
    if lower.endswith(".xlsx") or lower.endswith(".xls"):
        import io
        bio = io.BytesIO(uploaded_bytes)
        xdf = pd.read_excel(bio)
        xdf.to_csv(out, index=False, encoding="utf-8")
        return str(out)

    # senão salva como csv e pronto
    out.write_bytes(uploaded_bytes)
    return str(out)
