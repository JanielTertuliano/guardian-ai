# Matriz de Conformidade AV2 - Guardian AI

## Resultado Geral

O Guardian AI atende ao escopo de projeto de IA Generativa e RAG da especificacao AV2. Esta matriz aponta onde cada requisito esta coberto no repositorio.

| Requisito AV2 | Status | Evidencia |
| --- | --- | --- |
| Problema real de IA | Conforme | `docs/RELATORIO_TECNICO.md`, secao 2 |
| Modalidade aceita: IA Generativa/RAG | Conforme | `src/baseline.py`, `src/agent.py`, `docs/RELATORIO_TECNICO.md` |
| Pipeline de dados | Conforme | `src/generator.py`, `data/*.csv` |
| Base de conhecimento e RAG | Conforme | `data/politica_compliance_guardian.txt`, `src/baseline.py`, `chromadb_cache/` |
| Estrategia de divisao e indexacao | Conforme | `docs/RELATORIO_TECNICO.md`, secao 6 |
| Prompts versionados | Conforme | `prompts/` |
| Avaliacao da qualidade das respostas | Conforme | `tests/evaluation_cases.json`, `tests/evaluate_response_quality.py` |
| API funcional | Conforme | `src/main.py` |
| OpenAPI documentado | Conforme | FastAPI `/docs` |
| Docker | Conforme | `Dockerfile`, `docker-compose.yml` |
| README explicativo | Conforme | `README.md` |
| Relatorio tecnico | Conforme | `docs/RELATORIO_TECNICO.md` |
| Auditoria etica | Conforme | `docs/AUDITORIA_ETICA.md` |
| Defesa oral | Conforme | `presentation/ROTEIRO_DEFESA.md` |
| Repositorio Git publico | A confirmar externamente | Nao e possivel validar publicidade do repositorio a partir do workspace local |

## Observacao sobre Interpretabilidade

Para projetos LLM/RAG, a especificacao permite substituir os requisitos classicos de treino, comparacao baseline vs modelo final e SHAP/LIME por:

- estrategia documentada de divisao e indexacao;
- prompts versionados;
- avaliacao da qualidade das respostas.

Esses tres itens estao cobertos neste repositorio.

## Comandos de Evidencia

Validar artefatos obrigatorios:

```bash
python -m unittest tests.test_evaluation_contract
```

Executar avaliacao de qualidade com a API ligada:

```bash
python tests/evaluate_response_quality.py
```

Executar aplicacao completa:

```bash
docker compose up --build
```
