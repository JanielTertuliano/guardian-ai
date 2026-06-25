# Guardian AI: Sistema de Auditoria de Compliance Baseado em Agentes e RAG

## Descricao Breve

O Guardian AI automatiza a analise de Compliance e PLD/CFT em operacoes de cambio. O sistema cruza politicas internas recuperadas por RAG com dados estruturados de clientes e transacoes, permitindo que um agente de IA identifique indicios de risco, inconformidades e justificativas com base documental.

O projeto combina:

- dados sinteticos de clientes, transacoes e logs de compliance;
- politica interna de compliance indexada em ChromaDB;
- embeddings locais com `sentence-transformers`;
- agente LangChain com Function Calling;
- Gemini como LLM;
- API Web com FastAPI para expor a auditoria a futuras interfaces;
- testes automatizados com `requests` e geracao de relatorio Markdown.

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

5. Testes automatizados e registro de auditoria

   O script `tests/test_api.py` valida a API em execucao, mede o tempo de resposta do agente e gera `REGISTRO_DE_AUDITORIA.md` com a resposta analitica completa para o cliente `CLI-38726`.

## Estrutura do Projeto

```text
.
|-- data/
|   |-- compliance_logs.csv
|   |-- customers.csv
|   |-- politica_compliance_guardian.txt
|   `-- transactions.csv
|-- src/
|   |-- agent.py
|   |-- baseline.py
|   |-- generator.py
|   |-- init.py
|   `-- main.py
|-- tests/
|   `-- test_api.py
|-- chromadb_cache/
|-- .env
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- REGISTRO_DE_AUDITORIA.md
`-- README.md
```

## O Que Cada Arquivo Faz

- `src/generator.py`: gera a base sintetica usada nos testes do Guardian. Ele cria clientes PF/PJ, transacoes internacionais, paises de destino, clientes PEP e logs simulados de revisao de compliance.
- `src/baseline.py`: monta o primeiro pipeline RAG do projeto. Ele le a politica interna, divide o texto em chunks, gera embeddings locais, cria ou carrega o indice ChromaDB e faz uma pergunta de demonstracao ao Gemini.
- `src/agent.py`: implementa o agente inteligente de compliance. Ele usa LangChain, Function Calling e Gemini para decidir quando consultar dados cadastrais, historico de transacoes e regras da politica interna no ChromaDB.
- `src/main.py`: expoe o agente como uma API Web FastAPI. Ele fornece o healthcheck `GET /` e a rota `POST /api/audit`, que recebe uma pergunta e retorna a analise final do agente em JSON.
- `tests/test_api.py`: executa a validacao automatizada da API em funcionamento. Ele testa o healthcheck, chama a auditoria real, mede o tempo de resposta e gera `REGISTRO_DE_AUDITORIA.md`.
- `data/politica_compliance_guardian.txt`: contem as regras internas usadas pelo RAG, incluindo limites por valor, jurisdicoes de risco e regras para clientes PEP.
- `data/customers.csv`: contem os clientes sinteticos gerados, com perfil cadastral, faturamento, score interno e flag PEP.
- `data/transactions.csv`: contem as transacoes sinteticas usadas pelo agente para identificar possiveis comportamentos suspeitos.
- `data/compliance_logs.csv`: contem logs simulados de revisoes anteriores de compliance.
- `chromadb_cache/`: armazena o indice vetorial persistido pelo ChromaDB. Essa pasta permite reutilizar os embeddings sem recriar tudo a cada execucao.
- `requirements.txt`: lista as dependencias Python necessarias para executar geracao de dados, RAG, agente, API e testes.
- `Dockerfile`: define a imagem Docker da aplicacao, instala dependencias de sistema e Python, copia o codigo e inicia a API com Uvicorn.
- `docker-compose.yml`: orquestra o servico `guardian-api`, injeta variaveis do `.env`, publica a porta 8000 e persiste `data/` e `chromadb_cache/`.
- `.env`: guarda configuracoes sensiveis e locais, principalmente `GOOGLE_API_KEY` e opcionalmente `GUARDIAN_AGENT_LLM_MODEL`.
- `REGISTRO_DE_AUDITORIA.md`: relatorio gerado automaticamente pelos testes com status da API, tempo de processamento e resposta analitica do Gemini.

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

### 5. Executar testes automatizados da API

Com o servidor FastAPI rodando em outro terminal:

```bash
python tests/test_api.py
```

O teste executa:

- `GET /` para validar se a API esta online;
- `POST /api/audit` com uma pergunta real sobre o cliente `CLI-38726`;
- medicao do tempo total da consulta Agente + RAG + Function Calling + Gemini;
- criacao do arquivo `REGISTRO_DE_AUDITORIA.md` na raiz do projeto.

Se o servidor estiver desligado, o script exibe uma mensagem orientando a iniciar:

```bash
uvicorn src.main:app --reload
```

O relatorio gerado contem:

- status da API;
- cliente auditado;
- tempo total de processamento;
- pergunta enviada;
- resposta analitica completa retornada pelo Gemini.

### 6. Executar com Docker

O projeto inclui `Dockerfile` e `docker-compose.yml` para empacotar a API FastAPI e suas dependencias.

Antes de subir o container, confirme que o arquivo `.env` existe na raiz do projeto:

```text
GOOGLE_API_KEY=sua_chave_aqui
GUARDIAN_AGENT_LLM_MODEL=gemini-2.5-flash
```

Suba a aplicacao:

```bash
docker compose up --build
```

A API ficara disponivel em:

```text
http://127.0.0.1:8000
```

Valide o healthcheck:

```bash
curl http://127.0.0.1:8000/
```

Execute uma auditoria:

```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Analise o historico do cliente com ID CLI-38726 de acordo com as regras de compliance.\"}"
```

Ver logs do servico:

```bash
docker compose logs -f guardian-api
```

Parar a aplicacao:

```bash
docker compose down
```

O `docker-compose.yml` monta os diretorios locais abaixo dentro do container:

```text
./data:/app/data
./chromadb_cache:/app/chromadb_cache
```

Assim, os CSVs sinteticos e o indice ChromaDB persistem entre recriacoes do container.

## Observacoes Operacionais

- A primeira execucao pode demorar porque o modelo de embeddings pode ser carregado ou baixado localmente.
- Se a API Gemini retornar `429 RESOURCE_EXHAUSTED`, a chave atingiu limite de quota.
- Se retornar `503 UNAVAILABLE`, o modelo esta temporariamente sob alta demanda.
- Se `gemini-1.5-flash` nao estiver disponivel para a chave atual, defina `GUARDIAN_AGENT_LLM_MODEL` no `.env` com um modelo suportado, como `gemini-2.5-flash`, `gemini-2.0-flash` ou outro listado para sua conta.
- O teste `tests/test_api.py` depende da API estar ligada e de quota/modelo Gemini disponivel para concluir a auditoria real.
- Na primeira execucao Docker, o build pode demorar porque instala dependencias pesadas como ChromaDB, sentence-transformers e bibliotecas numericas.
