# Validação executada — 24/09/2026

Os testes abaixo ocorreram no ambiente real AWS/AAP, com tráfego HTTP do operador e jobs nos execution environments do AAP. Estado final: aplicação e PostgreSQL disponíveis; cadastro fictício HTTP 201; controles de falha removidos/consumidos.

## Evidência dos jobs

| Ação | Job AAP | Resultado |
|---|---:|---|
| deploy | [6](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/6/details) | successful |
| verify | [9](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/9/details) | successful |
| fault_database_stop | [10](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/10/details) | successful |
| diagnose | [11](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/11/details) | successful |
| recover_database | [12](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/12/details) | successful |
| fault_validation | [13](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/13/details) | successful |
| validation_evidence | [14](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/14/details) | successful |
| reset_validation | [15](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/15/details) | successful |
| fault_oom_once | [16](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/16/details) | successful |
| diagnose | [17](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/17/details) | successful |
| recover_application | [18](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/18/details) | successful |
| diagnose via MCP | [19](https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io/execution/jobs/playbook/19/details) | successful |

## Asserções executadas

- Baseline: `/health` 200 com banco UP; `/people` 201.
- PostgreSQL parado: saúde e cadastro 503; diagnóstico identificou serviço inativo e evento `DATABASE_UNAVAILABLE`; recuperação restaurou 200/201.
- Defeito de validação: saúde 200, cadastro válido 500; evidência identificou `VALIDATION_RULE_DEMO`, status e request ID. Reset restaurou 201.
- OOM: endpoint tornou-se indisponível; log confirmou `OOM_DEMO_TRIGGER_CONSUMED` e `OutOfMemoryError`; recuperação restaurou saúde/cadastro e não houve redisparo após espera adicional. Isso comprova o cenário de heap da JVM, não um OOM do kernel.
- PAT operacional: tentativas de launch dos templates deploy, fault_database_stop, fault_validation, fault_oom_once e reset_validation foram negadas (403/404).
- Escopo do token: listagem retornou exatamente cinco templates operacionais. Launch de diagnóstico com `extra_vars` e `limit` retornou ambos explicitamente ignorados pelo AAP (job 20), mantendo variáveis vazias e inventário fixo.
- Java: 3 testes unitários passaram, cobrindo entrada válida, distinção entre entrada inválida e falha deliberada, e formulário Unicode. Build também executado na EC2 pelo AAP.
- Sintaxe: todos os playbooks passaram; scripts Python compilaram e scripts Bash passaram `bash -n`.

## Integração MCP

Servidor oficial upstream, revisão `1108adb8309fb4da566285479a11c0b9f0f90469`, com alteração de bind para loopback. Serviço `caixa-demo-mcp.service` ativo no systemd do usuário e socket confirmado apenas em `127.0.0.1:3017`.

Teste de protocolo autenticado: initialize, tools/list (quatro ferramentas), job_templates_list, job_templates_launch_create, jobs_retrieve e jobs_stdout_retrieve passaram. O job 19 foi lançado e seu stdout lido por MCP. Usar `format: "json"` ao ler stdout; `txt` com o Accept JSON do upstream retornou a página HTML de negociação nesta instalação.

OpenCode `mcp list`: aap conectado. Codex `mcp get aap` com o wrapper: habilitado, Streamable HTTP, quatro ferramentas e token por variável. O CLI não carregou automaticamente o arquivo de projeto no teste; o wrapper passa a configuração explicitamente sem alterar configuração global. Não foi executado um turno autônomo de modelo dentro desses clientes nem testada uma sessão Codex Desktop já aberta. A validação cobre configuração, conexão OpenCode e execução MCP real.

Não há MCP nativo no cluster AAP, integração de tickets, teste Lightspeed/OpenSRE nem automação RAG nesta entrega.

## Recursos preservados

EC2 `i-07fc1db76ec70bc27`, VPC `vpc-0ccedacfe92314152`, subnet `subnet-0a17970d38dcc3df2`, security group `sg-0797f077714b427d0`. IPv4 atual `52.91.33.162`. Portas 22/8080 limitadas ao operador; 22 também ao IP de saída AAP observado. Nenhuma porta PostgreSQL pública.

Estado de provisionamento, chave privada, PAT e logs completos estão em diretório privado fora do Git. Não incluir esses arquivos em apresentações. Os recursos continuam ativos; encerramento descrito no README.
