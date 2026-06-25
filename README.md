# Guardian AI: Sistema de Auditoria de Compliance Baseado em Agentes e RAG

## Descricao Breve

O Guardian AI automatiza a analise de Compliance e PLD/CFT em operacoes de cambio. O sistema cruza politicas internas recuperadas por RAG com dados estruturados de clientes e transacoes, permitindo que um agente de IA identifique indicios de risco, inconformidades e justificativas com base documental.

O projeto combina:

- dados sinteticos de clientes, transacoes e logs de compliance;
- politica interna de compliance indexada em ChromaDB;
- embeddings locais com `sentence-transformers`;
- agente LangChain com Function Calling;
- Gemini como LLM;
- API Web com FastAPI para expor a auditoria a futuras interfaces.

## Arquitetura do Projeto

Pipeline principal:

1. Geracao de dados

   O script `src/generator.py` cria arquivos CSV sinteticos em `data/`:

   - `customers.csv`;
   - `transactions.csv`;
   - `compliance_logs.csv`.

2. Criacao de vetores e ChromaDB

   O script `src/baseline.py` le `data/politica_compliance_guardian.txt`, divide o texto em chunks, gera embeddings locais com `sentence-transformers/all-MiniLM-L6-v2` e persiste o indice vetorial em `chromadb_cache/`.

3. Orquestracao de agente com LangChain e Gemini

   O script `src/agent.py` implementa um agente com `create_tool_calling_agent` e `AgentExecutor`. A LLM usa Function Calling para decidir quando consultar:

   - `consultar_dados_cadastrais(customer_id)`;
   - `consultar_historico_transacoes(customer_id)`;
   - `consultar_politica_compliance(query)`.

   O modelo padrao do agente e `gemini-1.5-flash`, com suporte a override via `.env`:

   ```text
   GUARDIAN_AGENT_LLM_MODEL=gemini-2.5-flash
   ```

   Para a arquitetura alvo, recomenda-se usar `gemini-2.5-flash` quando disponivel para a chave configurada.

4. API com FastAPI

   O arquivo `src/main.py` expoe o agente por HTTP:

   - `GET /`: healthcheck da API;
   - `POST /api/audit`: recebe uma pergunta de auditoria e retorna a analise final do agente.

## Estrutura do Projeto

```text
.
├── data/
│   ├── compliance_logs.csv
│   ├── customers.csv
│   ├── politica_compliance_guardian.txt
│   └── transactions.csv
├── src/
│   ├── agent.py
│   ├── baseline.py
│   ├── generator.py
│   ├── init.py
│   └── main.py
├── chromadb_cache/
├── .env
├── requirements.txt
└── README.md
```

## Pre-requisitos e Instalacao

Requisitos principais:

- Python 3.11+;
- chave da Gemini API;
- ambiente virtual Python recomendado.

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto:

```text
GOOGLE_API_KEY=sua_chave_aqui
```

Opcionalmente, configure o modelo do agente:

```text
GUARDIAN_AGENT_LLM_MODEL=gemini-2.5-flash
```

## Como Executar

### 1. Gerar dados sinteticos

```bash
python src/generator.py
```

Esse comando gera:

```text
data/customers.csv
data/transactions.csv
data/compliance_logs.csv
```

### 2. Criar o indice vetorial do Baseline RAG

```bash
python src/baseline.py
```

Esse comando:

- carrega a politica interna;
- divide o documento em chunks;
- gera embeddings locais;
- cria ou reutiliza o indice ChromaDB em `chromadb_cache/`;
- executa uma pergunta de demonstracao contra a politica.

### 3. Executar o agente em modo script

```bash
python src/agent.py
```

O script executa uma pergunta de auditoria para o cliente `CLI-38726`, cruzando:

- cadastro do cliente;
- historico de transacoes;
- regras da politica interna via ChromaDB.

### 4. Subir a API FastAPI

```bash
uvicorn src.main:app --reload
```

Healthcheck:

```bash
curl http://127.0.0.1:8000/
```

Resposta esperada:

```json
{
  "status": "online",
  "projeto": "Guardian AI"
}
```

Auditoria via API:

```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Analise o historico do cliente com ID CLI-38726. Ele apresenta alguma inconformidade de acordo com a politica interna?\"}"
```

Formato da resposta:

```json
{
  "pergunta": "Analise o historico do cliente com ID CLI-38726. Ele apresenta alguma inconformidade de acordo com a politica interna?",
  "analise": "Resposta final gerada pelo agente."
}
```

## Observacoes Operacionais

- A primeira execucao pode demorar porque o modelo de embeddings pode ser carregado ou baixado localmente.
- Se a API Gemini retornar `429 RESOURCE_EXHAUSTED`, a chave atingiu limite de quota.
- Se retornar `503 UNAVAILABLE`, o modelo esta temporariamente sob alta demanda.
- Se `gemini-1.5-flash` nao estiver disponivel para a chave atual, defina `GUARDIAN_AGENT_LLM_MODEL` no `.env` com um modelo suportado, como `gemini-2.5-flash`, `gemini-2.0-flash` ou outro listado para sua conta.
