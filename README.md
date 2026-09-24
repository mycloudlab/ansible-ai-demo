# Troubleshooting com IA, MCP e Ansible Automation Platform

Demonstração executável: cadastro Java com PostgreSQL em uma EC2 pequena. Codex/OpenCode chamam o MCP oficial do AAP; o AAP executa playbooks fixos no único host `caixa-demo`. O agente operacional não recebe SSH nem credenciais administrativas.

## Ambiente implantado

- Aplicação: http://52.91.33.162:8080 — acesso restrito ao IPv4 do operador.
- AAP: https://aap-aap.apps.cluster-drjqz.dyn.redhatworkshops.io
- AWS: `us-east-1`, instância `i-07fc1db76ec70bc27`, Ubuntu 24.04, `t3.small`, 2 GiB RAM, 12 GiB gp3 criptografado, IMDSv2 obrigatório, CPU em modo Standard.
- Java 17, PostgreSQL 16 local, banco sem porta pública. HTTP sem TLS/autenticação apenas para dados fictícios no laboratório com allowlist.
- Serviço Java: heap 96 MiB, cgroup 256 MiB, sem swap e sem reinício automático. O OOM é da JVM; não pretende reproduzir um OOM global do host.
- Inventário AAP 3, projeto Git 10, organização 3. SSH permitido ao operador e à saída do execution environment do AAP.

O IP público é dinâmico: parar/iniciar a EC2 pode exigir atualização do inventário, URL e allowlist. Credenciais do workshop também podem expirar.

## Templates e roteiros

| Template | ID atual | Quem executa | Efeito |
|---|---:|---|---|
| CAIXA execution_network | 11 | Administrador | Identifica saída IP do AAP |
| CAIXA deploy | 12 | Administrador | Compila, testa e instala aplicação/banco |
| CAIXA diagnose | 13 | Agente | Estado, saúde e até 150 linhas recentes de log |
| CAIXA verify | 14 | Agente | Saúde e cadastro fictício (grava uma linha) |
| CAIXA recover_database | 15 | Agente | Inicia PostgreSQL e verifica cadastro |
| CAIXA recover_application | 16 | Agente | Preserva evidência, remove gatilho e reinicia Java |
| CAIXA validation_evidence | 17 | Agente | Reproduz erro e coleta evidências para chamado |
| CAIXA fault_database_stop | 18 | Administrador | Para somente o banco da demo |
| CAIXA fault_validation | 19 | Administrador | Ativa erro de validação deliberado |
| CAIXA fault_oom_once | 20 | Administrador | Ativa OOM de heap uma única vez |
| CAIXA reset_validation | 21 | Administrador | Restaura baseline de validação |

1. **Banco parado:** administrador executa 18; saúde/cadastro retornam 503. Agente executa 13, identifica PostgreSQL parado, executa 15 e confirma saúde 200/cadastro 201.
2. **Defeito de validação:** administrador executa 19. Um cadastro válido retorna 500 com request ID e evento `VALIDATION_RULE_DEMO`; entrada inválida continua retornando 400. Agente executa 17, prepara evidências e encaminhamento ao desenvolvimento. Nenhum sistema de chamados foi integrado e nenhum chamado real é aberto. Administrador executa 21 para preparar a próxima demonstração.
3. **OOM isolado:** administrador executa 20. A aplicação consome o arquivo de gatilho antes de alocar memória; a JVM registra `OutOfMemoryError` e encerra. Agente executa 13 e 16 e confirma recuperação. Reiniciar é mitigação; retirar o defeito de alocação exige correção de código. O gatilho consumido impede repetição automática após restart.

Não executar injeções em paralelo. Os jobs guardam evidências e podem conter IDs de requisição, mas a aplicação não registra nome, email nem senha. As verificações usam somente dados fictícios `example.invalid`.

## Codex e OpenCode

