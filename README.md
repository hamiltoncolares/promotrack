# PromoTrack (100% na nuvem)

Aplicacao para monitorar preco de vinhos e enviar e-mail quando houver queda de preco.

Este projeto foi preparado para rodar **sem execucao local**, usando apenas recursos gratuitos do GitHub:
- GitHub Actions para monitoramento recorrente.
- Edicao de arquivos pelo GitHub Web.
- Workflow administrativo para cadastrar/editar/remover trackers por formulario.

## Sumario
1. [Arquitetura](#arquitetura)
2. [Fluxo 100% nuvem](#fluxo-100-nuvem)
3. [Passo a passo inicial (GitHub)](#passo-a-passo-inicial-github)
4. [Usar CLI remoto no GitHub Codespaces](#usar-cli-remoto-no-github-codespaces)
5. [Configurar e-mail (secrets)](#configurar-e-mail-secrets)
6. [Forma 1: cadastrar vinhos editando `config/trackers.yaml`](#forma-1-cadastrar-vinhos-editando-configtrackersyaml)
7. [Forma 2: cadastrar vinhos via workflow Tracker Admin](#forma-2-cadastrar-vinhos-via-workflow-tracker-admin)
8. [Como adicionar novos sites para monitoramento](#como-adicionar-novos-sites-para-monitoramento)
9. [Workflows disponiveis](#workflows-disponiveis)
10. [Estrutura dos dados](#estrutura-dos-dados)
11. [Troubleshooting](#troubleshooting)

## Arquitetura
- `config/sites.yaml`: cadastro de sites suportados (Super Adega + novos sites por CSS selectors).
- `config/trackers.yaml`: cadastro dos vinhos monitorados (fonte de verdade para trackers).
- `data/state.json`: estado interno (ultimo preco, URL encontrada, historico de observacoes).

Fluxo interno:
1. `sync-trackers` sincroniza `config/trackers.yaml` para `data/state.json`.
2. `check` consulta preco dos trackers ativos no periodo.
3. Se houver queda, envia e-mail.
4. O GitHub Action faz commit do `data/state.json` atualizado.

## Fluxo 100% nuvem
Voce nao precisa rodar `python` no seu computador.

Operacao diaria pode ser feita assim:
1. Cadastrar/editar/remover trackers por uma das 2 formas abaixo.
2. Deixar o workflow `Price Monitor` executar no agendamento.
3. Receber e-mail quando houver queda de preco.

## Passo a passo inicial (GitHub)
1. Crie um repositorio no GitHub (ou use um existente).
2. Suba estes arquivos para o repositorio.
3. Verifique se estes workflows existem:
- `.github/workflows/price-monitor.yml`
- `.github/workflows/tracker-admin.yml`
4. Abra a aba `Actions` e habilite workflows, se o GitHub pedir confirmacao.

## Usar CLI remoto no GitHub Codespaces
Este repositorio ja inclui configuracao pronta em:
- `.devcontainer/devcontainer.json`

### Como abrir o Codespace
1. No GitHub, abra o repositorio.
2. Clique em `Code` -> aba `Codespaces`.
3. Clique em `Create codespace on main` (ou na branch desejada).
4. Aguarde a inicializacao do container.

O Codespaces executa automaticamente:
```bash
pip install -r requirements.txt
```

### Comandos CLI remotos (exemplos)
No terminal do Codespace:
```bash
python -m app.main cfg-list
python -m app.main cfg-add --wine "Vinho Catena Malbec" --site superadega --days 30
python -m app.main sync-trackers
python -m app.main check --send-email
```

### Variaveis SMTP no Codespace (teste manual via CLI)
Se quiser testar envio de e-mail manualmente no Codespace, defina:
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="seu_usuario"
export SMTP_PASS="sua_senha_ou_app_password"
export EMAIL_FROM="alertas@seudominio.com"
export EMAIL_TO="voce@seudominio.com"
```

Observacao:
- Para execucao automatica dos workflows, os segredos oficiais continuam sendo os `Repository Secrets` do GitHub Actions.

## Configurar e-mail (secrets)
No GitHub:
`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

Crie os secrets abaixo:
- `SMTP_HOST`
- `SMTP_PORT` (ex.: `587`)
- `SMTP_USER`
- `SMTP_PASS`
- `EMAIL_FROM`
- `EMAIL_TO`

Sem esses secrets o monitoramento roda, mas o envio de e-mail nao funciona.

## Forma 1: cadastrar vinhos editando `config/trackers.yaml`
Essa forma e boa quando voce quer controlar tudo por arquivo versionado.

### Formato do arquivo
Arquivo: `config/trackers.yaml`

Exemplo:
```yaml
trackers:
  - id: catena-malbec-001
    wine_name: "Vinho Catena Malbec"
    site: superadega
    start_date: "2026-03-02"
    end_date: "2026-05-31"
    active: true

  - id: dv-catena-001
    wine_name: "Vinho DV Catena"
    site: superadega
    start_date: "2026-03-10"
    end_date: "2026-06-10"
    active: true
```

Campos:
- `id` (obrigatorio, unico)
- `wine_name` (obrigatorio)
- `site` (obrigatorio; deve existir em `config/sites.yaml`)
- `start_date` (obrigatorio, formato `YYYY-MM-DD`)
- `end_date` (obrigatorio, formato `YYYY-MM-DD`)
- `active` (opcional, default `true`)

### Como aplicar
1. Edite `config/trackers.yaml` no GitHub Web.
2. Commit da alteracao.
3. Execute workflow `Price Monitor` manualmente (ou aguarde o agendamento).

O workflow ja roda `sync-trackers` antes da checagem, entao as mudancas entram automaticamente.

## Forma 2: cadastrar vinhos via workflow Tracker Admin
Essa forma e boa para nao editar YAML manualmente.

### Onde abrir
`Actions` -> `Tracker Admin` -> `Run workflow`

### Acoes disponiveis
- `add`
- `update`
- `remove`
- `list`

### Campos de entrada
- `action`: acao administrativa.
- `tracker_id`: obrigatorio para `update/remove`; opcional para `add`.
- `wine_name`: obrigatorio para `add`.
- `site`: site configurado em `config/sites.yaml` (default no add: `superadega`).
- `start_date` e `end_date`: periodo `YYYY-MM-DD`.
- `days`: alternativa a `start/end`.
- `activate` / `deactivate`: controle de ativo no `update`.

### Comportamento
- O workflow altera `config/trackers.yaml`.
- Em seguida executa `sync-trackers`.
- Faz commit automatico de `config/trackers.yaml` e `data/state.json`.

## Como adicionar novos sites para monitoramento
Arquivo: `config/sites.yaml`

Ja existe suporte nativo:
```yaml
superadega:
  provider: superadega
  enabled: true
```

Para um novo site, use `provider: generic_css`.

Exemplo:
```yaml
superadega:
  provider: superadega
  enabled: true

lojavinhos:
  provider: generic_css
  enabled: true
  base_url: "https://www.lojavinhos.com.br"
  search_url_template: "https://www.lojavinhos.com.br/busca?q={query}"
  card_selector: ".product-card"
  card_name_selector: ".product-card__name"
  card_link_selector: "a"
  card_price_selector: ".product-card__price"
  product_price_selector: ".product-page__price"
  timeout_seconds: 20
```

Depois disso, use `site: lojavinhos` nos trackers.

### Como descobrir seletores CSS
1. Abra o site e faca uma busca por um vinho.
2. Inspecione o card de produto no DevTools.
3. Mapeie nome, link e preco da listagem.
4. Abra a pagina de produto e mapeie o seletor de preco final.
5. Atualize `config/sites.yaml` e commit.

## Workflows disponiveis
### `Price Monitor`
Arquivo: `.github/workflows/price-monitor.yml`

- Agenda: a cada 6 horas.
- Tambem pode rodar manualmente.
- Etapas:
1. instala dependencias
2. sincroniza trackers
3. executa checagem de preco
4. envia e-mail se houver queda
5. commit do `data/state.json`

### `Tracker Admin`
Arquivo: `.github/workflows/tracker-admin.yml`

- Execucao manual por formulario.
- Gerencia trackers sem edicao manual de YAML.
- Commit automatico das alteracoes.

## Estrutura dos dados
### `config/trackers.yaml`
Fonte de verdade dos trackers (o que monitorar, onde, e por quanto tempo).

### `data/state.json`
Estado de execucao:
- trackers sincronizados
- URL de produto encontrada
- ultimo preco observado
- historico de observacoes

## Troubleshooting
### Nao chegou e-mail
- confira secrets SMTP
- confira se SMTP exige App Password
- confira `SMTP_PORT` (geralmente `587`)

### Workflow falhou com erro de tracker invalido
- valide `id` unico
- valide datas em `YYYY-MM-DD`
- valide `end_date >= start_date`

### Workflow falhou dizendo site nao configurado
- `site` do tracker nao existe em `config/sites.yaml`

### Nao encontrou preco
- seletor CSS pode ter mudado
- revise seletores em `config/sites.yaml`

---

Resumo operacional recomendado:
1. Use `Tracker Admin` para operacao rapida (add/update/remove/list).
2. Use edicao direta de `config/trackers.yaml` para alteracoes em lote.
3. Deixe `Price Monitor` rodando no cron.
