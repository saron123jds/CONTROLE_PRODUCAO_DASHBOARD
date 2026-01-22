# Controle de Produção — Dashboard estilo Power BI (Localhost)

Este projeto lê uma planilha (CSV/Excel) e gera um dashboard com:
- Produção (peças) por dia / semana / mês
- Meta x Realizado (metas configuráveis no Admin)
- Lead time (dias) e tempos médios (via DIAS_CONCLUSAO e/ou datas)
- Atrasos (STATUS_VENCIMENTO / vencimento)
- Ranking por processo e por responsável
- Filtros por Coleção, Processo, Status e Período

## Como rodar (Windows)
1) Abra o PowerShell na pasta do projeto
2) Crie um venv e instale dependências:
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3) Rode o app em localhost (porta 8000 por padrão):
```bash
streamlit run app/app.py --server.port 8000
```

## Como trocar o arquivo
No menu lateral do app existe a seção **Importar planilha**.
- Envie CSV ou Excel.
- O sistema salva como `data/current.csv` e atualiza os painéis.

## Admin (metas)
No menu **Admin** você configura:
- Meta semanal (por coleção e geral)
- Dias úteis da semana (para cálculo da meta diária automática)
- Override de meta diária (se quiser “forçar” um valor)

> Senha padrão do Admin: `admin` (você pode mudar em `app/lib/settings.py`).

## Observações sobre os dados
O sistema detecta e usa as colunas do seu arquivo, incluindo (se existirem):
- EMISSAO_PRODUCAO, VENCIMENTO_PRODUCAO, CONCLUSAO_PRODUCAO
- QTDE_PRODUCAO
- NOME_COLECAO, NOME_PROCESSO, RESPONSAVEL
- DIAS_CONCLUSAO, STATUS_PRODUCAO, STATUS_VENCIMENTO
