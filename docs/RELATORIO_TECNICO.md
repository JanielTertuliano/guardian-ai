# Relatorio Tecnico - Guardian AI

## 1. Resumo Executivo

O Guardian AI e uma solucao de inteligencia artificial generativa aplicada a auditoria de compliance e PLD/CFT em operacoes de cambio. O sistema combina dados estruturados sinteticos de clientes e transacoes, uma politica interna de compliance indexada em base vetorial, recuperacao aumentada por contexto (RAG), um agente com ferramentas especializadas e uma API operacional em FastAPI empacotada com Docker.

O objetivo do projeto e apoiar analistas de compliance na triagem de clientes e transacoes potencialmente suspeitos. Para isso, o agente consulta dados cadastrais, historico transacional e regras internas antes de gerar uma analise explicada. A resposta final deve indicar se ha indicios de risco, quais evidencias acionaram a regra e qual acao de compliance e recomendada.

O projeto se enquadra na modalidade "IA generativa com LLMs", conforme a especificacao do Projeto Final Integrador AV2. Em vez de treinar parametros de um modelo supervisionado, a equipe construiu uma base de conhecimento, definiu uma estrategia de divisao e indexacao documental, versionou prompts e criou uma avaliacao de qualidade das respostas baseada em casos de teste.

## 2. Problema e Motivacao

Instituicoes financeiras precisam revisar operacoes de cambio com foco em prevencao a lavagem de dinheiro, financiamento ao terrorismo e evasao de divisas. Esse processo envolve cruzar dados cadastrais, valores transacionados, paises de destino, natureza economica da operacao e regras internas.

Na pratica, analistas lidam com informacoes distribuídas em sistemas diferentes. A interpretacao manual pode ser lenta, inconsistente e sujeita a falhas de rastreabilidade. O Guardian AI foi proposto para reduzir essa friccao, organizando a consulta aos dados e explicando a aplicacao das regras de compliance.

O sistema nao substitui a decisao humana. Ele atua como apoio analitico, destacando evidencias, recuperando trechos de politica e sugerindo encaminhamentos. Essa delimitacao e importante porque decisoes de bloqueio, comunicacao regulatoria ou encerramento de relacionamento possuem impacto material sobre pessoas e empresas.

## 3. Escopo da Solucao

O escopo implementado contempla:

- geracao de base sintetica de clientes, transacoes e logs de revisao;
- documento de politica interna com regras de valores, jurisdicoes de risco e clientes PEP;
- indexacao da politica em ChromaDB usando embeddings locais;
- agente LangChain com function calling;
- LLM Gemini configuravel por variavel de ambiente;
- API FastAPI com endpoint de auditoria;
- interface Streamlit para consulta e painel de risco;
- execucao via Docker Compose;
- avaliacao de qualidade por casos definidos.

Fora do escopo desta versao estao integracoes com bases reais, autenticacao corporativa, trilha de auditoria imutavel, retencao regulatoria formal, comunicacao automatica a orgaos reguladores e decisao automatizada de bloqueio.

## 4. Dados Utilizados

A base de dados e sintetica e gerada pelo script `src/generator.py`. Ela contem tres arquivos principais:

- `data/customers.csv`: cadastro de clientes, incluindo identificador, nome, tipo de pessoa, faturamento anual estrangeiro, score interno, flag PEP e pais de origem principal.
- `data/transactions.csv`: historico de transacoes, incluindo identificador, cliente, moedas, valor em USD, valor em BRL, pais de destino, natureza da operacao e data/hora.
- `data/compliance_logs.csv`: logs simulados de alertas, status de revisao e justificativas anteriores.

O uso de dados sinteticos reduz risco de exposicao de informacoes sensiveis. Ainda assim, a estrutura do dataset simula atributos que, em contexto real, exigiriam governanca forte, controle de acesso, minimizacao de dados e justificativa legal para tratamento.

## 5. Base de Conhecimento e RAG

A base de conhecimento documental e representada por `data/politica_compliance_guardian.txt`. O conteudo descreve regras internas de compliance, incluindo:

- classificacao de risco por faixa de valor;
- tratamento de jurisdicoes criticas, como KY e PA;
- regra especifica para clientes PEP acima de USD 100.000;
- exigencia de auditoria documental e aprovacao manual em casos de risco alto.

