from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models.wifi_group import WifiGroup
from app.services.radius_sync import (
    sync_group_create, sync_group_update_vlan, sync_group_delete,
)
from app.blueprints.groups.forms import GroupForm

groups_bp = Blueprint("groups", __name__, url_prefix="/grupos")


@groups_bp.before_request
@login_required
def require_login():
    pass


@groups_bp.route("/")
def list_groups():
    groups = WifiGroup.query.order_by(WifiGroup.group_name).all()
    return render_template("groups/list.html", groups=groups)


@groups_bp.route("/nuevo", methods=["GET", "POST"])
def create_group():
    form = GroupForm()
    if form.validate_on_submit():
        if WifiGroup.query.filter_by(group_name=form.group_name.data).first():
            flash("Ya existe un grupo con ese nombre.", "danger")
            return render_template("groups/form.html", form=form, title="Nuevo Grupo")
        group = WifiGroup(
            group_name=form.group_name.data,
            description=form.description.data or "",
            vlan_id=form.vlan_id.data,
        )
        db.session.add(group)
        sync_group_create(group.group_name, group.vlan_id)
        db.session.commit()
        flash(f"Grupo '{group.group_name}' creado.", "success")
        return redirect(url_for("groups.list_groups"))
    return render_template("groups/form.html", form=form, title="Nuevo Grupo")


@groups_bp.route("/<int:group_id>/editar", methods=["GET", "POST"])
def edit_group(group_id):
    group = db.get_or_404(WifiGroup, group_id)
    form = GroupForm(obj=group)
    if form.validate_on_submit():
        old_vlan = group.vlan_id
        group.description = form.description.data or ""
        group.vlan_id = form.vlan_id.data
        if group.vlan_id != old_vlan:
            sync_group_update_vlan(group.group_name, group.vlan_id)
        db.session.commit()
        flash(f"Grupo '{group.group_name}' actualizado.", "success")
        return redirect(url_for("groups.list_groups"))
    return render_template("groups/form.html", form=form, title="Editar Grupo", editing=True)


@groups_bp.route("/<int:group_id>/eliminar", methods=["POST"])
def delete_group(group_id):
    group = db.get_or_404(WifiGroup, group_id)
    if group.users.count() > 0:
        flash("No se puede eliminar un grupo con usuarios asignados.", "danger")
        return redirect(url_for("groups.list_groups"))
    sync_group_delete(group.group_name)
    db.session.delete(group)
    db.session.commit()
    flash(f"Grupo '{group.group_name}' eliminado.", "success")
    return redirect(url_for("groups.list_groups"))
