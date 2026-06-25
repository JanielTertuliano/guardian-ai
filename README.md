# Guardian

Projeto local de IA Generativa e RAG para apoio a análises de Compliance e PLD/CFT em operações de câmbio.

Até agora, o Guardian possui uma base inicial com geração de dados sintéticos, uma política interna de compliance e um pipeline RAG Baseline usando LangChain, Sentence Transformers, ChromaDB e Gemini via Google GenAI.

## Estrutura Atual

```text
.
├── data/
│   └── politica_compliance_guardian.txt
├── src/
│   ├── baseline.py
│   ├── generator.py
│   └── init.py
├── requirements.txt
└── README.md
```

Após executar o gerador, a pasta `data/` também passa a conter:

```text
data/customers.csv
data/transactions.csv
data/compliance_logs.csv
```

Após executar o Baseline RAG, o projeto também cria:

```text
chromadb_cache/
```

## O Que Foi Construído

### 1. Geração de Dados Sintéticos

Arquivo: `src/generator.py`

Responsável por gerar uma base sintética com:

- clientes PF/PJ;
- transações internacionais;
- países de destino, incluindo jurisdições de maior risco;
- marcação de clientes PEP;
- logs simulados de análise de compliance.

Os arquivos gerados são salvos em `data/`:

- `customers.csv`
- `transactions.csv`
- `compliance_logs.csv`

### 2. Política de Compliance

Arquivo: `data/politica_compliance_guardian.txt`

Contém o manual inicial de regras de Compliance e PLD/CFT da Guardian Platform, incluindo:

- alçadas por valor de remessa;
- jurisdições de risco;
- regras para clientes PEP.

### 3. Baseline RAG Local

Arquivo: `src/baseline.py`

Implementa um pipeline RAG básico e local:

- carrega o texto da política de compliance;
- divide o documento em chunks de 500 caracteres com overlap de 50;
- cria embeddings locais com `sentence-transformers/all-MiniLM-L6-v2`;
- persiste o índice vetorial com ChromaDB em `chromadb_cache/`;
- executa busca semântica;
- envia o contexto recuperado para o Gemini usando `ChatGoogleGenerativeAI`;
- responde à pergunta de teste com base estrita na política interna.

## Configuração de Ambiente

Recomendado usar um ambiente virtual Python.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie também um arquivo `.env` na raiz do projeto com sua chave da Gemini API:

```text
GOOGLE_API_KEY=sua_chave_aqui
```

Opcionalmente, você pode definir o modelo Gemini pelo `.env`:

```text
GUARDIAN_LLM_MODEL=gemini-3.5-flash
```

Se o PowerShell bloquear a ativação do ambiente virtual, execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente novamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Como Executar o Projeto

### Etapa 1: Instalar Dependências

Com o ambiente virtual ativo:

```bash
pip install -r requirements.txt
```

### Etapa 2: Gerar Dados Sintéticos

```bash
python src/generator.py
```

Esse comando cria:

```text
data/customers.csv
data/transactions.csv
data/compliance_logs.csv
```

### Etapa 3: Executar o Baseline RAG

```bash
python src/baseline.py
```

Esse comando:

- carrega a política de compliance;
- cria os chunks;
- gera embeddings locais;
- persiste o banco vetorial em `chromadb_cache/`;
- recupera os trechos mais relevantes da política;
- envia a pergunta e o contexto para o Gemini;
- executa uma pergunta de demonstração:

```text
Qual a regra para remessas feitas por clientes PEP acima de USD 100.000?
```

## Dependências

As dependências atuais estão em `requirements.txt`:

```text
pandas
numpy
faker
langchain
langchain-text-splitters
langchain-google-genai
langchain-chroma
langchain-huggingface
chromadb
sentence-transformers
python-dotenv
```

## Observações

- A primeira execução de `src/baseline.py` pode demorar, pois o modelo `sentence-transformers/all-MiniLM-L6-v2` pode ser baixado localmente.
- O Baseline usa uma LLM real via Gemini. Para funcionar, `GOOGLE_API_KEY` precisa estar configurada no arquivo `.env`.
- O diretório `chromadb_cache/` é gerado automaticamente e contém o índice vetorial persistido.
