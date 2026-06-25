from datetime import datetime
from pathlib import Path
from time import perf_counter

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout


BASE_URL = "http://127.0.0.1:8000"
AUDIT_ENDPOINT = f"{BASE_URL}/api/audit"
HEALTHCHECK_ENDPOINT = f"{BASE_URL}/"
REPORT_PATH = Path(__file__).resolve().parent.parent / "REGISTRO_DE_AUDITORIA.md"
REQUEST_TIMEOUT_SECONDS = 300


def log(mensagem: str):
    """Imprime logs simples e padronizados no terminal."""
    print(f"[Guardian Test] {mensagem}")


def validar_healthcheck() -> dict:
    """Valida se a API FastAPI esta online e respondendo no endpoint raiz."""
    log("Validando healthcheck em GET / ...")

    response = requests.get(HEALTHCHECK_ENDPOINT, timeout=10)
    response.raise_for_status()

    payload = response.json()

    assert response.status_code == 200, (
        f"Healthcheck retornou status inesperado: {response.status_code}"
    )
    assert payload.get("status") == "online", (
        f"Healthcheck retornou payload inesperado: {payload}"
    )

    log("Healthcheck validado com sucesso. API online.")
    return payload


def executar_auditoria_real() -> tuple[dict, float]:
    """Executa a auditoria real contra o agente e mede o tempo total da resposta."""
    pergunta = (
        "Analise o histórico do cliente com ID CLI-38726 de acordo com as regras "
        "de compliance."
    )
    payload = {"query": pergunta}

    log("Enviando auditoria real para POST /api/audit ...")
    log("Esta etapa mede o tempo total do Agente + RAG + Function Calling + Gemini.")

    inicio = perf_counter()
    response = requests.post(
        AUDIT_ENDPOINT,
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    fim = perf_counter()

    tempo_total = fim - inicio

    response.raise_for_status()
    resultado = response.json()

    assert response.status_code == 200, (
        f"Auditoria retornou status inesperado: {response.status_code}"
    )
    assert "analise" in resultado, (
        f"Resposta da auditoria nao contem o campo 'analise': {resultado}"
    )

    log(f"Auditoria concluida em {tempo_total:.2f} segundos.")
    return resultado, tempo_total


def gerar_relatorio_markdown(status_api: str, tempo_total: float, resultado: dict):
    """Gera o registro formal da auditoria na raiz do projeto."""
    pergunta = resultado.get("pergunta", "")
    analise = resultado.get("analise", "")
    gerado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conteudo = f"""# Registro de Auditoria - Guardian AI

## Resumo Executivo

- **Status da API:** {status_api}
- **Cliente auditado:** CLI-38726
- **Tempo de processamento do agente:** {tempo_total:.2f} segundos
- **Gerado em:** {gerado_em}

## Pergunta de Auditoria

{pergunta}

## Resposta Analitica do Gemini

{analise}
"""

    REPORT_PATH.write_text(conteudo, encoding="utf-8")
    log(f"Relatorio de qualidade gerado em: {REPORT_PATH}")


def main():
    """Orquestra os testes da API e cria o relatorio quando tudo passa."""
    log("Iniciando validacao automatizada da API Guardian AI.")

    try:
        healthcheck = validar_healthcheck()
        resultado_auditoria, tempo_total = executar_auditoria_real()
        gerar_relatorio_markdown(
            status_api=healthcheck.get("status", "desconhecido").capitalize(),
            tempo_total=tempo_total,
            resultado=resultado_auditoria,
        )
    except (ConnectionError, Timeout):
        log(
            "Nao foi possivel conectar na API. Inicie o servidor antes de rodar "
            "os testes: uvicorn src.main:app --reload"
        )
        raise SystemExit(1)
    except RequestException as erro:
        log(f"A API respondeu com erro durante o teste: {erro}")
        log(
            "Verifique se o Gemini esta com quota disponivel e se "
            "GUARDIAN_AGENT_LLM_MODEL esta configurado no .env."
        )
        raise SystemExit(1)
    except AssertionError as erro:
        log(f"Falha de validacao: {erro}")
        raise SystemExit(1)

    log("Todos os testes passaram com sucesso.")


if __name__ == "__main__":
    main()
