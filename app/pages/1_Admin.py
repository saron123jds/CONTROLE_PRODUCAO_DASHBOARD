from __future__ import annotations
import streamlit as st
from lib.settings import ADMIN_PASSWORD, DB_PATH, DEFAULT_WORKING_DAYS
from lib.db import connect, init_db, get_config, set_config, upsert_meta_semanal, delete_meta_semanal, list_metas

st.set_page_config(page_title="Admin — Metas", page_icon="⚙️", layout="wide")

conn = connect(DB_PATH)
init_db(conn)

st.title("⚙️ Admin — Configuração de Metas")
st.caption("Aqui você configura metas semanais e regras de cálculo. (Senha simples)")

pwd = st.text_input("Senha do Admin", type="password")
if pwd != ADMIN_PASSWORD:
    st.warning("Digite a senha correta para liberar as configurações.")
    st.stop()

st.success("Admin liberado ✅")

st.markdown("## Metas gerais")
meta_geral = int(get_config(conn, "meta_semanal_geral", "0") or "0")
novo = st.number_input("Meta semanal geral (peças)", min_value=0, value=meta_geral, step=10)
if st.button("Salvar meta geral"):
    set_config(conn, "meta_semanal_geral", str(int(novo)))
    st.success("Meta geral salva!")

st.markdown("## Metas por coleção (opcional)")
col1, col2, col3 = st.columns([2,1,1])
with col1:
    colecao = st.text_input("Nome da coleção (exatamente como no arquivo)", placeholder="Ex.: INVERNO 2026 - DAZUL")
with col2:
    meta = st.number_input("Meta semanal (peças)", min_value=0, value=0, step=10)
with col3:
    if st.button("Adicionar/Atualizar"):
        if colecao.strip():
            set_config(conn, f"meta_semanal::{colecao.strip()}", str(int(meta)))
            st.success("Meta da coleção salva!")
        else:
            st.error("Informe o nome da coleção.")

metas = []
# listar configs do tipo meta_semanal::
# como está em config, não em tabela, listamos via SQL direto
cur = conn.cursor()
rows = cur.execute("SELECT k, v, updated_at FROM config WHERE k LIKE 'meta_semanal::%' ORDER BY k").fetchall()
for r in rows:
    metas.append({"colecao": r["k"].split("::",1)[1], "meta": int(r["v"]), "updated_at": r["updated_at"]})

st.markdown("### Metas cadastradas")
if metas:
    st.dataframe(metas, use_container_width=True)
    del_col = st.text_input("Excluir meta de qual coleção?", placeholder="Coleção para excluir")
    if st.button("Excluir"):
        if del_col.strip():
            set_config(conn, f"meta_semanal::{del_col.strip()}", "0")
            st.success("Excluída (zerada).")
else:
    st.info("Nenhuma meta por coleção cadastrada ainda.")

st.markdown("## Regras de dias úteis (para meta diária automática — em breve)")
st.caption("Nesta versão, o dashboard mostra Meta x Realizado semanal. A meta diária pode ser adicionada na próxima versão com calendário e feriados.")
