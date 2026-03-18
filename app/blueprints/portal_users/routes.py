from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models.portal_user import PortalUser
from app.models.wifi_group import WifiGroup
from app.services.portal_sync import (
    sync_user_deauthorize, sync_user_update_group, sync_user_update_password,
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
    sync_user_update_group(user.email, new_group)
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
        sync_user_deauthorize(user.email)
    else:
        # Re-authorize with existing password
        wifi_pass = user.get_wifi_password()
        if wifi_pass:
            from app.services.portal_sync import sync_user_authorize
            sync_user_authorize(user.email, wifi_pass, user.group_name)
    db.session.commit()
    state = "habilitado" if user.is_enabled else "deshabilitado"
    flash(f"Usuario '{user.email}' {state}.", "success")
    return redirect(url_for("portal_users.list_portal_users"))


@portal_users_bp.route("/<int:user_id>/eliminar", methods=["POST"])
def delete_user(user_id):
    user = db.get_or_404(PortalUser, user_id)
    sync_user_deauthorize(user.email)
    db.session.delete(user)
    db.session.commit()
    flash(f"Usuario portal '{user.email}' eliminado.", "success")
    return redirect(url_for("portal_users.list_portal_users"))


@portal_users_bp.route("/<int:user_id>/reset-password", methods=["POST"])
def reset_password(user_id):
    import secrets
    import string
    user = db.get_or_404(PortalUser, user_id)
    alphabet = string.ascii_letters + string.digits
    new_pass = "".join(secrets.choice(alphabet) for _ in range(12))
    user.set_wifi_password(new_pass)
    sync_user_update_password(user.email, new_pass)
    db.session.commit()
    flash(f"Contraseña WiFi de '{user.email}' reseteada.", "success")
    return redirect(url_for("portal_users.list_portal_users"))
