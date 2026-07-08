# CLAUDE.md — Sistema Oficial de Inventário de Máquinas

Memória de projeto para sessões de agente. Leia antes de editar.

## Visão geral
Sistema web de inventário de ativos de TI. **Flask + SQLAlchemy + MySQL**, padrão
*application factory* (`create_app()` em `app/__init__.py`). Código e comentários em PT-BR.

## Stack
- Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF (CSRF)
- MySQL via PyMySQL; config por `.env` (python-dotenv), ver `.env.example`
- Extensões instanciadas em `app/extensions.py` (evita import circular)

## Como rodar
```bash
# .venv já existe na pasta
cp .env.example .env          # e ajustar DATABASE_URL / SECRET_KEY
flask --app run:app db upgrade
flask --app run:app seed-admin        # cria ADMIN inicial (idempotente)
flask --app run:app seed-types        # popula os 7 tipos de ativo
flask --app run:app run
```

## Estrutura
- `app/models/` — models (Asset é o centro; 7 specs 1:1 por tipo; User, AuditLog,
  Employee/Department, Branch/Location, Supplier, AssetMovement, MaintenanceRecord)
- `app/routes/` — blueprints: `auth`, `main` (dashboard), `assets`, `maintenance`,
  `registry` (CRUD genérico), `audit` (leitura, só ADMIN)
- `app/utils/` — `audit_listener.py`, `decorators.py`, `spec_config.py`,
  `registry_config.py`, `template_helpers.py`
- `app/templates/`, `app/static/` — camada de apresentação

## Convenções importantes (seguir sempre)
- **Config-driven**: para adicionar/alterar campos de spec de ativo, editar
  `app/utils/spec_config.py`; para cadastros de apoio (fornecedores, unidades,
  localizações, departamentos, funcionários), editar `app/utils/registry_config.py`.
  **Não** duplicar lógica nas rotas — as rotas genéricas leem essas configs.
- **Auditoria automática**: decorar models com `@audit_model` gera CREATE/UPDATE/DELETE
  em `audit_logs` (snapshots, usuário, IP, user-agent). **Nunca** auditar `AuditLog`
  (recursão). `User` propositalmente não é auditado (evita ruído em login).
- **Soft-delete**: registros com `is_active` nunca são removidos fisicamente;
  `delete` seta `is_active = False`. Listagens filtram `is_active.is_(True)`.
- **Autorização**: roles `ADMIN` / `TI` / `VIEWER` (`app/models/enums.py`). **ADMIN = Gestor
  de TI** (acesso total + administra usuários/módulos/config/auditoria). Para os módulos de
  conteúdo (Inventário, Rede, Certificados) o acesso é **100% por módulo** (`Ver`/`Gerenciar`
  do `UserModuleAccess`), NÃO pelo papel: rotas de leitura usam `@module_required(slug)` e as
  de escrita `@module_required(slug, manage=True)`; nas telas `can_edit = can_manage_slug(slug)`
  (helpers em `utils/decorators.py`). Assim TI e VIEWER ficam equivalentes para módulos (o que
  vale é o Ver/Gerenciar). Áreas administrativas (Usuários, Configurações, Auditoria, Gestão do
  Centralizador) seguem ADMIN via `@role_required(ADMIN)`. Slugs: `inventario-maquinas`,
  `infraestrutura-rede`, `certificados`. No form de usuário há atalhos "Acesso total"/"Só
  visualização"/"Remover acessos" (JS) que setam todos os módulos de uma vez.
- **Parsing BR**: datas `YYYY-MM-DD`; decimais aceitam `1.234,56` e `1234.56`
  (ver `_parse_decimal` em `routes/assets.py` e `routes/maintenance.py`).
- **Movimentação**: transferir ativo (`assets/assign`) grava `AssetMovement` (cadeia de
  custódia) além de atualizar o estado atual do Asset.

## Recursos adicionais (jul/2026)
- **Gestão de usuários** (`routes/users.py`, ADMIN): criar com senha temporária,
  editar papel/situação, redefinir senha. Salvaguardas: não rebaixar/desativar o
  último ADMIN, não se auto-desativar.
- **Configurações** (`routes/settings.py`): minha conta, trocar senha, aparência
  (itens/página + densidade, salvos em `users.preferences`) e parâmetros do
  sistema (tabela `settings`: `company_name`, `warranty_window_days`,
  `currency_symbol`) — parâmetros só ADMIN. Ver `utils/settings.py`.
- **Busca automática** nas listagens (Ativos/Manutenções/Auditoria): forms com
  `data-autosubmit`; JS em `static/js/app.js` (debounce em texto, imediato em
  selects, restaura foco). Botão "Filtrar" só aparece via `<noscript>`.
