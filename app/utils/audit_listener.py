"""Auditoria automática via SQLAlchemy event listeners.

Uso: decore os models que devem ser auditados com ``@audit_model``.

    from app.utils.audit_listener import audit_model

    @audit_model
    class Asset(db.Model):
        ...

A partir daí, toda inserção, atualização e exclusão do model gera um
registro em ``audit_logs`` capturando:
  - a tabela e o id do registro afetado;
  - a ação (CREATE / UPDATE / DELETE);
  - o usuário logado (quando houver contexto de requisição);
  - snapshots old_values / new_values (em UPDATE, só as colunas alteradas);
  - IP e user-agent da requisição.

Implementação: os listeners `after_insert`, `before_update` e
`before_delete` são registrados por model via decorator. A escrita no
audit_log é feita diretamente na ``connection`` do flush em andamento
(via `AuditLog.__table__.insert()`), evitando reentrar na sessão que já
está em flush.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import event, inspect
from sqlalchemy.orm.attributes import get_history

from app.models.enums import AuditAction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _serialize(value):
    """Converte um valor de coluna para algo serializável em JSON."""
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return value


def _request_context():
    """Retorna (user_id, ip, user_agent) do contexto atual, se houver.

    Tudo protegido por try/except: os listeners também disparam fora de
    um request (seeds, scripts CLI, testes) — nesses casos os campos ficam
    nulos em vez de quebrar a operação.
    """
    user_id = ip = user_agent = None
    try:
        from flask import has_request_context, request

        if has_request_context():
            ip = request.remote_addr
            user_agent = (request.user_agent.string or None)
            if user_agent:
                user_agent = user_agent[:400]

            from flask_login import current_user

            if getattr(current_user, "is_authenticated", False):
                user_id = current_user.id
    except Exception:  # noqa: BLE001 — auditoria nunca deve quebrar o fluxo
        pass
    return user_id, ip, user_agent


def _column_snapshot(target):
    """Dicionário {coluna: valor_serializado} de todas as colunas."""
    mapper = inspect(target).mapper
    return {
        col.key: _serialize(getattr(target, col.key))
        for col in mapper.column_attrs
    }


def _write_log(connection, target, action, old_values, new_values):
    """Insere um registro em audit_logs na connection do flush atual."""
    # Import tardio evita importação circular (audit.py -> extensions).
    from app.models.audit import AuditLog

    user_id, ip, user_agent = _request_context()

    connection.execute(
        AuditLog.__table__.insert().values(
            table_name=target.__tablename__,
            record_id=getattr(target, "id", None),
            action=action,
            changed_by_id=user_id,
            changed_at=datetime.utcnow(),
            old_values=old_values,
            new_values=new_values,
            ip_address=ip,
            user_agent=user_agent,
        )
    )


# ---------------------------------------------------------------------------
# Listeners
# ---------------------------------------------------------------------------
def _after_insert(mapper, connection, target):
    _write_log(
        connection,
        target,
        AuditAction.CREATE,
        old_values=None,
        new_values=_column_snapshot(target),
    )


def _before_update(mapper, connection, target):
    old_values, new_values = {}, {}
    for col in mapper.column_attrs:
        hist = get_history(target, col.key)
        if not hist.has_changes():
            continue
        old_values[col.key] = _serialize(hist.deleted[0]) if hist.deleted else None
        new_values[col.key] = _serialize(hist.added[0]) if hist.added else None

    # Sem alterações reais de coluna (ex.: só relacionamentos tocados) ->
    # não registra nada.
    if not new_values:
        return

    _write_log(
        connection, target, AuditAction.UPDATE, old_values, new_values
    )


def _before_delete(mapper, connection, target):
    _write_log(
        connection,
        target,
        AuditAction.DELETE,
        old_values=_column_snapshot(target),
        new_values=None,
    )


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------
def audit_model(cls):
    """Marca um model para auditoria automática (CREATE/UPDATE/DELETE)."""
    event.listen(cls, "after_insert", _after_insert)
    event.listen(cls, "before_update", _before_update)
    event.listen(cls, "before_delete", _before_delete)
    return cls