O script `src/baseline.py` carrega o documento, divide o texto em chunks de 500 caracteres com overlap de 50 e persiste os embeddings em `chromadb_cache/`. O modelo de embeddings utilizado e `sentence-transformers/all-MiniLM-L6-v2`, executado localmente.

Essa abordagem permite que o agente recupere trechos relevantes da politica em tempo de consulta. A recuperacao e feita por similaridade semantica, com `k=3`, retornando os trechos mais proximos da pergunta ou regra consultada.

## 6. Estrategia de Divisao e Indexacao

Para projetos com LLMs, a especificacao da AV2 permite substituir itens de modelagem classica por estrategia documentada de divisao e indexacao de documentos. A estrategia do Guardian AI e:

1. Manter a politica interna como fonte textual controlada.
2. Dividir o documento por separadores naturais: paragrafos, quebras de linha, frases e espacos.
3. Usar chunks pequenos o suficiente para preservar foco semantico.
4. Aplicar overlap para evitar perda de contexto entre fronteiras de chunks.
5. Persistir os vetores em ChromaDB para reuso entre execucoes.
6. Consultar os tres trechos mais relevantes para cada pergunta de politica.

Essa estrategia e adequada para o tamanho atual da politica. Em uma versao maior, com centenas de documentos, seria necessario adicionar metadados por secao, versao normativa, data de vigencia, unidade responsavel e nivel de confianca documental.

## 7. Arquitetura da Aplicacao

A arquitetura segue um fluxo em camadas:

1. Dados sinteticos sao gerados e armazenados em CSV.
2. A politica interna e indexada em uma base vetorial ChromaDB.
3. A API FastAPI recebe uma pergunta de auditoria.
4. O agente LangChain decide quais ferramentas utilizar.
5. As ferramentas consultam cadastro, historico transacional e politica interna.
6. A LLM sintetiza uma resposta final fundamentada.
7. A interface Streamlit exibe painel de risco e chat com o agente.

Os principais arquivos sao:

- `src/generator.py`: geracao de dados.
- `src/baseline.py`: pipeline RAG basico.
- `src/agent.py`: agente com tools.
- `src/main.py`: API FastAPI.
- `src/app.py`: interface Streamlit.
- `tests/test_api.py`: teste end-to-end da API.
- `tests/evaluate_response_quality.py`: avaliacao de qualidade das respostas.

## 8. Agente e Ferramentas

O agente foi implementado com LangChain e Gemini. Ele utiliza function calling para decidir quando chamar cada ferramenta. As ferramentas disponiveis sao:

- `consultar_dados_cadastrais(customer_id)`;
- `consultar_historico_transacoes(customer_id)`;
- `consultar_politica_compliance(query)`.

O prompt de sistema instrui o agente a primeiro buscar dados estruturados e depois consultar a politica interna. A resposta deve justificar a conclusao com base nos dados encontrados, citando indicios de risco e acao recomendada.

Os prompts foram externalizados na pasta `prompts/` para cumprir o requisito de versionamento. O codigo ainda contem o prompt operacional usado em execucao, mas a pasta de prompts documenta a versao vigente, o objetivo e os criterios esperados de resposta.

## 9. API e Deploy

A API esta implementada em FastAPI no arquivo `src/main.py`. Os endpoints principais sao:

- `GET /`: healthcheck.
- `POST /api/audit`: recebe uma pergunta e retorna a analise do agente.

O FastAPI disponibiliza documentacao OpenAPI automaticamente em `/docs`. O projeto inclui `Dockerfile` e `docker-compose.yml`, com dois servicos:

- `guardian-api`: servidor FastAPI na porta 8000.
- `guardian-ui`: interface Streamlit na porta 8501.

O Compose monta `data/` e `chromadb_cache/` como volumes, preservando dados sinteticos e indice vetorial entre recriacoes de container.

## 10. Avaliacao da Qualidade das Respostas

A avaliacao da qualidade e baseada em casos definidos em `tests/evaluation_cases.json`. Cada caso especifica:

- identificador do caso;
- pergunta de auditoria;
- tipo de risco esperado;
- termos que devem aparecer na resposta;
- ferramentas esperadas;
- criterio de sucesso.

