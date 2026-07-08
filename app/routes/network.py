"""Blueprint do módulo Infraestrutura (mapa de rede / cabeamento).

Telas de ocupação: visão geral por rack/painel, grade de pontos de um painel,
busca de pontos e edição de um ponto (status, o que está plugado, área).
Desacoplado do inventário.
"""
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from app.extensions import db
from app.models.asset import Asset
from app.models.employee import Employee
from app.models.enums import PortStatus, UserRole
from app.models.network import (
    NetworkArea,
    NetworkDesk,
    NetworkEquipment,
    NetworkPoint,
    NetworkSeat,
    NetworkSector,
    PatchPanel,
    Rack,
)
from app.utils.decorators import can_manage_slug, module_required

network_bp = Blueprint("network", __name__, url_prefix="/infra")

# Módulo "Infraestrutura de Rede". Ver exige can_view; escrever exige manage.
MODULE_SLUG = "infraestrutura-rede"

# Tipos sugeridos (usados nos <select> das telas).
AREA_KINDS = ["CPD", "Sala técnica", "Operações", "Escritório", "Recepção", "Outro"]
EQUIP_KINDS = ["Servidor", "Switch", "Roteador", "Desktop", "Notebook",
               "Storage", "Nobreak", "Telefone", "Outro"]


def _status_counts_by_panel():
    """{panel_id: {status_name: count}} para os pontos ativos."""
    rows = (
        db.session.query(
            NetworkPoint.patch_panel_id, NetworkPoint.status, func.count()
        )
        .filter(NetworkPoint.is_active.is_(True))
        .group_by(NetworkPoint.patch_panel_id, NetworkPoint.status)
        .all()
    )
    out = {}
    for panel_id, status, count in rows:
        out.setdefault(panel_id, {})[status.value] = count
    return out


def _rows_per_page():
    try:
        return int((current_user.get_pref("appearance", {}) or {}).get("rows_per_page", 30))
    except Exception:  # noqa: BLE001
        return 30


