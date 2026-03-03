from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models.portal_user import PortalUser
from app.models.portal_session import PortalSession
from app.models.wifi_group import WifiGroup
from app.services.portal_sync import (
    sync_mac_deauthorize, sync_mac_update_group, cleanup_expired_sessions,
)

portal_users_bp = Blueprint(
    "portal_users", __name__, url_prefix="/portal-usuarios"
)


@portal_users_bp.before_request
@login_required
def require_login():
    pass


@portal_users_bp.route("/")
def list_portal_users():
    q = request.args.get("q", "").strip()
    query = PortalUser.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                PortalUser.email.ilike(like),
                PortalUser.full_name.ilike(like),
            )
        )
    users = query.order_by(PortalUser.created_at.desc()).all()
    groups = WifiGroup.query.order_by(WifiGroup.group_name).all()
    return render_template(
        "portal_users/list.html", users=users, groups=groups, q=q,
    )


@portal_users_bp.route("/<int:user_id>/cambiar-grupo", methods=["POST"])
def change_group(user_id):
    user = db.get_or_404(PortalUser, user_id)
    new_group = request.form.get("group_name")
    if not new_group:
        flash("Grupo inválido.", "danger")
        return redirect(url_for("portal_users.list_portal_users"))
    old_group = user.group_name
    user.group_name = new_group
    # Actualizar MACs activas de este usuario
    active_sessions = user.sessions.all()
    for sess in active_sessions:
        sync_mac_update_group(sess.mac_address, new_group)
    db.session.commit()
    flash(
        f"Grupo de '{user.email}' cambiado de '{old_group}' a '{new_group}'.",
        "success",
    )
    return redirect(url_for("portal_users.list_portal_users"))


@portal_users_bp.route("/<int:user_id>/toggle", methods=["POST"])
def toggle_user(user_id):
    user = db.get_or_404(PortalUser, user_id)
    user.is_enabled = not user.is_enabled
    if not user.is_enabled:
        # Desautorizar todas las MACs activas
        for sess in user.sessions.all():
            sync_mac_deauthorize(sess.mac_address)
            db.session.delete(sess)
    db.session.commit()
    state = "habilitado" if user.is_enabled else "deshabilitado"
    flash(f"Usuario '{user.email}' {state}.", "success")
    return redirect(url_for("portal_users.list_portal_users"))


@portal_users_bp.route("/<int:user_id>/eliminar", methods=["POST"])
def delete_user(user_id):
    user = db.get_or_404(PortalUser, user_id)
    # Desautorizar todas las MACs
    for sess in user.sessions.all():
        sync_mac_deauthorize(sess.mac_address)
    db.session.delete(user)
    db.session.commit()
    flash(f"Usuario portal '{user.email}' eliminado.", "success")
    return redirect(url_for("portal_users.list_portal_users"))


@portal_users_bp.route("/cleanup", methods=["POST"])
def run_cleanup():
    removed = cleanup_expired_sessions()
    flash(f"Limpieza completada: {removed} MAC(s) desautorizadas.", "success")
    return redirect(url_for("portal_users.list_portal_users"))
