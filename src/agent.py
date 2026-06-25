import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CUSTOMERS_PATH = DATA_DIR / "customers.csv"
TRANSACTIONS_PATH = DATA_DIR / "transactions.csv"
CHROMA_DIR = BASE_DIR / "chromadb_cache"
COLLECTION_NAME = "guardian_compliance_policy"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "gemini-1.5-flash"
FALLBACK_LLM_MODEL = "gemini-3.5-flash"


def carregar_variaveis_ambiente():
    """Carrega o .env e valida a chave necessaria para usar o Gemini."""
    load_dotenv(BASE_DIR / ".env")

    if not os.getenv("GOOGLE_API_KEY"):
        raise EnvironmentError(
            "GOOGLE_API_KEY nao encontrada. Crie um arquivo .env na raiz do projeto "
            "com a linha: GOOGLE_API_KEY=sua_chave_aqui"
        )


def obter_modelo_llm():
    """Retorna o modelo configurado para o agente, mantendo gemini-1.5-flash como default."""
    return os.getenv("GUARDIAN_AGENT_LLM_MODEL", LLM_MODEL)


def criar_llm(modelo_llm: str | None = None):
    """Inicializa o modelo Gemini que fara o raciocinio e o function calling."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=modelo_llm or obter_modelo_llm(),
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def _ler_csv_obrigatorio(caminho: Path) -> pd.DataFrame:
    """Le um CSV do projeto e gera erro claro quando o arquivo ainda nao existe."""
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado em {caminho}. Execute python src/generator.py "
            "antes de consultar dados estruturados."
        )

    return pd.read_csv(caminho)


@tool
def consultar_dados_cadastrais(customer_id: str) -> str:
    """Consulta dados cadastrais de um cliente pelo id_cliente.

    Use esta ferramenta quando precisar saber perfil cadastral, tipo de pessoa,
    faturamento anual em USD, score interno de credito, flag status_PEP e pais de
    origem principal de um cliente especifico. O parametro customer_id deve estar
    no formato CLI-12345.
    """
    clientes = _ler_csv_obrigatorio(CUSTOMERS_PATH)
    cliente = clientes[clientes["id_cliente"] == customer_id]

    if cliente.empty:
        return f"Nenhum cliente encontrado para id_cliente={customer_id}."

    # A ferramenta devolve texto estruturado porque esse retorno entra como
    # observacao no historico do agente e sera usado pela LLM no proximo passo.
    return cliente.iloc[0].to_json(force_ascii=False, indent=2)


@tool
def consultar_historico_transacoes(customer_id: str) -> str:
    """Consulta o historico de transacoes financeiras de um cliente pelo id_cliente.

    Use esta ferramenta quando precisar analisar valores transacionados, moedas,
    paises de destino, natureza das operacoes e datas de todas as transacoes de
    um cliente especifico. O parametro customer_id deve estar no formato CLI-12345.
    """
    transacoes = _ler_csv_obrigatorio(TRANSACTIONS_PATH)
    historico = transacoes[transacoes["id_cliente"] == customer_id].copy()

    if historico.empty:
        return f"Nenhuma transacao encontrada para id_cliente={customer_id}."

    historico = historico.sort_values("data_hora")

    # Limita o volume de texto enviado de volta ao modelo para manter a chamada
    # eficiente; o dataset atual e pequeno, mas este padrao evita prompts enormes.
    total_transacoes = len(historico)
    historico = historico.head(20)
    retorno = historico.to_json(orient="records", force_ascii=False, indent=2)

    if total_transacoes > len(historico):
        retorno += (
            f"\n\nObservacao: exibidas {len(historico)} de {total_transacoes} "
            "transacoes encontradas."
        )

    return retorno


@tool
def consultar_politica_compliance(query: str) -> str:
    """Busca regras relevantes na politica interna de compliance e PLD/CFT.

    Use esta ferramenta depois de identificar fatos relevantes nos dados
    estruturados, como status PEP, valores altos, pais de destino de risco ou
    natureza da operacao. O parametro query deve descrever a regra que precisa
    ser verificada, por exemplo: "cliente PEP remessa acima de USD 100.000".
    """
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"Indice vetorial nao encontrado em {CHROMA_DIR}. Execute "
            "python src/baseline.py para criar o chromadb_cache antes da busca."
        )

    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    documentos = vectorstore.similarity_search(query, k=3)

    if not documentos:
        return "Nenhum trecho relevante encontrado na politica interna."

    return "\n\n".join(
        f"Trecho {idx}:\n{documento.page_content}"
        for idx, documento in enumerate(documentos, start=1)
    )


def criar_agent_executor(modelo_llm: str | None = None):
    """Monta o agente com prompt, ferramentas e executor verbose."""
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

    llm = criar_llm(modelo_llm=modelo_llm)
    tools = [
        consultar_dados_cadastrais,
        consultar_historico_transacoes,
        consultar_politica_compliance,
    ]

    # O prompt define a politica de raciocinio. A LLM decide quais ferramentas
    # chamar e com quais argumentos; o AgentExecutor executa as funcoes Python e
    # devolve os resultados para o modelo continuar a analise.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Voce e o Guardian, o agente inteligente de compliance do "
                    "banco. O seu objetivo e analisar se um determinado cliente "
                    "ou transacao infringe as regras de compliance e PLD "
                    "(Prevencao a Lavagem de Dinheiro). Siga a logica de "
                    "raciocinio: primeiro busque os dados estruturados do "
                    "cliente/transacao usando as ferramentas e, em seguida, "
                    "consulte a politica de compliance para verificar se ha "
                    "alguma infracao. Sempre justifique a sua resposta com base "
                    "nos dados encontrados. Quando houver indicio de risco, "
                    "cite objetivamente quais dados acionaram a regra e qual "
                    "acao de compliance e recomendada."
                ),
            ),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )


def _erro_modelo_gemini_indisponivel(erro: Exception) -> bool:
    """Identifica a resposta 404 da API quando um modelo Gemini nao esta disponivel."""
    mensagem = str(erro)
    return (
        "404" in mensagem
        and "NOT_FOUND" in mensagem
        and "generateContent" in mensagem
        and "is not found" in mensagem
    )


def _erro_servico_gemini_temporario_ou_quota(erro: Exception) -> bool:
    """Identifica falhas externas comuns da API Gemini, como quota ou indisponibilidade."""
    mensagem = str(erro)
    return (
        "429 RESOURCE_EXHAUSTED" in mensagem
        or "503 UNAVAILABLE" in mensagem
        or "Quota exceeded" in mensagem
        or "high demand" in mensagem
    )


def _imprimir_erro_gemini(erro: Exception):
    """Mostra uma mensagem curta para erros de provedor sem despejar stack trace."""
    print("\nNao foi possivel concluir a chamada ao Gemini.")
    print(
        "A API retornou limite de quota, alta demanda temporaria ou modelo "
        "indisponivel para a chave atual."
    )
    print(
        "Defina GUARDIAN_AGENT_LLM_MODEL no .env com um modelo disponivel "
        "para sua chave e tente novamente."
    )
    print(f"Detalhe tecnico: {erro}")


def executar_teste_integrado():
    """Executa uma pergunta de auditoria realista contra o agente Guardian."""
    carregar_variaveis_ambiente()
    modelo_llm = obter_modelo_llm()

    exemplo_pergunta = (
        "Analise o historico do cliente com ID CLI-38726. Ele apresenta alguma "
        "inconformidade ou comportamento suspeito de acordo com as regras da "
        "nossa politica de compliance?"
    )

    print("\nPergunta de teste:")
    print(exemplo_pergunta)
    print(f"\nExecutando agente Guardian com function calling usando {modelo_llm}...\n")
    print("Inicializando AgentExecutor e ferramentas...\n", flush=True)

    agent_executor = criar_agent_executor(modelo_llm=modelo_llm)

    try:
        resultado = agent_executor.invoke({"input": exemplo_pergunta})
    except Exception as erro:
        if modelo_llm == LLM_MODEL and _erro_modelo_gemini_indisponivel(erro):
            print(
                f"\nModelo {LLM_MODEL} indisponivel para esta chave/API. "
                f"Tentando fallback com {FALLBACK_LLM_MODEL}...\n"
            )
            agent_executor = criar_agent_executor(modelo_llm=FALLBACK_LLM_MODEL)
            try:
                resultado = agent_executor.invoke({"input": exemplo_pergunta})
            except Exception as erro_fallback:
                if _erro_servico_gemini_temporario_ou_quota(erro_fallback):
                    _imprimir_erro_gemini(erro_fallback)
                    return
                raise
        elif _erro_servico_gemini_temporario_ou_quota(erro):
            _imprimir_erro_gemini(erro)
            return
        else:
            raise

    print("\nResposta final do agente:")
    print(resultado["output"])


if __name__ == "__main__":
    executar_teste_integrado()
