# Auditoria Etica - Guardian AI

## Objetivo

Este documento registra os principais riscos eticos, vieses potenciais e medidas de mitigacao do Guardian AI. A analise considera que o sistema apoia auditorias de compliance e PLD/CFT, um dominio sensivel por envolver clientes, transacoes financeiras e possiveis restricoes operacionais.

## Dados e Privacidade

O projeto usa dados sinteticos gerados localmente. Isso reduz risco de exposicao de informacoes pessoais reais. Ainda assim, a estrutura da base simula dados sensiveis, como status PEP, pais de origem, faturamento e historico financeiro.

Em ambiente real, esses dados exigiriam:

- base legal para tratamento;
- minimizacao de campos;
- controle de acesso por perfil;
- criptografia em repouso e em transito;
- logs de acesso;
- politicas de retencao e descarte;
- revisao juridica e regulatoria.

## Riscos de Vies

O sistema pode reproduzir vieses caso regras ou dados sejam mal desenhados. Os principais riscos sao:

- associar pais de origem a risco de forma indevida;
- usar score interno sem explicacao de sua origem;
- tratar clientes PEP sempre como suspeitos, em vez de apenas exigir maior diligencia;
- gerar maior escrutinio para determinados perfis sem justificativa documental;
- confundir jurisdicao de destino com caracteristica pessoal do cliente.

## Riscos Operacionais

Os riscos operacionais mais relevantes sao:

- falso positivo: cliente ou transacao legitima marcada como suspeita;
- falso negativo: operacao suspeita sem alerta;
- resposta da LLM sem base suficiente;
- uso da recomendacao como decisao automatica;
- falha de disponibilidade da API Gemini;
- mudanca de comportamento apos troca de modelo.

## Mitigacoes Implementadas

O projeto implementa as seguintes mitigacoes:

- usa dados sinteticos;
- obriga o agente a consultar dados estruturados e politica interna;
- recupera trechos documentais por RAG;
- usa temperatura 0 para reduzir variabilidade;
- expõe a resposta como recomendacao analitica, nao decisao final;
- inclui avaliacao por casos de teste;
- documenta prompts versionados;
- registra limitacoes tecnicas.

## Mitigacoes Recomendadas para Producao

Antes de uso real, recomenda-se:

- manter humano no loop para qualquer acao restritiva;
- registrar os passos intermediarios do agente em trilha de auditoria;
- criar politica de contestacao e revisao manual;
- monitorar taxas de falso positivo por perfil de cliente;
- validar periodicamente regras e prompts;
- bloquear perguntas fora do escopo;
- remover ou mascarar dados pessoais desnecessarios;
- aplicar autenticacao, autorizacao e segregacao de funcoes.

## Posicionamento Etico

O Guardian AI deve ser tratado como ferramenta de apoio. Ele organiza evidencias, recupera regras e sugere encaminhamentos, mas nao deve decidir bloqueios, encerramentos de relacionamento ou comunicacoes regulatorias sem revisao humana qualificada.

## Conclusao

O projeto reconhece os riscos do uso de IA em compliance financeiro e estabelece controles iniciais adequados para uma prova de conceito academica. Para uso operacional, seriam necessarias camadas adicionais de governanca, seguranca, monitoramento e accountability.
