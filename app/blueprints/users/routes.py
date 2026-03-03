from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models.wifi_user import WifiUser
from app.models.wifi_group import WifiGroup
from app.services.radius_sync import (
    sync_user_create, sync_user_delete, sync_user_disable, sync_user_enable,
    sync_user_update_password, sync_user_update_group,
)
from app.blueprints.users.forms import UserCreateForm, UserEditForm

users_bp = Blueprint("users", __name__, url_prefix="/usuarios")


@users_bp.before_request
@login_required
def require_login():
    pass


def _group_choices():
    return [
        (g.group_name, f"{g.group_name} (VLAN {g.vlan_id})")
        for g in WifiGroup.query.order_by(WifiGroup.group_name).all()
    ]


@users_bp.route("/")
def list_users():
    q = request.args.get("q", "").strip()
    query = WifiUser.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                WifiUser.username.ilike(like),
                WifiUser.full_name.ilike(like),
                WifiUser.email.ilike(like),
            )
        )
    users = query.order_by(WifiUser.username).all()
    return render_template("users/list.html", users=users, q=q)


@users_bp.route("/nuevo", methods=["GET", "POST"])
def create_user():
    form = UserCreateForm()
    form.group_name.choices = _group_choices()
    if form.validate_on_submit():
        if WifiUser.query.filter_by(username=form.username.data).first():
            flash("Ya existe un usuario con ese nombre.", "danger")
            return render_template("users/form.html", form=form, title="Nuevo Usuario")
        user = WifiUser(
            username=form.username.data,
            full_name=form.full_name.data,
            email=form.email.data or "",
            group_name=form.group_name.data,
            notes=form.notes.data or "",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        sync_user_create(user.username, form.password.data, user.group_name)
        db.session.commit()
        flash(f"Usuario '{user.username}' creado.", "success")
        return redirect(url_for("users.list_users"))
    return render_template("users/form.html", form=form, title="Nuevo Usuario")


@users_bp.route("/<int:user_id>/editar", methods=["GET", "POST"])
def edit_user(user_id):
    user = db.get_or_404(WifiUser, user_id)
    form = UserEditForm(obj=user)
    form.group_name.choices = _group_choices()
    if form.validate_on_submit():
        old_group = user.group_name
        user.full_name = form.full_name.data
        user.email = form.email.data or ""
        user.notes = form.notes.data or ""
        if form.group_name.data != old_group:
            user.group_name = form.group_name.data
            sync_user_update_group(user.username, old_group, form.group_name.data)
        if form.password.data:
            user.set_password(form.password.data)
            sync_user_update_password(user.username, form.password.data)
        db.session.commit()
        flash(f"Usuario '{user.username}' actualizado.", "success")
        return redirect(url_for("users.list_users"))
    return render_template("users/form.html", form=form, title="Editar Usuario", editing=True, user=user)


@users_bp.route("/<int:user_id>/toggle", methods=["POST"])
def toggle_user(user_id):
    user = db.get_or_404(WifiUser, user_id)
    if user.is_enabled:
        user.is_enabled = False
        sync_user_disable(user.username)
        flash(f"Usuario '{user.username}' deshabilitado.", "warning")
    else:
        user.is_enabled = True
        sync_user_enable(user.username)
        flash(f"Usuario '{user.username}' habilitado.", "success")
    db.session.commit()
    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:user_id>/eliminar", methods=["POST"])
def delete_user(user_id):
    user = db.get_or_404(WifiUser, user_id)
    sync_user_delete(user.username)
    db.session.delete(user)
    db.session.commit()
    flash(f"Usuario '{user.username}' eliminado.", "success")
    return redirect(url_for("users.list_users"))
