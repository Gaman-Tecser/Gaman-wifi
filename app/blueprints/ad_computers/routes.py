import logging

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from app.extensions import db
from app.models.ad_computer import AdComputer
from app.models.wifi_group import WifiGroup
from app.models.radius import Radusergroup

logger = logging.getLogger(__name__)

ad_computers_bp = Blueprint(
    "ad_computers", __name__, url_prefix="/equipos-ad"
)


@ad_computers_bp.before_request
@login_required
def require_login():
    pass


@ad_computers_bp.route("/")
def list_computers():
    q = request.args.get("q", "").strip()
    query = AdComputer.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                AdComputer.name.ilike(like),
                AdComputer.sam_account_name.ilike(like),
                AdComputer.ou.ilike(like),
                AdComputer.description.ilike(like),
            )
        )
    computers = query.order_by(AdComputer.name).all()
    groups = WifiGroup.query.order_by(WifiGroup.group_name).all()

    ad_configured = bool(current_app.config.get("AD_LDAP_HOST"))

    return render_template(
        "ad_computers/list.html",
        computers=computers, groups=groups, q=q,
        ad_configured=ad_configured,
    )


@ad_computers_bp.route("/importar", methods=["POST"])
def import_from_ad():
    host = current_app.config.get("AD_LDAP_HOST")
    base_dn = current_app.config.get("AD_BASE_DN")
    bind_user = current_app.config.get("AD_BIND_USER")
    bind_password = current_app.config.get("AD_BIND_PASSWORD")

    if not host or not bind_user:
        flash("LDAP no configurado. Configurá AD_LDAP_HOST y AD_BIND_USER.", "danger")
        return redirect(url_for("ad_computers.list_computers"))

    try:
        from app.services.ad_sync import fetch_ad_computers
        ad_computers = fetch_ad_computers(host, base_dn, bind_user, bind_password)
    except Exception as e:
        logger.error(f"[AD IMPORT] error: {e}")
        flash(f"Error al conectar con AD: {e}", "danger")
        return redirect(url_for("ad_computers.list_computers"))

    default_group = WifiGroup.query.order_by(WifiGroup.id).first()
    if not default_group:
        flash("No hay grupos creados. Creá un grupo primero.", "danger")
        return redirect(url_for("ad_computers.list_computers"))

    imported = 0
    updated = 0
    for comp in ad_computers:
        sam = comp["sam_account_name"]
        existing = AdComputer.query.filter_by(sam_account_name=sam).first()
        if existing:
            existing.name = comp["name"]
            existing.dns_hostname = comp["dns_hostname"]
            existing.os = comp["os"]
            existing.ou = comp["ou"]
            existing.description = comp["description"]
            updated += 1
        else:
            db.session.add(AdComputer(
                name=comp["name"],
                sam_account_name=sam,
                dns_hostname=comp["dns_hostname"],
                os=comp["os"],
                ou=comp["ou"],
                description=comp["description"],
                group_name=default_group.group_name,
                is_enabled=True,
            ))
            imported += 1

    db.session.commit()
    flash(f"AD: {imported} equipos importados, {updated} actualizados.", "success")
    return redirect(url_for("ad_computers.list_computers"))


@ad_computers_bp.route("/<int:comp_id>/cambiar-grupo", methods=["POST"])
def change_group(comp_id):
    comp = db.get_or_404(AdComputer, comp_id)
    new_group = request.form.get("group_name")
    if not new_group:
        flash("Grupo inválido.", "danger")
        return redirect(url_for("ad_computers.list_computers"))

    old_group = comp.group_name
    comp.group_name = new_group

    # Sync to radusergroup
    radius_user = comp.radius_username
    existing = Radusergroup.query.filter_by(username=radius_user).first()
    if not existing:
        db.session.add(Radusergroup(
            username=radius_user, groupname=new_group, priority=1,
        ))
    else:
        existing.groupname = new_group

    db.session.commit()
    flash(f"Grupo de '{comp.name}' cambiado de '{old_group}' a '{new_group}'.", "success")
    return redirect(url_for("ad_computers.list_computers"))


@ad_computers_bp.route("/<int:comp_id>/toggle", methods=["POST"])
def toggle_computer(comp_id):
    comp = db.get_or_404(AdComputer, comp_id)
    comp.is_enabled = not comp.is_enabled

    radius_user = comp.radius_username
    if not comp.is_enabled:
        Radusergroup.query.filter_by(username=radius_user).delete()
    else:
        existing = Radusergroup.query.filter_by(username=radius_user).first()
        if not existing:
            db.session.add(Radusergroup(
                username=radius_user, groupname=comp.group_name, priority=1,
            ))

    db.session.commit()
    state = "habilitado" if comp.is_enabled else "deshabilitado"
    flash(f"Equipo '{comp.name}' {state}.", "success")
    return redirect(url_for("ad_computers.list_computers"))


@ad_computers_bp.route("/<int:comp_id>/eliminar", methods=["POST"])
def delete_computer(comp_id):
    comp = db.get_or_404(AdComputer, comp_id)
    Radusergroup.query.filter_by(username=comp.radius_username).delete()
    db.session.delete(comp)
    db.session.commit()
    flash(f"Equipo '{comp.name}' eliminado.", "success")
    return redirect(url_for("ad_computers.list_computers"))


@ad_computers_bp.route("/sync-todos", methods=["POST"])
def sync_all():
    """Sincroniza todos los equipos habilitados a radusergroup."""
    computers = AdComputer.query.filter_by(is_enabled=True).all()
    count = 0
    for comp in computers:
        radius_user = comp.radius_username
        existing = Radusergroup.query.filter_by(username=radius_user).first()
        if not existing:
            db.session.add(Radusergroup(
                username=radius_user, groupname=comp.group_name, priority=1,
            ))
            count += 1
        elif existing.groupname != comp.group_name:
            existing.groupname = comp.group_name
            count += 1

    db.session.commit()
    flash(f"{count} equipos sincronizados a RADIUS.", "success")
    return redirect(url_for("ad_computers.list_computers"))
