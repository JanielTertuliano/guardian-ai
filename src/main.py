from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(
    title="Guardian AI",
    description="API de auditoria de compliance baseada em agentes LangChain e RAG.",
    version="1.0.0",
)

# CORS aberto nesta fase para permitir que futuras interfaces web/mobile
# consumam a API durante o desenvolvimento. Em producao, restrinja origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditRequest(BaseModel):
    """Contrato de entrada da rota de auditoria."""

    query: str


_agent_executor = None
_agent_model = None
_agent_lock = Lock()


def _extrair_texto_resposta(valor) -> str:
    """Extrai apenas texto legivel de respostas em string, dict ou blocos Gemini."""
    if valor is None:
        return ""

    if isinstance(valor, str):
        return valor

    if isinstance(valor, list):
        partes = [_extrair_texto_resposta(item) for item in valor]
        return "".join(parte for parte in partes if parte)

    if isinstance(valor, dict):
        if isinstance(valor.get("text"), str):
            return valor["text"]

        if "content" in valor:
            return _extrair_texto_resposta(valor["content"])

        partes = []
        for chave, item in valor.items():
            if chave in {"extras", "signature", "index", "type"}:
                continue
            partes.append(_extrair_texto_resposta(item))
        return "".join(parte for parte in partes if parte)

    return str(valor)


def _carregar_modulo_agente():
    """Importa o modulo do agente sob demanda para manter o startup da API leve."""
    from src import agent

    return agent


def _obter_agent_executor(modelo_llm: str | None = None):
    """Inicializa e reutiliza o AgentExecutor para evitar recriacao a cada request."""
    global _agent_executor, _agent_model

    agent = _carregar_modulo_agente()
    modelo = modelo_llm or agent.obter_modelo_llm()

    with _agent_lock:
        if _agent_executor is None or _agent_model != modelo:
            agent.carregar_variaveis_ambiente()
            _agent_executor = agent.criar_agent_executor(modelo_llm=modelo)
            _agent_model = modelo

    return _agent_executor


def _executar_auditoria_com_fallback(query: str) -> str:
    """Executa o agente e trata fallback de modelo quando a API Gemini recusar o default."""
    agent = _carregar_modulo_agente()
    modelo = agent.obter_modelo_llm()
    executor = _obter_agent_executor(modelo_llm=modelo)

    try:
        resultado = executor.invoke({"input": query})
    except Exception as erro:
        if modelo == agent.LLM_MODEL and agent._erro_modelo_gemini_indisponivel(erro):
            executor = _obter_agent_executor(modelo_llm=agent.FALLBACK_LLM_MODEL)
            try:
                resultado = executor.invoke({"input": query})
            except Exception as erro_fallback:
                if agent._erro_servico_gemini_temporario_ou_quota(erro_fallback):
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "A API Gemini retornou limite de quota, alta demanda "
                            "temporaria ou modelo indisponivel para a chave atual."
                        ),
                    ) from erro_fallback
                raise
        elif agent._erro_servico_gemini_temporario_ou_quota(erro):
            raise HTTPException(
                status_code=503,
                detail=(
                    "A API Gemini retornou limite de quota, alta demanda "
                    "temporaria ou modelo indisponivel para a chave atual."
                ),
            ) from erro
        else:
            raise

    return _extrair_texto_resposta(resultado.get("output")).strip()


@app.get("/")
def healthcheck():
    """Healthcheck simples para confirmar que a API esta online."""
    return {"status": "online", "projeto": "Guardian AI"}


@app.post("/api/audit")
def auditar_requisicao(payload: AuditRequest):
    """Recebe uma pergunta de auditoria, aciona o agente e retorna a analise final.

    A LLM decide quais ferramentas chamar: CSVs para dados estruturados e
    ChromaDB para politica interna. A API devolve apenas a pergunta original e
    a resposta final, mantendo os passos intermediarios fora do JSON publico.
    """
    pergunta = payload.query.strip()

    if not pergunta:
        raise HTTPException(status_code=400, detail="O campo query nao pode ser vazio.")

    try:
        resposta_final = _executar_auditoria_com_fallback(pergunta)
    except HTTPException:
        raise
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar auditoria pelo agente Guardian: {erro}",
        ) from erro

    return {"pergunta": pergunta, "analise": resposta_final}
