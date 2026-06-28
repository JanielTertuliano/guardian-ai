import ast
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOMERS_PATH = BASE_DIR / "data" / "customers.csv"
TRANSACTIONS_PATH = BASE_DIR / "data" / "transactions.csv"
DEFAULT_API_URL = "http://127.0.0.1:8000"
API_URL = os.getenv("GUARDIAN_API_URL", DEFAULT_API_URL).rstrip("/")


st.set_page_config(
    page_title="Guardian AI - Sistema de Auditoria",
    page_icon="🛡️",
    layout="wide",
)


st.markdown(
    """
    <style>
        .main {
            background-color: #f7f9fb;
        }
        .guardian-header {
            padding: 1.25rem 1.5rem;
            border-left: 6px solid #0f766e;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 1px 8px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
        }
        .guardian-kicker {
            color: #0f766e;
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.04rem;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }
        .guardian-title {
            color: #0f172a;
            font-size: 2rem;
            font-weight: 800;
            margin: 0;
        }
        .guardian-subtitle {
            color: #475569;
            font-size: 1rem;
            margin-top: 0.5rem;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dbe4ea;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 6px rgba(15, 23, 42, 0.06);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega os CSVs usados no painel de risco."""
    if not CUSTOMERS_PATH.exists() or not TRANSACTIONS_PATH.exists():
        raise FileNotFoundError(
            "Arquivos de dados nao encontrados. Execute python src/generator.py antes."
        )

    clientes = pd.read_csv(CUSTOMERS_PATH)
    transacoes = pd.read_csv(TRANSACTIONS_PATH)
    return clientes, transacoes


def formatar_moeda_brl(valor: float) -> str:
    """Formata valores monetarios em BRL para exibicao executiva."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def renderizar_cabecalho():
    """Renderiza o cabecalho visual da aplicacao."""
    st.markdown(
        """
        <div class="guardian-header">
            <div class="guardian-kicker">Compliance Intelligence Platform</div>
            <h1 class="guardian-title">Guardian AI - Sistema de Auditoria</h1>
            <div class="guardian-subtitle">
                Analise de PLD/CFT com RAG, dados estruturados e agente com Function Calling.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def renderizar_painel_risco():
    """Exibe metricas e dados brutos para apoio ao auditor."""
    try:
        clientes, transacoes = carregar_dados()
    except FileNotFoundError as erro:
        st.error(str(erro))
        return

    total_clientes = len(clientes)
    clientes_pep = int(clientes["status_PEP"].sum()) if "status_PEP" in clientes else 0
    volume_total = (
        float(transacoes["valor_brl"].sum()) if "valor_brl" in transacoes else 0.0
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Clientes", f"{total_clientes:,}".replace(",", "."))
    col2.metric("Clientes PEP Identificados", f"{clientes_pep:,}".replace(",", "."))
    col3.metric("Volume Total Auditado", formatar_moeda_brl(volume_total))

    st.divider()

    st.subheader("Base de Clientes")
    st.dataframe(clientes, use_container_width=True, hide_index=True)

    st.subheader("Transacoes Financeiras")
    st.dataframe(transacoes, use_container_width=True, hide_index=True)


def consultar_agente(pergunta: str) -> str:
    """Chama a API FastAPI que orquestra o AgentExecutor."""
    response = requests.post(
        f"{API_URL}/api/audit",
        json={"query": pergunta},
        timeout=300,
    )
    response.raise_for_status()
    payload = response.json()
    return formatar_resposta_auditoria(
        extrair_texto_resposta(payload.get("analise", "A API nao retornou o campo 'analise'."))
    )


def extrair_texto_resposta(valor) -> str:
    """Remove metadados tecnicos de respostas em blocos e conserva apenas o texto."""
    if valor is None:
        return ""

    if isinstance(valor, str):
        texto = valor.strip()
        if texto.startswith("[") and "'text'" in texto:
            try:
                return extrair_texto_resposta(ast.literal_eval(texto))
            except (SyntaxError, ValueError):
                return valor
        return valor

    if isinstance(valor, list):
        return "".join(extrair_texto_resposta(item) for item in valor)

    if isinstance(valor, dict):
        if isinstance(valor.get("text"), str):
            return valor["text"]

        if "content" in valor:
            return extrair_texto_resposta(valor["content"])

        partes = []
        for chave, item in valor.items():
            if chave in {"extras", "signature", "index", "type"}:
                continue
            partes.append(extrair_texto_resposta(item))
        return "".join(partes)

    return str(valor)


def formatar_resposta_auditoria(texto: str) -> str:
    """Organiza a resposta do agente em secoes Markdown para exibicao no chat."""
    texto = texto.strip()
    secoes = {
        "Justificativa:": "### Justificativa",
        "Dados que acionaram a regra:": "### Dados que acionaram a regra",
        "Ação de compliance recomendada:": "### Ação de compliance recomendada",
        "Acao de compliance recomendada:": "### Acao de compliance recomendada",
    }

    for marcador, titulo in secoes.items():
        texto = texto.replace(f"\n\n{marcador}", f"\n\n{titulo}\n")
        if texto.startswith(marcador):
            texto = texto.replace(marcador, f"{titulo}\n", 1)

    return texto


def inicializar_chat():
    """Prepara o historico de chat em memoria de sessao do Streamlit."""
    if "mensagens" not in st.session_state:
        st.session_state.mensagens = [
            {
                "role": "assistant",
                "content": (
                    "Informe um cliente ou transacao para auditoria. Exemplo: "
                    "Analise o cliente CLI-38726."
                ),
            }
        ]


def renderizar_central_agente():
    """Renderiza a interface de chat conectada ao Guardian Agent."""
    inicializar_chat()

    st.caption(f"API conectada em: `{API_URL}`")

    for mensagem in st.session_state.mensagens:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    pergunta = st.chat_input("Digite uma pergunta de auditoria para o Guardian...")

    if not pergunta:
        return

    st.session_state.mensagens.append({"role": "user", "content": pergunta})

    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando agente, RAG e politicas internas..."):
            try:
                resposta = consultar_agente(pergunta)
            except requests.exceptions.ConnectionError:
                st.error(
                    "Nao foi possivel conectar na API FastAPI. "
                    "Inicie o servidor com: uvicorn src.main:app --reload"
                )
                return
            except requests.exceptions.Timeout:
                st.error("A consulta demorou demais e excedeu o limite de tempo.")
                return
            except requests.exceptions.HTTPError as erro:
                detalhe = erro.response.text if erro.response is not None else str(erro)
                st.error(f"A API retornou erro durante a auditoria: {detalhe}")
                return
            except requests.exceptions.RequestException as erro:
                st.error(f"Erro inesperado ao chamar a API: {erro}")
                return

            st.markdown(resposta)

    st.session_state.mensagens.append({"role": "assistant", "content": resposta})


def main():
    """Ponto de entrada da aplicacao Streamlit."""
    renderizar_cabecalho()

    aba_risco, aba_agente = st.tabs(["📊 Painel de Risco", "💬 Central do Agente"])

    with aba_risco:
        renderizar_painel_risco()

    with aba_agente:
        renderizar_central_agente()


if __name__ == "__main__":
    main()
