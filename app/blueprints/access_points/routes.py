from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.access_point import GamanAccessPoint
from app.services.radius_sync import sync_ap_create, sync_ap_delete
from app.services.radius_restart import restart_freeradius
from app.blueprints.access_points.forms import APForm

ap_bp = Blueprint("access_points", __name__, url_prefix="/puntos-de-acceso")


@ap_bp.before_request
@login_required
def require_login():
    pass


@ap_bp.route("/")
def list_aps():
    aps = GamanAccessPoint.query.order_by(GamanAccessPoint.name).all()
    return render_template("access_points/list.html", aps=aps)


@ap_bp.route("/nuevo", methods=["GET", "POST"])
def create_ap():
    form = APForm()
    if form.validate_on_submit():
        if GamanAccessPoint.query.filter_by(ip_address=form.ip_address.data).first():
            flash("Ya existe un AP con esa IP.", "danger")
            return render_template("access_points/form.html", form=form, title="Nuevo Punto de Acceso")
        nas_id = sync_ap_create(
            form.ip_address.data, form.name.data, form.secret.data
        )
        ap = GamanAccessPoint(
            nas_id=nas_id,
            ip_address=form.ip_address.data,
            name=form.name.data,
            secret=form.secret.data,
            model=form.model.data or "",
            location=form.location.data or "",
        )
        db.session.add(ap)
        db.session.commit()
        ok, msg = restart_freeradius()
        if ok:
            flash(f"AP '{ap.name}' creado y FreeRADIUS reiniciado.", "success")
        else:
            flash(f"AP '{ap.name}' creado. Advertencia al reiniciar: {msg}", "warning")
        return redirect(url_for("access_points.list_aps"))
    return render_template("access_points/form.html", form=form, title="Nuevo Punto de Acceso")


@ap_bp.route("/<int:ap_id>/editar", methods=["GET", "POST"])
def edit_ap(ap_id):
    ap = db.get_or_404(GamanAccessPoint, ap_id)
    form = APForm(obj=ap)
    if form.validate_on_submit():
        ap.name = form.name.data
        ap.ip_address = form.ip_address.data
        ap.secret = form.secret.data
        ap.model = form.model.data or ""
        ap.location = form.location.data or ""
        # Actualizar NAS también
        if ap.nas_id:
            from app.models.radius import Nas
            nas = db.session.get(Nas, ap.nas_id)
            if nas:
                nas.nasname = ap.ip_address
                nas.shortname = ap.name
                nas.secret = ap.secret
        db.session.commit()
        ok, msg = restart_freeradius()
        if ok:
            flash(f"AP '{ap.name}' actualizado y FreeRADIUS reiniciado.", "success")
        else:
            flash(f"AP '{ap.name}' actualizado. Advertencia al reiniciar: {msg}", "warning")
        return redirect(url_for("access_points.list_aps"))
    return render_template("access_points/form.html", form=form, title="Editar Punto de Acceso", editing=True)


@ap_bp.route("/<int:ap_id>/eliminar", methods=["POST"])
def delete_ap(ap_id):
    ap = db.get_or_404(GamanAccessPoint, ap_id)
    sync_ap_delete(ap.nas_id)
    db.session.delete(ap)
    db.session.commit()
    ok, msg = restart_freeradius()
    if ok:
        flash(f"AP '{ap.name}' eliminado y FreeRADIUS reiniciado.", "success")
    else:
        flash(f"AP '{ap.name}' eliminado. Advertencia al reiniciar: {msg}", "warning")
    return redirect(url_for("access_points.list_aps"))


@ap_bp.route("/restart-radius", methods=["POST"])
def restart_radius():
    ok, msg = restart_freeradius()
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("access_points.list_aps"))
