from __future__ import annotations
import os

# Senha simples para Admin (troque aqui)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Nome do arquivo em uso (padrão: current.csv; se não existir, usa sample.csv)
DATA_CURRENT_CSV = os.getenv("DATA_CURRENT_CSV", "data/current.csv")
DATA_SAMPLE_CSV = os.getenv("DATA_SAMPLE_CSV", "data/sample.csv")

# Banco local (configs/metas)
DB_PATH = os.getenv("DB_PATH", "data/app.db")

# Dias úteis padrão (0=seg ... 6=dom)
DEFAULT_WORKING_DAYS = [0,1,2,3,4]  # seg-sex
