# Prompts Versionados - Guardian AI

Esta pasta registra os prompts usados ou recomendados para o Guardian AI. O objetivo e permitir revisao, comparacao entre versoes e avaliacao de regressao quando o prompt ou o modelo LLM forem alterados.

## Convencao

- `agent_system_v1.md`: prompt principal do agente de auditoria.
- `rag_baseline_system_v1.md`: prompt do baseline RAG sobre a politica interna.
- `tool_guidance_v1.md`: orientacoes de uso das ferramentas.

## Politica de Mudanca

Toda mudanca de prompt deve registrar:

- objetivo da alteracao;
- impacto esperado;
- casos de avaliacao afetados;
- resultado antes/depois nos testes de qualidade.