A instalação AAP inspecionada não publica um endpoint MCP nativo. Usamos o projeto oficial [ansible/aap-mcp-server](https://github.com/ansible/aap-mcp-server), fixado no commit `1108adb8309fb4da566285479a11c0b9f0f90469`, como ponte local para a API do AAP. A única alteração no upstream restringe o bind a `127.0.0.1`; não há bypass de certificado TLS.

O instalador precisa de Node.js 22+, npm, Git, Python 3 e systemd de usuário:

```bash
./scripts/install-mcp.sh
systemctl --user status caixa-demo-mcp
export AAP_TOKEN_FILE=/caminho/privado/aap-runtime-token
./scripts/with-demo-env codex mcp get aap
./scripts/with-demo-env opencode mcp list
./scripts/with-demo-env python3 scripts/test_mcp.py
./scripts/with-demo-env codex
# ou
./scripts/with-demo-env opencode
```

Endpoint: `http://127.0.0.1:3017/mcp/caixa_demo`. Quatro ferramentas: `job_templates_list`, `job_templates_launch_create`, `jobs_retrieve`, `jobs_stdout_retrieve`. `ALLOW_WRITE_OPERATIONS` permite launch; a autorização efetiva é o RBAC do token no AAP, com Execute somente nos cinco templates operacionais. O token não executa deploy nem injeções. Templates não aceitam inventário, limit, credenciais ou extra vars fornecidos no launch.

`.codex/config.toml` e `opencode.json` não contêm segredo. O wrapper injeta o token no ambiente e passa a configuração MCP explicitamente ao Codex: no CLI instalado, a listagem sem override não carregou a configuração do projeto. Não alteramos configurações globais. Para Codex Desktop, iniciar um processo que herde `AAP_TOKEN` e abrir este repositório confiável; uma sessão já aberta não ganha automaticamente o novo servidor/token. O teste direto de protocolo valida initialize, tools/list, listagem de templates, launch, polling e stdout. Para `jobs_stdout_retrieve`, usar `format: "json"`; o formato txt entrou em conflito com o Accept JSON do servidor upstream nesta instalação. A descoberta não equivale a um teste de raciocínio de modelo.

O serviço local inicia com a sessão de usuário; não habilitamos linger. Se trocar o endpoint AAP, atualizar `config/aap-mcp.yaml` e reinstalar/reiniciar o serviço.

Exemplo de prompt para a demonstração:

> Use somente o MCP aap. Liste os templates CAIXA acessíveis, execute diagnose, acompanhe o job e leia stdout. Explique a evidência antes de agir. Para banco parado, use recover_database; para JVM encerrada por OOM, preserve a evidência e use recover_application como mitigação. Para erro de validação, use validation_evidence e prepare um resumo de chamado sem enviá-lo. Confirme o estado final pelos resultados dos jobs. Não use SSH, não altere inventário e não injete falhas.

## Reprodução

Pré-requisitos do operador: AWS CLI autenticado por profile/ambiente, Python 3 com `requests`, Git/SSH, Ansible e Maven/JDK 17+. As credenciais administrativas AAP são necessárias somente ao bootstrap. Não passar senhas em argumentos nem gravá-las no Git. Executar da raiz do repositório; `.private/` é ignorado e deve permanecer com permissão 0700.

1. `python3 scripts/provision_aws.py`: cria VPC/subnet/IGW/SG, chave SSH local e EC2. Estado em `.private/aws-state.json`; repetir para registrar IP após a instância iniciar. O provisionamento assume `us-east-1a` disponível e nome de chave ainda livre. Não apague o estado para tentar corrigir uma execução parcial: inspecione recursos antes de repetir.
2. Configure `AAP_URL`, `AAP_ADMIN_USER` e `AAP_ADMIN_PASSWORD` por ambiente em sessão privada. `python3 scripts/bootstrap_aap.py` cria objetos AAP e dispara `execution_network`. O script usa EE 2 desta instalação; ajuste para um EE suportado no novo AAP, caso necessário. Aguarde projeto e job de rede concluírem.
3. `python3 scripts/runtime_access.py`: concede Execute aos cinco templates, cria PAT privado e libera SSH do IP de saída observado do AAP. Confirme a regra e o estado do job de rede. A chave privada vai apenas à credencial de máquina AAP; nunca ao MCP.
4. Sincronize projeto Git e execute o template `CAIXA deploy` como administrador. Ele instala o pacote `acl` necessário ao become postgres, compila com testes, cria senha aleatória no host (no_log), configura banco e verifica a aplicação.
5. `python3 scripts/test_scenarios.py`: realiza os três cenários e confirma negações de RBAC. Exige credenciais de administrador para injetar falhas, PAT para operar e acesso HTTP permitido ao operador. Resultados/jobs ficam em `.private/`.
6. Instale o MCP e execute os comandos da seção anterior. `DIAGNOSE_TEMPLATE_ID` substitui o ID 13 no teste para outra instalação.

Para compilar localmente: `mvn test package`. Os playbooks usam módulos builtin e não dependem de collections adicionais. Não há endpoint HTTP para injetar falhas; os controles são arquivos locais acessados pelos playbooks administrativos.

## Custos e encerramento

Estimativa sem descontos/créditos, impostos ou tráfego: aproximadamente **US$ 20/mês** para 730 horas de t3.small, um IPv4 público e 12 GiB gp3. Referências oficiais: [T3](https://aws.amazon.com/ec2/instance-types/t3/), [IPv4 público](https://aws.amazon.com/vpc/pricing/) e [EBS](https://aws.amazon.com/ebs/pricing/). AAP usa o workshop existente; consumo de modelos é separado. Não há NAT Gateway nem load balancer.

A demo foi deixada ligada. Para apenas interromper computação, pare a instância; o volume continua cobrado. Para remover definitivamente:

```bash
# Executar na pasta que contém o estado correto. Primeiro apenas mostra o plano:
python3 scripts/teardown_aws.py
# Após conferir IDs, destrói a EC2, seus dados e a rede criada pela demo:
python3 scripts/teardown_aws.py --execute
systemctl --user disable --now caixa-demo-mcp
```

No AAP, remova os templates CAIXA, inventário, projeto e credencial da organização CAIXA AI Demo; revogue o PAT e remova o usuário `caixa-demo-agent`, depois a organização. Não remover objetos Default/APD do workshop. Preserve evidências desejadas antes de remover recursos, token e chave local. O teardown não foi executado.