@network_bp.route("/")
@module_required(MODULE_SLUG)
def overview():
    racks = Rack.query.filter(Rack.is_active.is_(True)).order_by(Rack.code).all()
    panels = (
        PatchPanel.query.filter(PatchPanel.is_active.is_(True))
        .order_by(PatchPanel.code)
        .all()
    )
    counts = _status_counts_by_panel()

    # Totais gerais por status.
    totals = {s.value: 0 for s in PortStatus}
    for pc in counts.values():
        for k, v in pc.items():
            totals[k] = totals.get(k, 0) + v
    total_points = sum(totals.values())

    # Agrupa painéis por rack.
    panels_by_rack = {}
    for p in panels:
        panels_by_rack.setdefault(p.rack_id, []).append(p)

    return render_template(
        "infra/overview.html",
        racks=racks,
        panels_by_rack=panels_by_rack,
        counts=counts,
        totals=totals,
        total_points=total_points,
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@network_bp.route("/paineis/<int:panel_id>")
@module_required(MODULE_SLUG)
def panel(panel_id):
    panel = db.session.get(PatchPanel, panel_id)
    if panel is None:
        abort(404)
    points = (
        NetworkPoint.query.filter(
            NetworkPoint.patch_panel_id == panel.id,
            NetworkPoint.is_active.is_(True),
        )
        .order_by(NetworkPoint.number)
        .all()
    )
    counts = {}
    for p in points:
        counts[p.status.value] = counts.get(p.status.value, 0) + 1
    return render_template(
        "infra/panel.html",
        panel=panel,
        points=points,
        counts=counts,
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@network_bp.route("/pontos")
@module_required(MODULE_SLUG)
def points():
    query = NetworkPoint.query.filter(NetworkPoint.is_active.is_(True))

    rack_id = request.args.get("rack", type=int)
    panel_id = request.args.get("panel", type=int)
    status = request.args.get("status") or ""
    search = (request.args.get("q") or "").strip()

    if panel_id:
        query = query.filter(NetworkPoint.patch_panel_id == panel_id)
    elif rack_id:
        panel_ids = [p.id for p in PatchPanel.query.filter_by(rack_id=rack_id).all()]
        query = query.filter(NetworkPoint.patch_panel_id.in_(panel_ids or [-1]))
    if status:
        try:
            query = query.filter(NetworkPoint.status == PortStatus[status])
        except KeyError:
            pass
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                NetworkPoint.label.ilike(like),
                NetworkPoint.endpoint.ilike(like),
                db.cast(NetworkPoint.number, db.String).ilike(like),
            )
        )

    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(NetworkPoint.label).paginate(
        page=page, per_page=_rows_per_page(), error_out=False
    )
    return render_template(
        "infra/points.html",
        points=pagination.items,
        pagination=pagination,
        racks=Rack.query.order_by(Rack.code).all(),
        panels=PatchPanel.query.order_by(PatchPanel.code).all(),
        filters={"rack": rack_id, "panel": panel_id, "status": status, "q": search},
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@network_bp.route("/pontos/<int:point_id>/edit", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def edit_point(point_id):
    point = db.session.get(NetworkPoint, point_id)
    if point is None:
        abort(404)

    if request.method == "POST":
        try:
            point.status = PortStatus[request.form.get("status")]
        except (KeyError, TypeError):
            point.status = PortStatus.FREE
        point.endpoint = (request.form.get("endpoint") or "").strip() or None
        area_id = request.form.get("area_id", type=int)
        point.area_id = area_id or None
        point.notes = (request.form.get("notes") or "").strip() or None
        db.session.commit()
        flash("Ponto atualizado.", "success")
        return redirect(url_for("network.panel", panel_id=point.patch_panel_id))

    return render_template(
        "infra/point_form.html",
        point=point,
        areas=NetworkArea.query.filter(NetworkArea.is_active.is_(True))
        .order_by(NetworkArea.name)
        .all(),
    )


# ---------------------------------------------------------------------------
# Ambientes / Salas (organização física do escritório)
# ---------------------------------------------------------------------------
@network_bp.route("/ambientes")
@module_required(MODULE_SLUG)
def areas():
    areas = (
        NetworkArea.query.filter(NetworkArea.is_active.is_(True))
        .order_by(NetworkArea.name)
        .all()
    )
    # Contagens por ambiente (pontos e equipamentos).
    pt_counts = dict(
        db.session.query(NetworkPoint.area_id, func.count())
        .filter(NetworkPoint.is_active.is_(True), NetworkPoint.area_id.isnot(None))
        .group_by(NetworkPoint.area_id)
        .all()
    )
    eq_counts = dict(
        db.session.query(NetworkEquipment.area_id, func.coalesce(func.sum(NetworkEquipment.quantity), 0))
        .filter(NetworkEquipment.is_active.is_(True))
        .group_by(NetworkEquipment.area_id)
        .all()
    )
    return render_template(
        "infra/areas.html",
        areas=areas,
        pt_counts=pt_counts,
        eq_counts=eq_counts,
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@network_bp.route("/ambientes/new", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def new_area():
    area = NetworkArea()
    if request.method == "POST":
        error = _apply_area(area, request.form)
        if error is None:
            db.session.add(area)
            db.session.commit()
            flash("Ambiente criado.", "success")
            return redirect(url_for("network.area_detail", area_id=area.id))
        flash(error, "danger")
    return render_template("infra/area_form.html", area=area, is_new=True,
                           kinds=AREA_KINDS, all_sectors=_all_sectors())


@network_bp.route("/ambientes/<int:area_id>/edit", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def edit_area(area_id):
    area = db.session.get(NetworkArea, area_id)
    if area is None:
        abort(404)
    if request.method == "POST":
        error = _apply_area(area, request.form)
        if error is None:
            db.session.commit()
            flash("Ambiente atualizado.", "success")
            return redirect(url_for("network.area_detail", area_id=area.id))
        flash(error, "danger")
    return render_template("infra/area_form.html", area=area, is_new=False,
                           kinds=AREA_KINDS, all_sectors=_all_sectors())


@network_bp.route("/ambientes/<int:area_id>")
@module_required(MODULE_SLUG)
def area_detail(area_id):
    area = db.session.get(NetworkArea, area_id)
    if area is None:
        abort(404)
    equipment = (
        NetworkEquipment.query.filter(
            NetworkEquipment.area_id == area.id,
            NetworkEquipment.is_active.is_(True),
        )
        .order_by(NetworkEquipment.name)
        .all()
    )
    points = (
        NetworkPoint.query.filter(
            NetworkPoint.area_id == area.id, NetworkPoint.is_active.is_(True)
        )
        .order_by(NetworkPoint.label)
        .all()
    )
    racks = (
        Rack.query.filter(Rack.area_id == area.id, Rack.is_active.is_(True))
        .order_by(Rack.code)
        .all()
    )
    desks = (
        NetworkDesk.query.filter(
            NetworkDesk.area_id == area.id, NetworkDesk.is_active.is_(True)
        )
        .order_by(NetworkDesk.name)
        .all()
    )
    return render_template(
        "infra/area_detail.html",
        area=area,
        equipment=equipment,
        points=points,
        racks=racks,
        desks=desks,
        total_equip=sum(e.quantity for e in equipment),
        equip_kinds=EQUIP_KINDS,
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@network_bp.route("/ambientes/<int:area_id>/delete", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def delete_area(area_id):
    area = db.session.get(NetworkArea, area_id)
    if area is None:
        abort(404)
    area.is_active = False
    db.session.commit()
    flash("Ambiente removido.", "info")
    return redirect(url_for("network.areas"))


@network_bp.route("/ambientes/<int:area_id>/equip/new", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def add_equipment(area_id):
    area = db.session.get(NetworkArea, area_id)
    if area is None:
        abort(404)
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Informe o nome do equipamento.", "danger")
    else:
        try:
            qty = max(1, int(request.form.get("quantity") or 1))
        except ValueError:
            qty = 1
        db.session.add(NetworkEquipment(
            area_id=area.id,
            name=name,
            kind=(request.form.get("kind") or "").strip() or None,
            quantity=qty,
            notes=(request.form.get("notes") or "").strip() or None,
        ))
        db.session.commit()
        flash("Equipamento adicionado.", "success")
    return redirect(url_for("network.area_detail", area_id=area.id))


@network_bp.route("/equip/<int:equip_id>/delete", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def delete_equipment(equip_id):
    eq = db.session.get(NetworkEquipment, equip_id)
    if eq is None:
        abort(404)
    area_id = eq.area_id
    db.session.delete(eq)
    db.session.commit()
    flash("Equipamento removido.", "info")
    return redirect(url_for("network.area_detail", area_id=area_id))


def _all_sectors():
    return (
        NetworkSector.query.filter(NetworkSector.is_active.is_(True))
        .order_by(NetworkSector.name)
        .all()
    )


def _sectors_from_form(form):
    ids = [int(x) for x in form.getlist("sectors") if x.isdigit()]
    if not ids:
        return []
    return NetworkSector.query.filter(NetworkSector.id.in_(ids)).all()


def _apply_area(area, form):
    name = (form.get("name") or "").strip()
    if not name:
        return "Informe o nome do ambiente."
    area.name = name
    area.kind = (form.get("kind") or "").strip() or None
    area.description = (form.get("description") or "").strip() or None
    area.notes = (form.get("notes") or "").strip() or None
    area.sectors = _sectors_from_form(form)
    return None


# ---------------------------------------------------------------------------
# Racks e Patch Panels (dentro de um ambiente)
# ---------------------------------------------------------------------------
def _areas_options():
    return (
        NetworkArea.query.filter(NetworkArea.is_active.is_(True))
        .order_by(NetworkArea.name)
        .all()
    )


@network_bp.route("/racks/new", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def new_rack():
    rack = Rack()
    rack.area_id = request.args.get("area", type=int)
    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        if not code:
            flash("Informe o código do rack (ex.: R04).", "danger")
        elif Rack.query.filter_by(code=code).first():
            flash("Já existe um rack com esse código.", "danger")
        else:
            rack.code = code
            rack.name = (request.form.get("name") or "").strip() or None
            rack.area_id = request.form.get("area_id", type=int) or None
            rack.notes = (request.form.get("notes") or "").strip() or None
            db.session.add(rack)
            db.session.commit()
            flash("Rack criado.", "success")
            return redirect(url_for("network.rack_detail", rack_id=rack.id))
    return render_template("infra/rack_form.html", rack=rack, is_new=True, areas=_areas_options())


@network_bp.route("/racks/<int:rack_id>/edit", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def edit_rack(rack_id):
    rack = db.session.get(Rack, rack_id)
    if rack is None:
        abort(404)
    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        other = Rack.query.filter_by(code=code).first()
        if not code:
            flash("Informe o código do rack.", "danger")
        elif other and other.id != rack.id:
            flash("Já existe um rack com esse código.", "danger")
        else:
            rack.code = code
            rack.name = (request.form.get("name") or "").strip() or None
            rack.area_id = request.form.get("area_id", type=int) or None
            rack.notes = (request.form.get("notes") or "").strip() or None
            db.session.commit()
            flash("Rack atualizado.", "success")
            return redirect(url_for("network.rack_detail", rack_id=rack.id))
    return render_template("infra/rack_form.html", rack=rack, is_new=False, areas=_areas_options())


@network_bp.route("/racks/<int:rack_id>")
@module_required(MODULE_SLUG)
def rack_detail(rack_id):
    rack = db.session.get(Rack, rack_id)
    if rack is None:
        abort(404)
    panels = (
        PatchPanel.query.filter(
            PatchPanel.rack_id == rack.id, PatchPanel.is_active.is_(True)
        )
        .order_by(PatchPanel.code)
        .all()
    )
    counts = _status_counts_by_panel()
    return render_template(
        "infra/rack_detail.html",
        rack=rack, panels=panels, counts=counts,
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@network_bp.route("/racks/<int:rack_id>/delete", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def delete_rack(rack_id):
    rack = db.session.get(Rack, rack_id)
    if rack is None:
        abort(404)
    rack.is_active = False
    db.session.commit()
    flash("Rack removido.", "info")
    return redirect(url_for("network.overview"))


@network_bp.route("/racks/<int:rack_id>/paineis/new", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def new_panel(rack_id):
    rack = db.session.get(Rack, rack_id)
    if rack is None:
        abort(404)
    code = (request.form.get("code") or "").strip().upper()
    try:
        num_ports = max(0, int(request.form.get("num_ports") or 0))
    except ValueError:
        num_ports = 0

    if not code:
        flash("Informe o código do painel (ex.: PPA).", "danger")
    elif PatchPanel.query.filter_by(rack_id=rack.id, code=code).first():
        flash("Já existe um painel com esse código neste rack.", "danger")
    else:
        panel = PatchPanel(code=code, rack_id=rack.id)
        db.session.add(panel)
        db.session.flush()
        for i in range(1, num_ports + 1):
            db.session.add(NetworkPoint(
                patch_panel_id=panel.id,
                number=i,
                label=f"{rack.code} {code} {i}",
                status=PortStatus.FREE,
            ))
        db.session.commit()
        flash(f"Painel {code} criado com {num_ports} porta(s).", "success")
    return redirect(url_for("network.rack_detail", rack_id=rack.id))


@network_bp.route("/paineis/<int:panel_id>/delete", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def delete_panel(panel_id):
    panel = db.session.get(PatchPanel, panel_id)
    if panel is None:
        abort(404)
    rack_id = panel.rack_id
    panel.is_active = False
    db.session.commit()
    flash("Painel removido.", "info")
    return redirect(url_for("network.rack_detail", rack_id=rack_id))


# ---------------------------------------------------------------------------
# Setores (etiquetas N:N)
# ---------------------------------------------------------------------------
@network_bp.route("/setores", methods=["GET"])
@module_required(MODULE_SLUG)
def sectors():
    return render_template(
        "infra/sectors.html",
        sectors=NetworkSector.query.filter(NetworkSector.is_active.is_(True))
        .order_by(NetworkSector.name).all(),
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@network_bp.route("/setores/new", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def new_sector():
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Informe o nome do setor.", "danger")
    elif NetworkSector.query.filter_by(name=name).first():
        flash("Já existe um setor com esse nome.", "danger")
    else:
        db.session.add(NetworkSector(name=name))
        db.session.commit()
        flash("Setor criado.", "success")
    return redirect(url_for("network.sectors"))


@network_bp.route("/setores/<int:sector_id>/delete", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def delete_sector(sector_id):
    s = db.session.get(NetworkSector, sector_id)
    if s is None:
        abort(404)
    s.is_active = False
    db.session.commit()
    flash("Setor removido.", "info")
    return redirect(url_for("network.sectors"))


# ---------------------------------------------------------------------------
# Mesas e posições (layout de ocupação)
# ---------------------------------------------------------------------------
def _machine_map(seats):
    """employee_id -> Asset (máquina principal: prioriza notebook/desktop)."""
    emp_ids = [s.employee_id for s in seats if s.employee_id]
    if not emp_ids:
        return {}
    assets = Asset.query.filter(
        Asset.assigned_to_id.in_(emp_ids), Asset.is_active.is_(True)
    ).all()
    rank = {"notebook": 0, "desktop": 1}
    best = {}
    for a in assets:
        slug = a.asset_type.slug if a.asset_type else ""
        r = rank.get(slug, 9)
        cur = best.get(a.assigned_to_id)
        if cur is None or r < cur[0]:
            best[a.assigned_to_id] = (r, a)
    return {emp: pair[1] for emp, pair in best.items()}


def _apply_desk(desk, form):
    name = (form.get("name") or "").strip()
    if not name:
        return "Informe o nome da mesa."
    desk.name = name
    desk.notes = (form.get("notes") or "").strip() or None
    desk.sectors = _sectors_from_form(form)
    return None


@network_bp.route("/ambientes/<int:area_id>/mesas/new", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def new_desk(area_id):
    area = db.session.get(NetworkArea, area_id)
    if area is None:
        abort(404)
    desk = NetworkDesk(area_id=area.id)
    if request.method == "POST":
        error = _apply_desk(desk, request.form)
        if error is None:
            desk.area_id = area.id
            db.session.add(desk)
            db.session.commit()
            flash("Mesa criada.", "success")
            return redirect(url_for("network.desk_detail", desk_id=desk.id))
        flash(error, "danger")
    return render_template("infra/desk_form.html", desk=desk, area=area,
                           is_new=True, all_sectors=_all_sectors())


@network_bp.route("/mesas/<int:desk_id>/edit", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def edit_desk(desk_id):
    desk = db.session.get(NetworkDesk, desk_id)
    if desk is None:
        abort(404)
    if request.method == "POST":
        error = _apply_desk(desk, request.form)
        if error is None:
            db.session.commit()
            flash("Mesa atualizada.", "success")
            return redirect(url_for("network.desk_detail", desk_id=desk.id))
        flash(error, "danger")
    return render_template("infra/desk_form.html", desk=desk, area=desk.area,
                           is_new=False, all_sectors=_all_sectors())


@network_bp.route("/mesas/<int:desk_id>")
@module_required(MODULE_SLUG)
def desk_detail(desk_id):
    desk = db.session.get(NetworkDesk, desk_id)
    if desk is None:
        abort(404)
    seats = [s for s in desk.seats if s.is_active]
    machines = _machine_map(seats)
    return render_template(
        "infra/desk_detail.html",
        desk=desk,
        seats=seats,
        machines=machines,
        employees=Employee.query.filter_by(is_active=True).order_by(Employee.name).all(),
        can_edit=can_manage_slug(MODULE_SLUG),
    )


@network_bp.route("/mesas/<int:desk_id>/delete", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def delete_desk(desk_id):
    desk = db.session.get(NetworkDesk, desk_id)
    if desk is None:
        abort(404)
    area_id = desk.area_id
    desk.is_active = False
    db.session.commit()
    flash("Mesa removida.", "info")
    return redirect(url_for("network.area_detail", area_id=area_id))


@network_bp.route("/mesas/<int:desk_id>/posicoes/new", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def add_seat(desk_id):
    desk = db.session.get(NetworkDesk, desk_id)
    if desk is None:
        abort(404)
    next_pos = 1 + max([s.position for s in desk.seats] or [0])
    emp_id = request.form.get("employee_id", type=int)
    db.session.add(NetworkSeat(
        desk_id=desk.id,
        position=next_pos,
        employee_id=emp_id or None,
        label=(request.form.get("label") or "").strip() or None,
    ))
    db.session.commit()
    flash("Posição adicionada.", "success")
    return redirect(url_for("network.desk_detail", desk_id=desk.id))


@network_bp.route("/posicoes/<int:seat_id>/edit", methods=["GET", "POST"])
@module_required(MODULE_SLUG, manage=True)
def edit_seat(seat_id):
    seat = db.session.get(NetworkSeat, seat_id)
    if seat is None:
        abort(404)
    if request.method == "POST":
        seat.employee_id = request.form.get("employee_id", type=int) or None
        seat.label = (request.form.get("label") or "").strip() or None
        seat.notes = (request.form.get("notes") or "").strip() or None
        db.session.commit()
        flash("Posição atualizada.", "success")
        return redirect(url_for("network.desk_detail", desk_id=seat.desk_id))
    machine = _machine_map([seat]).get(seat.employee_id)
    return render_template(
        "infra/seat_form.html",
        seat=seat,
        machine=machine,
        employees=Employee.query.filter_by(is_active=True).order_by(Employee.name).all(),
    )


@network_bp.route("/posicoes/<int:seat_id>/delete", methods=["POST"])
@module_required(MODULE_SLUG, manage=True)
def delete_seat(seat_id):
    seat = db.session.get(NetworkSeat, seat_id)
    if seat is None:
        abort(404)
    desk_id = seat.desk_id
    db.session.delete(seat)
    db.session.commit()
    flash("Posição removida.", "info")
    return redirect(url_for("network.desk_detail", desk_id=desk_id))
