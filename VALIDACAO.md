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

## Painel do apresentador — validação adicional em 24/09/2026

Deploy AAP job 25 successful, revisão 3f4d15f. Os três botões foram acionados pelo navegador em `/demo`, com confirmação visual das mudanças de estado:

| Cenário pelo painel | Diagnóstico/evidência via MCP | Recuperação via MCP | Resultado |
|---|---:|---:|---|
| Parar banco | job 27 | job 28 | saúde 503, PostgreSQL inativo, recuperação 200/201 |
| Erro de validação | job 29 | Limpeza pelo apresentador | cadastro 500 com request ID/evento, após limpeza 201 |
| Provocar OOM | job 30 | job 31 | JVM failed, painel 200, banco ativo; recuperação 200/201 |

O log do job 30 confirmou `OOM_DEMO_TRIGGER_CONSUMED` e `OutOfMemoryError`. O painel ficou acessível durante a queda da JVM. As chamadas de diagnóstico, polling, stdout JSON e recuperação ocorreram pelo servidor MCP oficial com o PAT operacional. Não foram necessários credenciais administrativas AAP nem SSH para injetar pelo painel e recuperar pelo MCP.

Proteções verificadas: POST sem origem/cabeçalho retorna 403; tentar outro incidente durante banco parado retorna 409; ação desconhecida retorna 404. O estado final apresenta Java e banco ativos, validação normal e nenhum gatilho OOM pendente. Java compilado e testes unitários aprovados; Python compilado e sintaxe do playbook validada. O arquivo `.codex/config.toml` tinha alterações locais anteriores e foi preservado.

## Workspace operacional e defeito de e-mail — melhoria posterior

Implantação AAP job 37 successful, revisão 2d5dd4d. Workspace criado em `/home/csantana/Projetos/caixa-ai/workspace-trabalho`, fora do repositório ansible-ai-demo e sem cópia do código ou dos roteiros. Configuração de projeto reconhecida por `codex mcp get aap`, com autenticação automática por helper; initialize e tools/list passaram usando esse helper. Instruções exigem investigação via MCP e proíbem consulta ao código, diretórios vizinhos e histórico. É separação de contexto, não isolamento de filesystem. Não foi executado um turno de modelo nessa pasta; a validação cobre carregamento da configuração, autenticação e protocolo MCP.

O formulário permitiu enviar e-mail inválido: HTTP 500 e request ID `98e1619d-28a7-422e-9897-e7b5260ae999`. A coleta pelo MCP no job 39 correlacionou esse ID com `UNHANDLED_EXCEPTION`, `EmailValidationException` e stack trace em `Application.validateEmail`. O job 40 reproduziu a entrada inválida e coletou evidências sem explicação pré-programada da causa.

Um e-mail válido enviado imediatamente depois retornou 201, sem reset. A validação não lê flags nem exige ativação. A antiga ação HTTP de ativação retorna 404. A exceção escapa da camada de negócio; o limite HTTP apenas registra stack trace e responde erro genérico, preservando request ID sem registrar o valor do e-mail. Seis testes locais passaram, incluindo um teste HTTP de status, correlação e ausência de dados da entrada no log/resposta.

Painel atualizado com link para cadastro contendo e-mail inválido e prompt neutro. Serviço Java, PostgreSQL e painel permaneceram ativos ao final. As alterações locais preexistentes em `.codex/config.toml` do repositório foram preservadas.
