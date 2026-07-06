# ETL — Sances Turbo → MySQL → FastAPI

Pipeline ETL em Python com FastAPI seguindo a arquitetura **Bronze → Silver → Gold**.

---

## Estrutura

```
ETL/
├── app.py                          ← Entry point FastAPI
├── auth/router.py                  ← JWT
├── config/                         ← Settings, logging, ambiente
├── database/
│   ├── mysql_connection.py
│   └── schemas/
│       ├── bronze/financeiro_raw.sql
│       ├── silver/financeiro_bi.sql
│       └── gold/inadimplencia_gold.sql
├── bronze/extract/sances/financeiro.py   ← APENAS extração da API
├── silver/transform/financeiro/financeiro.py ← Transformação + cálculo status
├── gold/
│   ├── marts/sances.inadimplencia.py      ← Carga na gold
│   ├── views/vw_bi_inadimplencia.sql
│   └── indicators/kpi_inadimplencia.py
├── pipelines/financeiro_pipeline.py ← Orquestra Bronze→Silver→Gold
├── repositories/financeiro_repository.py
├── services/inadimplencia_service.py
├── api/routers/
│   ├── pipeline_router.py
│   ├── financeiro_router.py
│   └── dashboard_router.py
└── monitoring/pipeline_status.py
```

---

## Setup

```bash
cp .env.example .env
# edite .env com suas credenciais

pip install -r requirements.txt
```

### Criar tabelas no MySQL

python -m database.create_schema

### Rodar a API

```bash
uvicorn app:app --reload --port 8000
```

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/login` | Login — retorna JWT |
| POST | `/pipeline/executar` | Dispara pipeline em background |
| POST | `/pipeline/executar/sync` | Executa pipeline síncrono |
| GET  | `/pipeline/status` | Resultado da última execução |
| GET  | `/financeiro/inadimplencia` | Lista inadimplência com filtros |
| GET  | `/dashboard/kpi/inadimplencia` | KPIs para o dashboard Angular |

### Filtros disponíveis em `/financeiro/inadimplencia`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `id_empresa` | string | Filtrar por empresa |
| `id_pessoa` | string | Filtrar por pessoa |
| `status` | string | `VENCIDO` \| `EM ABERTO` |
| `dias_atraso_min` | int | Mínimo de dias em atraso |
| `limit` / `offset` | int | Paginação |

### Filtros no pipeline `/pipeline/executar`

```json
{
  "data_baixa_inicial": "2024-01-01",
  "data_baixa_final":   "2024-12-31"
}
```

---

## Fluxo de dados SANCES

```
API Sances
   │
   ▼
BRONZE — financeiro_raw
   │   (extração pura, sem transformação)
   ▼
SILVER — financeiro_bi
   │   (status_financeiro, dias_atraso calculados)
   ▼
GOLD — inadimplencia_gold + vw_bi_inadimplencia
   │
   ▼
FastAPI → Angular Dashboard
```

## Fluxo de dados SULTS

```
API Sults
   │
   ▼
BRONZE — chamados_raw
   │   (extração pura, sem transformação)
   ▼
SILVER — chamados_bi
   │   (status_financeiro, dias_atraso calculados)
   ▼
GOLD — chamados_geral_gold + vw_bi_geral
   │
   ▼
FastAPI → Angular Dashboard
```

---

## Status financeiro calculado (Silver)

| Condição | Status |
|----------|--------|
| `data_baixa` preenchida | `PAGO` |
| Situação contém "CANCELADO" | `CANCELADO` |
| `data_vencimento` < hoje e sem baixa | `VENCIDO` |
| Demais casos | `EM ABERTO` |
