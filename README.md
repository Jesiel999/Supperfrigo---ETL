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
│       └── silver/financeiro_bi.sql
├── bronze/extract/sances/financeiro.py
├── silver/transform/financeiro/financeiro.py
├── gold/
│   ├── marts/sances.inadimplencia.py
│   ├── views/vw_bi_inadimplencia.sql
│   └── indicators/kpi_inadimplencia.py
├── pipelines/financeiro_pipeline.py
├── repositories/financeiro_repository.py
├── services/inadimplencia_service.py
├── api/routers/
│   ├── pipeline_router.py
│   ├── financeiro_router.py
│   └── dashboard_router.py
└── monitoring/pipeline_status.py
```

---

## Tecnologias

| Categoria | Biblioteca | Finalidade |
|------------|------------|------------|
| API | FastAPI | Framework para construção da API REST |
| Servidor | Uvicorn | Servidor ASGI para execução da aplicação |
| Validação | Pydantic | Validação de dados e modelos |
| Banco de Dados | mysql-connector-python | Conexão com MySQL |
| Banco de Dados | mysqlclient | Driver MySQL de alta performance |
| ETL | Pandas | Transformação e manipulação de dados |
| ETL | NumPy | Operações numéricas |
| Excel | OpenPyXL | Importação e exportação de planilhas |
| Agendamento | APScheduler | Execução automática dos pipelines |
| HTTP | Requests | Consumo das APIs externas |
| Autenticação | python-jose | Geração e validação de tokens JWT |
| Segurança | Passlib + BCrypt | Hash de senhas |
| Upload | python-multipart | Upload de arquivos |
| Configuração | python-dotenv | Variáveis de ambiente |
| Logs | concurrent-log-handler | Rotação segura de logs |
| Data/Hora | python-dateutil | Manipulação de datas |
| Fuso Horário | tzlocal | Identificação do fuso local |
| YAML | PyYAML | Leitura de arquivos YAML |

---

## Setup

```bash
cp .env.example .env

# Edite o arquivo .env com as credenciais do ambiente

pip install -r requirements.txt
```

### Criar tabelas no MySQL

```bash
python -m database.create_schema
```

### Rodar a API

```bash
uvicorn app:app --reload --port 8000
```

---

## Endpoints

| Método | Endpoint | Descrição |
|---------|----------|-----------|
| POST | `/auth/login` | Autenticação e geração do JWT |
| POST | `/pipeline/executar` | Executa o pipeline em background |
| POST | `/pipeline/executar/sync` | Executa o pipeline de forma síncrona |
| GET | `/pipeline/status` | Status da última execução |
| GET | `/financeiro/inadimplencia` | Consulta financeira |
| GET | `/dashboard/kpi/inadimplencia` | Indicadores do Dashboard |

### Filtros disponíveis

#### `/financeiro/inadimplencia`

| Parâmetro | Tipo | Descrição |
|------------|------|-----------|
| id_empresa | string | Empresa |
| id_pessoa | string | Cliente |
| status | string | VENCIDO \| EM ABERTO |
| dias_atraso_min | int | Dias mínimos em atraso |
| limit | int | Quantidade de registros |
| offset | int | Paginação |

#### `/pipeline/executar`

```json
{
    "data_baixa_inicial": "2024-01-01",
    "data_baixa_final": "2024-12-31"
}
```

---

## Arquitetura ETL

### Pipeline Sances

```
API Sances
      │
      ▼
BRONZE
financeiro_raw
      │
      │ Extração dos dados
      ▼
SILVER
financeiro_bi
      │
      │ Transformação
      │ Normalização
      │ Regras de negócio
      ▼
GOLD
inadimplencia_gold
vw_bi_inadimplencia
      │
      ▼
FastAPI
      │
      ▼
Angular Dashboard
```

### Pipeline Sults

```
API Sults
      │
      ▼
BRONZE
chamados_raw
      │
      ▼
SILVER
chamados_bi
      │
      ▼
GOLD
chamados_geral_gold
vw_bi_geral
      │
      ▼
FastAPI
      │
      ▼
Angular Dashboard
```

---

## Regras de Negócio

### Status Financeiro (Camada Silver)

| Condição | Resultado |
|-----------|-----------|
| `data_baixa` preenchida | PAGO |
| Situação contém CANCELADO | CANCELADO |
| Data de vencimento menor que hoje e sem baixa | VENCIDO |
| Demais situações | EM ABERTO |

---

## Arquitetura

O projeto segue a arquitetura de Data Lake em três camadas:

- **Bronze:** Armazena os dados brutos extraídos das APIs.
- **Silver:** Realiza limpeza, padronização e aplicação das regras de negócio.
- **Gold:** Disponibiliza dados consolidados para consultas analíticas e dashboards.

Essa separação facilita a rastreabilidade dos dados, reduz o acoplamento entre extração e análise e melhora a manutenção da solução.