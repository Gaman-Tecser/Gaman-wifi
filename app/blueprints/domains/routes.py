from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.allowed_domain import AllowedDomain
from app.models.wifi_group import WifiGroup
from app.blueprints.domains.forms import DomainForm

domains_bp = Blueprint("domains", __name__, url_prefix="/dominios")


@domains_bp.before_request
@login_required
def require_login():
    pass


def _populate_group_choices(form):
    groups = WifiGroup.query.order_by(WifiGroup.group_name).all()
    form.default_group_name.choices = [
        (g.group_name, f"{g.group_name} (VLAN {g.vlan_id})") for g in groups
    ]


@domains_bp.route("/")
def list_domains():
    domains = AllowedDomain.query.order_by(AllowedDomain.domain).all()
    return render_template("domains/list.html", domains=domains)


@domains_bp.route("/nuevo", methods=["GET", "POST"])
def create_domain():
    form = DomainForm()
    _populate_group_choices(form)
    if form.validate_on_submit():
        domain_val = form.domain.data.strip().lower()
        if AllowedDomain.query.filter_by(domain=domain_val).first():
            flash("Ya existe ese dominio.", "danger")
            return render_template("domains/form.html", form=form, title="Nuevo Dominio")
        dom = AllowedDomain(
            domain=domain_val,
            default_group_name=form.default_group_name.data,
            is_active=form.is_active.data,
        )
        db.session.add(dom)
        db.session.commit()
        flash(f"Dominio '{dom.domain}' agregado.", "success")
        return redirect(url_for("domains.list_domains"))
    return render_template("domains/form.html", form=form, title="Nuevo Dominio")


@domains_bp.route("/<int:domain_id>/editar", methods=["GET", "POST"])
def edit_domain(domain_id):
    dom = db.get_or_404(AllowedDomain, domain_id)
    form = DomainForm(obj=dom)
    _populate_group_choices(form)
    if form.validate_on_submit():
        dom.domain = form.domain.data.strip().lower()
        dom.default_group_name = form.default_group_name.data
        dom.is_active = form.is_active.data
        db.session.commit()
        flash(f"Dominio '{dom.domain}' actualizado.", "success")
        return redirect(url_for("domains.list_domains"))
    return render_template("domains/form.html", form=form, title="Editar Dominio", editing=True)


@domains_bp.route("/<int:domain_id>/eliminar", methods=["POST"])
def delete_domain(domain_id):
    dom = db.get_or_404(AllowedDomain, domain_id)
    db.session.delete(dom)
    db.session.commit()
    flash(f"Dominio '{dom.domain}' eliminado.", "success")
    return redirect(url_for("domains.list_domains"))
