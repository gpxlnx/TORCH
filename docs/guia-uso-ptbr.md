# TORCH + Hilton HackerOne: runbook do começo ao relatório

Este é um roteiro operacional para a superfície **web** do programa Hilton.
Execute primeiro a Parte 1 no Bash. Depois abra o Claude Code e siga a Parte 2.

> Autorização não é estática. Antes de cada sessão, confira a página
> [Hilton no HackerOne](https://hackerone.com/hilton). A política oficial sempre
> prevalece sobre este documento. Este snapshot foi conferido em 2026-08-19.

## Regras que valem durante toda a execução

- Todo HTTP/HTTPS deve usar um User-Agent contendo `HackerOne`.
- Scans automatizados: máximo oficial de 100 requests/minuto/site; este guia usa
  1 request/segundo e uma thread.
- Pare ao receber `429`, `Retry-After`, timeouts repetidos, aumento de latência ou
  bloqueios uniformes. Não troque de IP para continuar.
- Não faça DoS, brute force de credenciais, engenharia social ou reservas.
- Use somente contas e registros próprios. First Name e Last Name das contas de
  teste devem começar com `Test-Hackerone`.
- Se aparecer dado real de cliente, pare, retenha somente a evidência mínima e
  avise o programa.
- Resultado de scanner não é finding: reproduza manualmente e demonstre impacto.

### Web scope deste runbook

```text
hilton.com
*.hilton.com
hilton.io
*.hilton.io
hiltonbusinessonline.com
*.hiltonbusinessonline.com
hiltonlocalbiz.com
*.hiltonlocalbiz.com
resmax.hilton.com
```

Não use este roteiro para CIDRs, aplicativos móveis, propriedades ou aplicações
de terceiros. Também não teste os seguintes ativos:

```text
*.hamptonhotels.com.cn
*.hiltonhotels.jp
a1.hilton.com
eis.hilton.com
guestfeedback.hilton.com
hgv.com
hiltonfoundation.org
hiltongrandvacations.com
hiltonnet.hilton.com
jobs.hilton.com
onqinsider.hilton.com
pim.hilton.com
```

Qualquer `*.hilton.com` que resolva para IP pertencente à Rackspace também fica
fora do escopo. Essa exclusão exige verificação de DNS e ownership por host.

---

# Parte 1 — o que digitar no Bash

## 1. Entrar no TORCH e verificar a instalação

```bash
cd /home/gxavier/tstsh/TORCH
export PATH="$HOME/.bun/bin:$PATH"
python3 scripts/campaign-doctor.py --verbose
```

Se o doctor apontar skills ou hooks ausentes:

```bash
bash setup/install-skills.sh
bash setup/install-hooks.sh
qmd update
python3 scripts/check-hooks.py
```

Resultado esperado: nenhuma falha no driver. Não use
`bash setup/new-engagement.sh --help`: esse script não possui essa opção.

## 2. Criar ou reabrir o engagement

Na primeira execução:

```bash
bash setup/new-engagement.sh hilton-h1 bugbounty \
  --scope hilton.com \
  --scope hilton.io \
  --scope hiltonbusinessonline.com \
  --scope hiltonlocalbiz.com \
  --scope resmax.hilton.com
```

Se `targets/hilton-h1/` já existir, não execute o comando de criação novamente.
Apenas torne-o ativo:

```bash
printf '%s\n' hilton-h1 > targets/active.md
```

## 3. Preencher o escopo e o RoE

```bash
nano targets/hilton-h1/scope.md
```

No frontmatter, ajuste estes campos:

```yaml
no_bruteforce: true
no_dos: true
passive_only: false
tunnel_safe: false
autonomy: supervised
enum_cap: 5
write_policy: own-records-only
oob_allowed: false
scanners: conditional
budget_requests: 500
rate_per_host: 1
target_severity: HIGH
sources:
  - https://hackerone.com/hilton
```

No corpo do arquivo, use:

```markdown
## In scope
- hilton.com
- hilton.io
- hiltonbusinessonline.com
- hiltonlocalbiz.com
- resmax.hilton.com

## Out of scope
- *.hamptonhotels.com.cn
- *.hiltonhotels.jp
- a1.hilton.com
- eis.hilton.com
- guestfeedback.hilton.com
- hgv.com
- hiltonfoundation.org
- hiltongrandvacations.com
- hiltonnet.hilton.com
- jobs.hilton.com
- onqinsider.hilton.com
- pim.hilton.com

## Allowed tooling
- OSINT passivo
- Browser e Caido com User-Agent contendo HackerOne
- httpx, ffuf e nuclei com 1 req/s e uma thread
- Validação manual antes do reporte

## Rules of engagement
- Fonte de verdade: https://hackerone.com/hilton
- Todo HTTP/HTTPS contém HackerOne no User-Agent
- Sem DoS, brute force, reservas ou interação com clientes
- Somente contas próprias Test-Hackerone e registros próprios
- Subdomínios Hilton em Rackspace são out of scope
- Dados reais encontrados: parar e notificar
```

Agora inicialize o driver:

```bash
python3 scripts/campaign.py --eng hilton-h1 init --type bb
python3 scripts/campaign.py --eng hilton-h1 ledger
```

## 4. Conferir a Kali VM

O TORCH executa as ferramentas ofensivas na Kali por `/root/vm.sh`:

```bash
bash /root/vm.sh 'command -v subfinder; command -v httpx; command -v ffuf; command -v nuclei'
```

Se uma ferramenta estiver ausente, provisione a VM antes de continuar:

```bash
bash scripts/vm-provision.sh --list
bash scripts/vm-provision.sh
```

## 5. Fazer recon passivo

Execute o `subfinder` na Kali e salve a saída no engagement local:

```bash
for domain in \
  hilton.com \
  hilton.io \
  hiltonbusinessonline.com \
  hiltonlocalbiz.com
do
  bash /root/vm.sh "subfinder -d $domain -silent"
done | sort -u > targets/hilton-h1/ingest/subdomains-passive.txt
```

Garanta que o host nomeado também esteja presente:

```bash
printf '%s\n' resmax.hilton.com \
  >> targets/hilton-h1/ingest/subdomains-passive.txt
sort -u -o targets/hilton-h1/ingest/subdomains-passive.txt \
  targets/hilton-h1/ingest/subdomains-passive.txt
```

Retire as exclusões explícitas de `hilton.com`:

```bash
rg -v '^(a1|eis|guestfeedback|hiltonnet|jobs|onqinsider|pim)\.hilton\.com$' \
  targets/hilton-h1/ingest/subdomains-passive.txt \
  > targets/hilton-h1/ingest/candidates.txt
```

## 6. Revisar DNS, CNAME e Rackspace

Produza uma planilha textual para revisão:

```bash
while IFS= read -r host
do
  printf '\n[%s]\n' "$host"
  dig +short A "$host"
  dig +short CNAME "$host"
done < targets/hilton-h1/ingest/candidates.txt \
  | tee targets/hilton-h1/ingest/dns-review.txt
```

Para cada IP ou CNAME duvidoso:

```bash
whois IP_ENCONTRADO
```

Crie manualmente a allowlist final. Inclua somente hosts do scope atual cuja
atribuição foi revisada e que não pertençam à Rackspace:

```bash
nano targets/hilton-h1/in-scope-reviewed.txt
```

Um host por linha, sem `https://`. Não avance enquanto houver ownership ambíguo.

## 7. Enviar a allowlist para a Kali

```bash
HILTON_SCOPE_B64=$(base64 -w0 targets/hilton-h1/in-scope-reviewed.txt)
bash /root/vm.sh "mkdir -p /tmp/hilton-h1; echo '$HILTON_SCOPE_B64' | base64 -d > /tmp/hilton-h1/in-scope-reviewed.txt"
```

## 8. Descobrir serviços HTTP

Inicie uma janela persistente na Kali:

```bash
bash scripts/vm-scan.sh --win httpx hilton-h1 web \
  "httpx -l /tmp/hilton-h1/in-scope-reviewed.txt -silent -sc -title -td -ip -rate-limit 1 -threads 1 -H 'User-Agent: Mozilla/5.0 TORCH-Research HackerOne' -o /tmp/hilton-h1/httpx-reviewed.txt"
```

Acompanhe sem iniciar outro scan na mesma janela:

```bash
bash /root/vm.sh 'tmux capture-pane -p -t hilton-h1:httpx -S -80'
```

Quando terminar, traga o resultado para o TORCH:

```bash
bash /root/vm.sh 'base64 -w0 /tmp/hilton-h1/httpx-reviewed.txt' \
  | base64 -d > targets/hilton-h1/ingest/httpx-reviewed.txt
```

Opcionalmente capture a execução como artefato de recon:

```bash
bash scripts/capture.sh recon hilton-h1 httpx-reviewed httpx
```

## 9. Validar o fan-out interno sem executá-lo

```bash
RECON_WEB_DRYRUN=1 bash scripts/recon-web.sh \
  hilton-h1 https://www.hilton.com/
```

Para Hilton, nunca remova `RECON_WEB_DRYRUN=1`: `recon-web.sh` não injeta sozinho
o User-Agent obrigatório nem garante o limite real de 100 requests/minuto.

## 10. Rodar ffuf somente em um host revisado

Escolha um único host da allowlist e uma wordlist pequena:

```bash
bash scripts/vm-scan.sh --win ffuf-www hilton-h1 www.hilton.com \
  "ffuf -u 'https://www.hilton.com/FUZZ' -w /usr/share/seclists/Discovery/Web-Content/common.txt -H 'User-Agent: Mozilla/5.0 TORCH-Research HackerOne' -rate 1 -t 1 -ic -o /tmp/hilton-h1/ffuf-www.json -of json"
```

Quando terminar:

```bash
bash /root/vm.sh 'base64 -w0 /tmp/hilton-h1/ffuf-www.json' \
  | base64 -d > targets/hilton-h1/ingest/ffuf-www.json
```

Não transforme a allowlist inteira em loop de ffuf. O board do TORCH deve escolher
qual ativo e qual superfície justificam aprofundamento.

## 11. Rodar Nuclei focado

Use somente templates high/critical não intrusivos contra um host revisado:

```bash
bash scripts/vm-scan.sh --win nuclei-www hilton-h1 www.hilton.com \
  "nuclei -u 'https://www.hilton.com/' -severity high,critical -exclude-tags dos,fuzz,intrusive,default-login -rl 1 -c 1 -H 'User-Agent: Mozilla/5.0 TORCH-Research HackerOne' -o /tmp/hilton-h1/nuclei-www.txt"
```

Quando terminar:

```bash
bash /root/vm.sh 'base64 -w0 /tmp/hilton-h1/nuclei-www.txt' \
  | base64 -d > targets/hilton-h1/ingest/nuclei-www.txt
```

Uma correspondência do Nuclei é apenas um candidato. Não envie relatório sem
reprodução manual, diferencial e impacto.

## 12. Abrir o Claude Code

```bash
cd /home/gxavier/tstsh/TORCH
export PATH="$HOME/.bun/bin:$PATH"
claude
```

---

# Parte 2 — o que digitar no Claude Code

## 13. Validar, ingerir e iniciar o workflow

Digite, um comando por vez:

```text
/campaign-health
/ingest
/coverage
/bb-workflow
```

O que acontece:

1. `/campaign-health` valida driver, hooks e skills.
2. `/ingest` lê todos os arquivos de `targets/hilton-h1/ingest/`, atualiza
   `state.md` e arquiva o material processado.
3. `/coverage` mostra o que ainda não foi testado.
4. `/bb-workflow` chama `campaign.py next`, executa uma ação por vez e atualiza o
   board. Não mantenha outro checklist paralelo.

Se o Claude quiser navegar com o navegador automatizado, pare antes da primeira
URL. `browser.sh` não define o User-Agent Hilton. Configure primeiro no Caido uma
regra de rewrite restrita ao scope, acrescentando `HackerOne`, e confirme o header
em uma requisição capturada. Sem essa confirmação, use somente os comandos
`curl`, `httpx`, `ffuf` e `nuclei` deste guia.

## 14. Consultar a próxima ação manualmente, se necessário

Em um segundo terminal Bash:

```bash
python3 scripts/campaign.py --eng hilton-h1 next
```

Use esse comando para diagnóstico ou aprendizado. Durante a operação normal,
deixe `/bb-workflow` controlar o loop e não marque passes ou linhas manualmente em
paralelo.

Se estiver deliberadamente operando o driver à mão, cada passe termina assim:

```bash
python3 scripts/campaign.py --eng hilton-h1 pass-done
python3 scripts/campaign.py --eng hilton-h1 next
```

Depois dos passes 0 a 3:

```bash
python3 scripts/campaign.py --eng hilton-h1 board
python3 scripts/campaign.py --eng hilton-h1 next
```

`pass-done` não recebe o número do passe.

## 15. Trabalhar uma linha de vulnerabilidade

O driver imprime a linha, a classe, a skill e a ferramenta obrigatórias. Exemplo
para autenticação:

No Claude:

```text
/wiki-arsenal deep auth
```

No Bash, registre o arsenal usando o número de linha mostrado pelo driver:

```bash
python3 scripts/campaign.py --eng hilton-h1 note 4a:1 --arsenal auth
python3 scripts/campaign.py --eng hilton-h1 next
```

De volta ao Claude:

```text
/hunt-auth
```

Outras skills web existentes, usadas somente quando o driver as mapear:

```text
/hunt-api
/hunt-idor
/hunt-bizlogic
/hunt-cache
/hunt-deserialization
/hunt-injection
/hunt-rce
/hunt-secrets
/hunt-smuggling
/hunt-sqli
/hunt-ssrf
/hunt-upload
/hunt-xss
/fuzz
```

Não execute todas cegamente. O TORCH trabalha por par ativo × classe: arsenal,
skill, ferramenta, evidência e encerramento da linha.

Para conferir lacunas a qualquer momento:

```text
/coverage
```

## 16. Contas e testes autenticados

Antes de `/hunt-auth`, `/hunt-idor`, `/hunt-api` ou `/hunt-bizlogic`, crie duas
contas controladas por você, por exemplo:

```text
Conta A
First Name: Test-HackeroneResearcherA
Last Name:  Test-HackeroneAccountA

Conta B
First Name: Test-HackeroneResearcherB
Last Name:  Test-HackeroneAccountB
```

Registre apenas identificadores não secretos em
`targets/hilton-h1/identities.md`. Não salve senhas, cookies ou tokens em arquivos
rastreados. Não conclua reservas e não tente IDs pertencentes a usuários reais.

## 17. Capturar evidência de uma reprodução manual

Depois de confirmar um comportamento em endpoint observado, execute no Bash:

```bash
bash scripts/capture.sh req hilton-h1 auth-differential -- \
  -A 'Mozilla/5.0 TORCH-Research HackerOne' \
  'https://HOST_REVISADO/ENDPOINT_CONFIRMADO'
```

O comando imprime o caminho real, normalmente
`targets/hilton-h1/poc/NN-auth-differential.png`. Use exatamente esse caminho ao
fechar a linha.

No Claude:

```text
/triage
/evidence
```

## 18. Encerrar a linha do board

Sem vulnerabilidade:

```bash
python3 scripts/campaign.py --eng hilton-h1 done 4a:1 \
  --dead 'nenhum diferencial após validação controlada'
```

Teste incompatível com o RoE ou ownership incerto:

```bash
python3 scripts/campaign.py --eng hilton-h1 done 4a:1 \
  --park 'teste fora do envelope autorizado'
```

Com evidência válida, mas ainda sem finding:

```bash
python3 scripts/campaign.py --eng hilton-h1 done 4a:1 \
  --poc targets/hilton-h1/poc/NN-auth-differential.png \
  --kind req
```

Substitua `4a:1`, `NN` e o slug pelos valores reais. Nunca marque como concluído
sem executar a skill mapeada e capturar a evidência exigida.

## 19. Criar um finding confirmado

No Bash:

```bash
mkdir -p targets/hilton-h1/Vulns/Research
cp setup/templates/_find.md \
  targets/hilton-h1/Vulns/Research/FIND-001-HIGH-titulo.md
nano targets/hilton-h1/Vulns/Research/FIND-001-HIGH-titulo.md
```

Preencha ativo, pré-condições, passos, request/response, impacto, evidência de que
somente dados próprios foram usados, User-Agent, taxa e remediação. Redija tokens,
cookies, senhas e PII.

Valide:

```bash
python3 scripts/find-lint.py
```

Depois registre o finding na linha:

```bash
python3 scripts/campaign.py --eng hilton-h1 done 4a:1 \
  --find FIND-001-HIGH-titulo.md \
  --poc targets/hilton-h1/poc/NN-auth-differential.png \
  --kind req
```

No Claude:

```text
/triage
/evidence
/learn
```

A checkout atual menciona `Skill(report)` no fechamento do workflow, mas não
contém `skills/workflow/report/SKILL.md`. Portanto, não digite `/report` até essa
skill existir. O caminho funcional atual é `_find.md` + `/triage` + `/evidence` +
`find-lint.py`, seguido do envio manual pela HackerOne.

## 20. Repetir até encerrar a cobertura

No Claude:

```text
/bb-workflow
/coverage
```

No Bash, acompanhe o estado:

```bash
python3 scripts/campaign.py --eng hilton-h1 ledger
python3 scripts/campaign.py --eng hilton-h1 board
python3 scripts/campaign.py --eng hilton-h1 next
```

Repita o ciclo até cada linha aplicável estar concluída, descartada com motivo ou
parked por RoE. Um scan “completo” significa cobertura documentada do board, não
executar todas as ferramentas contra todos os hosts.

## 21. Fechamento local

```bash
python3 scripts/find-lint.py
bash scripts/check-leaks.sh
python3 scripts/campaign.py --eng hilton-h1 ledger --json
```

Envie cada finding separadamente pelo botão **Submit report** do programa Hilton.
Não publique detalhes sem consentimento expresso da Hilton.

## Referências

- [Hilton no HackerOne](https://hackerone.com/hilton)
- [Definição de scope na HackerOne](https://docs.hackerone.com/en/articles/8494552-defining-scope)
- [`docs/virtual-machine.md`](virtual-machine.md)
- [`skills/workflow/bb-workflow/SKILL.md`](../skills/workflow/bb-workflow/SKILL.md)
- [`scripts/campaign.py`](../scripts/campaign.py)
