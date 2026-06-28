import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_PATH = BASE_DIR / "data" / "politica_compliance_guardian.txt"
CHROMA_DIR = BASE_DIR / "chromadb_cache"
PROMPTS_DIR = BASE_DIR / "prompts"
RAG_PROMPT_PATH = PROMPTS_DIR / "rag_baseline_system_v1.md"
COLLECTION_NAME = "guardian_compliance_policy"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "gemini-3.5-flash"


def carregar_variaveis_ambiente():
    """Carrega variaveis de ambiente do arquivo .env e valida a chave do Google."""
    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY nao encontrada. Crie um arquivo .env na raiz do projeto "
            "com a linha: GOOGLE_API_KEY=sua_chave_aqui"
        )

    return api_key


def carregar_politica_compliance():
    """Carrega o manual de compliance usado como fonte documental do RAG."""
    if not POLICY_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo de politica nao encontrado em: {POLICY_PATH}. "
            "Execute a etapa de geracao/estruturacao dos dados antes do Baseline."
        )

    texto_politica = POLICY_PATH.read_text(encoding="utf-8")
    return [
        Document(
            page_content=texto_politica,
            metadata={"source": str(POLICY_PATH)},
        )
    ]


def carregar_prompt_versionado(caminho: Path) -> str:
    """Carrega o prompt versionado e extrai o bloco operacional para a LLM."""
    if not caminho.exists():
        raise FileNotFoundError(
            f"Prompt versionado nao encontrado em {caminho}. "
            "Verifique a pasta prompts/ antes de executar o baseline."
        )

    conteudo = caminho.read_text(encoding="utf-8").strip()
    inicio = conteudo.find("## Prompt")

    if inicio == -1:
        return conteudo

    return conteudo[inicio:].replace("## Prompt", "", 1).strip()


def fatiar_documentos(documentos):
    """Divide o texto em chunks de 500 caracteres com overlap de 50."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return text_splitter.split_documents(documentos)


def criar_modelo_embeddings():
    """Inicializa embeddings locais com sentence-transformers."""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def criar_ou_carregar_vectorstore(chunks, embeddings):
    """Carrega o ChromaDB persistido ou cria o indice vetorial quando vazio."""
    os.makedirs(CHROMA_DIR, exist_ok=True)

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    # Evita duplicar os mesmos chunks em execucoes repetidas do script.
    if vectorstore._collection.count() == 0:
        vectorstore.add_documents(chunks)
        vectorstore.persist()

    return vectorstore


def formatar_documentos(documentos):
    """Formata os documentos recuperados em um unico bloco de contexto."""
    return "\n\n".join(
        f"Trecho {idx}:\n{documento.page_content}"
        for idx, documento in enumerate(documentos, start=1)
    )


def criar_cadeia_qa(vectorstore):
    """Cria a cadeia RAG com prompt versionado e Gemini via LangChain."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    system_prompt = carregar_prompt_versionado(RAG_PROMPT_PATH)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                (
                    "Contexto recuperado do manual interno:\n\n{contexto}\n\n"
                    "Pergunta do usuario:\n{pergunta}"
                ),
            ),
        ]
    )

    modelo_llm = os.getenv("GUARDIAN_LLM_MODEL", LLM_MODEL)
    llm = ChatGoogleGenerativeAI(
        model=modelo_llm,
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    return (
        {
            "contexto": retriever | formatar_documentos,
            "pergunta": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )


def executar_baseline():
    """Orquestra o pipeline RAG local e executa uma pergunta de teste."""
    carregar_variaveis_ambiente()

    print("Carregando politica de compliance...")
    documentos = carregar_politica_compliance()

    print("Fatiando documento em chunks...")
    chunks = fatiar_documentos(documentos)
    print(f"Total de chunks gerados: {len(chunks)}")

    print("Inicializando modelo local de embeddings...")
    embeddings = criar_modelo_embeddings()

    print("Carregando ou criando indice vetorial ChromaDB...")
    vectorstore = criar_ou_carregar_vectorstore(chunks, embeddings)

    print("Configurando cadeia RAG com Gemini...")
    cadeia_qa = criar_cadeia_qa(vectorstore)

    pergunta = "Qual a regra para remessas feitas por clientes PEP acima de USD 100.000?"
    print(f"\nPergunta de teste: {pergunta}")

    resposta = cadeia_qa.invoke(pergunta)

    print("\nResposta gerada pela LLM:")
    print(resposta)


if __name__ == "__main__":
    executar_baseline()
