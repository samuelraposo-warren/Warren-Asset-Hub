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
- **Autorização**: roles `ADMIN` / `TI` / `VIEWER` (`app/models/enums.py`). Criar/editar
  ativos e cadastros exige ADMIN ou TI via `@role_required(*_EDITORS)`. Auditoria só ADMIN.
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

## Pendências conhecidas
- `migrations/` não está versionado nesta pasta (Drive) — as alterações de schema
  recentes foram feitas por script (`upgrade_schema.py`), não por Flask-Migrate.
- Auditoria de ações de usuário/`Setting` ainda pendente (leva 2).

## Filtros de template disponíveis
`status_label`, `status_badge`, `condition_label`, `condition_badge`, `brl`, `date_br`,
`humanize`, `audit_label`/`audit_badge`, `maintenance_label`/`maintenance_badge`
(definidos em `app/utils/template_helpers.py`).
