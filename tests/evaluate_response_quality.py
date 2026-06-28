from datetime import datetime
import json
from pathlib import Path
from time import perf_counter
import unicodedata

import requests
from requests.exceptions import RequestException


BASE_DIR = Path(__file__).resolve().parent.parent
CASES_PATH = BASE_DIR / "tests" / "evaluation_cases.json"
REPORT_PATH = BASE_DIR / "REGISTRO_QUALIDADE_RESPOSTAS.md"
API_URL = "http://127.0.0.1:8000/api/audit"
TIMEOUT_SECONDS = 300


def carregar_casos():
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def normalizar_texto(texto: str) -> str:
    texto_sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )
    return texto_sem_acentos.casefold()


def avaliar_resposta(texto: str, termos_obrigatorios: list[str]) -> tuple[int, list[str]]:
    texto_normalizado = normalizar_texto(texto)
    encontrados = [
        termo
        for termo in termos_obrigatorios
        if normalizar_texto(termo) in texto_normalizado
    ]
    return len(encontrados), encontrados


def executar_caso(caso: dict) -> dict:
    inicio = perf_counter()
    response = requests.post(
        API_URL,
        json={"query": caso["query"]},
        timeout=TIMEOUT_SECONDS,
    )
    duracao = perf_counter() - inicio
    response.raise_for_status()

    payload = response.json()
    analise = payload.get("analise", "")
    score, encontrados = avaliar_resposta(analise, caso["required_terms"])
    total = len(caso["required_terms"])

    return {
        "id": caso["id"],
        "expected_risk": caso["expected_risk"],
        "query": caso["query"],
        "score": score,
        "total": total,
        "passed": score == total,
        "found_terms": encontrados,
        "missing_terms": [
            termo for termo in caso["required_terms"] if termo not in encontrados
        ],
        "duration_seconds": duracao,
        "analysis": analise,
    }


def gerar_relatorio(resultados: list[dict]):
    total = len(resultados)
    aprovados = sum(1 for item in resultados if item["passed"])
    gerado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    linhas = [
        "# Registro de Qualidade das Respostas - Guardian AI",
        "",
        f"- **Gerado em:** {gerado_em}",
        f"- **Casos avaliados:** {total}",
        f"- **Casos aprovados:** {aprovados}",
        f"- **Taxa de aprovacao:** {(aprovados / total * 100 if total else 0):.1f}%",
        "",
        "## Resultados por Caso",
        "",
    ]

    for item in resultados:
        status = "APROVADO" if item["passed"] else "REPROVADO"
        linhas.extend(
            [
                f"### {item['id']} - {status}",
                "",
                f"- **Risco esperado:** {item['expected_risk']}",
                f"- **Score:** {item['score']}/{item['total']}",
                f"- **Tempo:** {item['duration_seconds']:.2f}s",
                f"- **Termos encontrados:** {', '.join(item['found_terms']) or 'nenhum'}",
                f"- **Termos ausentes:** {', '.join(item['missing_terms']) or 'nenhum'}",
                "",
                "**Pergunta:**",
                "",
                item["query"],
                "",
                "**Resposta do agente:**",
                "",
                item["analysis"],
                "",
            ]
        )

    REPORT_PATH.write_text("\n".join(linhas), encoding="utf-8")


def main():
    casos = carregar_casos()
    resultados = []

    try:
        for caso in casos:
            resultados.append(executar_caso(caso))
    except RequestException as erro:
        raise SystemExit(
            "Nao foi possivel executar a avaliacao. Confirme que a API esta "
            f"online em {API_URL}. Detalhe: {erro}"
        ) from erro

    gerar_relatorio(resultados)

    if not all(item["passed"] for item in resultados):
        raise SystemExit(1)

    print(f"Relatorio de qualidade gerado em: {REPORT_PATH}")


if __name__ == "__main__":
    main()