- **Dashboard editável** (`main/dashboard.html`): widgets arrastáveis/ocultáveis
  (SortableJS) + gráficos (Chart.js, ambos via CDN jsdelivr). Layout salvo por
  usuário em `users.preferences.dashboard` (rotas `main.save_layout`/`reset_layout`).
- **Schema**: `Setting` (tabela `settings`) e coluna `users.preferences` (JSON).
  Atualização idempotente via `Atualizar_Banco.bat` → `upgrade_schema.py` (PyMySQL,
  lê `.env`). **IMPORTANTE:** rodar ANTES de subir o código novo — o model já
  referencia `users.preferences`, então sem a coluna qualquer query de User
  (inclusive login) quebra.
- **Notificações**: sino no topo (`base.html`) alimentado por `utils/notifications.py`
  (avisos calculados: garantias vencendo/vencidas, manutenções abertas, sem
  responsável, furtados). Sem tabela — tudo em tempo real.
- **Foto do ativo**: coluna `assets.image_url` guarda o *link* (ex.: Google Drive);
  filtro `drive_img` (em `template_helpers.py`) converte link de compartilhamento em
  URL embutível (`thumbnail?id=`). Nada é armazenado no servidor.
- **Exportar Excel** (`assets.export_assets`, openpyxl), **QR/etiqueta**
  (`assets.qrcode_png`/`assets.label`, qrcode+Pillow) e **termo de responsabilidade
  em PDF** (`assets.termo`/`_build_termo_pdf`, reportlab). Imports são tardios: sem a
  lib, a feature avisa para rodar `Instalar_Dependencias.bat` (o app não quebra).
- **Paginação** na listagem de ativos (usa itens/página da aparência) e **rate limit**
  simples de login por IP (em memória, `routes/auth.py`).
- **Troca de senha obrigatória** (senha temporária): coluna `users.must_change_password`.
- Scripts na raiz: `Popular_Banco.bat` (seed), `Atualizar_Banco.bat` (schema),
  `Instalar_Dependencias.bat` (pip install -r requirements.txt).

## Centralizador Warren (camada de acessos, jul/2026)
- Evolução de "inventário" para **Centralizador de TI**: hub de módulos (`main.hub`,
  `/inicio`, é o destino pós-login). Cada módulo é vinculado a um **sub-setor**.
- Models em `app/models/access.py`: `ITSubsector` (it_subsectors), `Module`
  (it_modules, com `endpoint` do Flask + `subsector_id`), `UserModuleAccess`
  (user_module_access, nível `ModuleAccessLevel` VIEW/MANAGE). `User` ganhou
  `subsector_id` + `is_gestor`/`can_view`/`can_manage`/`_module_level`.
- **Gestor de TI** = `role == ADMIN` (acesso total + administra). Demais usuários:
  acesso **por módulo** (Ver/Gerenciar), definido na tela de edição do usuário.
- Blueprint `access` (`/gestao`, só Gestor): CRUD de sub-setores e módulos.
  `routes/users.py` salva sub-setor + acessos por módulo.
- Schema: tabelas it_subsectors/it_modules/user_module_access + `users.subsector_id`
  (via `upgrade_schema.py`). Seed de teste: `seed_acessos.py` / `Popular_Acessos.bat`.
- Módulo **Infraestrutura** segue no código, mas oculto do menu (link comentado em
  `base.html`).

## Módulo Certificados (Cyber, jul/2026)
- Gestão de certificados digitais dos sistemas externos, com foco em **validade e
  alerta de vencimento por e-mail**. Módulo do Centralizador (slug `certificados`,
  sub-setor `cyber`); endpoint `certificates.list_certificates`.
- Origem dos dados: exportação do **crt.sh (Certificate Transparency)** — tem MUITA
  duplicata. Models em `app/models/certificate.py`: `Certificate` (tabela
  `certificates`, **chave de dedup = `serial_number`**, `not_after`, tracking de
  alerta `last_alert_stage`/`last_alert_sent_on`, soft-delete, `@audit_model`) e
  `CertificateDomain` (tabela `certificate_domains`, 1 linha por SAN; **não auditado**
  de propósito — reconstruído a cada upsert). `status_key`/`days_to_expiry` são
  calculados (não persistidos).