O script `tests/evaluate_response_quality.py` executa esses casos contra a API em funcionamento e gera um relatorio Markdown em `REGISTRO_QUALIDADE_RESPOSTAS.md`. A avaliacao verifica se a resposta contem evidencias essenciais, como identificador do cliente, jurisdicao de risco, cliente PEP, valor limite ou acao recomendada.

Essa avaliacao nao substitui julgamento humano, mas cria uma base objetiva para medir regressao de comportamento. Caso uma alteracao de prompt ou modelo passe a omitir evidencias obrigatorias, o teste sinaliza queda de qualidade.

## 11. Resultados Esperados

Para uma consulta sobre cliente PEP com remessa acima do limite, espera-se que o agente:

- consulte os dados cadastrais;
- identifique a flag `status_PEP = 1`;
- consulte o historico transacional;
- recupere a regra de PEP acima de USD 100.000;
- recomende alerta e dupla checagem de compliance.

Para uma consulta sobre jurisdicao de risco, espera-se que o agente:

- identifique transacoes com destino KY ou PA;
- relacione essas jurisdicoes a risco critico;
- avalie a natureza da operacao;
- recomende retencao ou analise manual quando aplicavel.

Para valores acima de USD 500.000, espera-se que a resposta indique classificacao de risco alto e necessidade de auditoria documental estrita.

## 12. Auditoria Etica

O Guardian AI lida com um dominio sensivel. Mesmo usando dados sinteticos, o caso simula decisoes que poderiam afetar acesso a servicos financeiros. Os principais riscos eticos sao:

- falsos positivos que gerem bloqueio injustificado;
- falsos negativos que deixem passar operacoes suspeitas;
- interpretacao incorreta de perfis PEP;
- uso indevido de pais de origem como proxy discriminatorio;
- explicacoes convincentes porem nao fundamentadas;
- dependencia excessiva do modelo por parte do analista.

Para mitigar esses riscos, o projeto adota:

- uso de dados sinteticos;
- resposta explicada com base em evidencias;
- recuperacao de trechos da politica interna;
- recomendacao de revisao humana;
- avaliacao por casos de teste;
- documentacao de limitacoes.

O sistema deve ser usado como apoio e nao como decisor final. Em ambiente produtivo, seria necessario adicionar controle de acesso, logs auditaveis, monitoramento de vieses, revisao periodica de regras e validacao juridica.

## 13. Limitacoes

As principais limitacoes atuais sao:

- base documental pequena;
- ausencia de dados reais;
- dependencia de disponibilidade e quota da API Gemini;
- avaliacao de qualidade ainda baseada em termos esperados;
- ausencia de metricas quantitativas robustas como precisao, recall ou F1;
- prompts versionados em arquivos, mas ainda duplicados no codigo;
- pouca cobertura de testes unitarios isolados;
- ausencia de autenticacao na API.

Essas limitacoes sao aceitaveis para uma prova de conceito academica, mas devem ser resolvidas antes de qualquer uso corporativo real.

## 14. Reprodutibilidade

O ambiente pode ser reproduzido localmente com:

```bash
pip install -r requirements.txt
python src/generator.py
python src/baseline.py
uvicorn src.main:app --reload
streamlit run src/app.py
```

Tambem pode ser executado via Docker:

```bash
docker compose up --build
```

A API fica disponivel em `http://127.0.0.1:8000` e a interface em `http://127.0.0.1:8501`.

## 15. Conclusao

O Guardian AI atende ao escopo de um projeto final de IA generativa com RAG. Ele entrega pipeline de dados, base vetorial, agente orquestrado, API operacional, interface web, Docker, prompts versionados e avaliacao de qualidade.

Do ponto de vista tecnico, o projeto demonstra integracao entre dados estruturados e conhecimento documental. Do ponto de vista etico, reconhece limitacoes e posiciona o sistema como ferramenta de apoio a decisao humana.

Como evolucao, recomenda-se ampliar a base de regras, criar metricas quantitativas de avaliacao, integrar testes automatizados a CI/CD, separar prompts do codigo em tempo de execucao e adicionar controles de seguranca para uso multiusuario.

## Referencias

- Documentacao oficial FastAPI.
- Documentacao LangChain sobre agents e tools.
- Documentacao ChromaDB.
- Documentacao Google Gemini API.
- Politica interna sintetica `data/politica_compliance_guardian.txt`.
- Especificacao do Projeto Final Integrador AV2.