- **Importação idempotente** (`utils/cert_import.py`): upsert por `serial_number`,
  quebra `name_value` (\n) em domínios, infere ambiente (prd/stg/hml/dev). Reimportar
  não duplica. Duas origens: **JSON do crt.sh** (`import_from_json_text`) e **Excel .xlsx**
  (`import_from_xlsx`, openpyxl). O Excel tem mapeamento flexível de cabeçalhos
  (`_HEADER_ALIASES`: serial/CN/domínios/emissor/emissão/validade/obs; ignora dicas entre
  parênteses e acentos) — reconhece tanto os PT-BR do modelo quanto os do monitor real
  (`domain_name`, `ssl_expiration_date`, `base_domain`…) e aceita datas BR (dd/mm/aaaa[ HH:MM]).
  **Sem coluna de serial**, gera chave sintética **por domínio** `XLSX-<domínio>` (reimportar
  a planilha atualizada atualiza no lugar; não cruza com o serial real do JSON). Planilha-modelo
  em `certificates.import_template_xlsx` (`build_template_workbook`).
  Fluxo do Excel = **tela de revisão** (`certificates/import_review.html`): `parse_xlsx` lê sem
  gravar → `_render_xlsx_review` compara com o banco (Novo × Atualizar, muda-validade) e marca
  avisos; o admin seleciona e confirma (`import_confirm` → `import_selected_rows`). **Sem validade
  NÃO bloqueia**: importa com `not_after` nulo (status calculado 'unknown' = "Sem data") p/ filtrar
  e resolver depois; só "sem domínio/nome" bloqueia. Filtro **"Sem validade"** (`status=novalidity`,
  `not_after IS NULL`) na listagem. O JSON do crt.sh continua import direto.
  Também por CLI `flask import-certs <arquivo.json|.xlsx>` (detecta extensão; xlsx grava direto,
  pulando linhas com problema) ou `Importar_Certificados.bat` (arraste o arquivo no .bat).
- **Alertas** (`utils/cert_alerts.py`): estágios 30/15/7/1 dia, no vencimento e
  **diário enquanto vencido**; anti-spam por `last_alert_stage`/`last_alert_sent_on`.
  Destinatários = **todos com acesso ao módulo** (ADMINs + `UserModuleAccess`) +
  `MAIL_ALERT_EXTRA`. Disparo: `flask send-cert-alerts` (`--dry-run`) via
  `Enviar_Alertas_Certificados.bat` (agendar no Agendador de Tarefas do Windows).
  Envio **manual** tem tela de revisão (`certificates.alerts_review` → `/certificados/alertas`,
  template `certificates/alerts.html`): escolhe o alcance (incluir vencidos + janela de
  dias), mostra os certificados incluídos e os destinatários (todos marcados por padrão,
  dá pra desmarcar), e envia um **e-mail-resumo** (`send_manual`/`build_digest_email`) sem
  mexer no anti-spam da automação. Integra também no sino de notificações.
- **E-mail**: `utils/mailer.py` (smtplib/STARTTLS, stdlib, sem dependência nova).
  Config editável por **tela só ADMIN** (`settings.email` → `/settings/email`,
  template `settings/email.html`, com botão de e-mail de teste). Valores ficam na
  tabela `settings` (chaves `mail_*`) e **têm prioridade sobre o `.env`** — resolução
  em `utils/settings.py:mail_settings()` (padrão Google Workspace — exige **Senha de
  app**). A senha nunca é reexibida e as chaves `mail_*` são removidas do contexto
  público de templates via `public_settings()` (o `SETTINGS` do Jinja usa essa versão
  filtrada, não `current_settings()`).
- **Listagem**: filtro reutilizável `_filtered_query(args)` (busca/ambiente/situação),
  paginação, chips de resumo. **Exclusão em lote** (`bulk_delete`, manage): checkboxes por
  linha + "selecionar página" + "selecionar todos os N do filtro" (`select_all_filtered`
  reroda `_filtered_query`); soft-delete. JS no `{% block scripts %}` da `list.html`.
- Autorização por módulo: decorator `module_required(slug, manage=False)` em
  `utils/decorators.py` (Gestor sempre passa; usa `can_view`/`can_manage`).
- Schema: tabelas `certificates`/`certificate_domains` + UPDATE do endpoint do módulo,
  via `upgrade_schema.py` (rodar `Atualizar_Banco.bat`). Filtros de template novos:
  `cert_status_label`/`cert_status_badge`/`cert_env_label`.

## Pendências conhecidas
- `migrations/` não está versionado nesta pasta (Drive) — as alterações de schema
  recentes foram feitas por script (`upgrade_schema.py`), não por Flask-Migrate.
- Auditoria de ações de usuário/`Setting` ainda pendente (leva 2).

## Filtros de template disponíveis
`status_label`, `status_badge`, `condition_label`, `condition_badge`, `brl`, `date_br`,
`humanize`, `audit_label`/`audit_badge`, `maintenance_label`/`maintenance_badge`
(definidos em `app/utils/template_helpers.py`).
