import logging
import secrets
import string
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, redirect, url_for,
    session, request, current_app,
)

logger = logging.getLogger(__name__)
from app.extensions import db, oauth
from app.models.allowed_domain import AllowedDomain
from app.models.portal_user import PortalUser
from app.services.portal_sync import sync_user_authorize

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@portal_bp.route("/")
def landing():
    logger.info(f"[PORTAL LANDING] full_url={request.url}")
    return render_template("portal/landing.html")


@portal_bp.route("/login")
def login():
    redirect_uri = url_for("portal.callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@portal_bp.route("/callback")
def callback():
    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        return render_template(
            "portal/error.html",
            error="No se pudo completar la autenticación con Google.",
        )

    userinfo = token.get("userinfo")
    if not userinfo:
        return render_template(
            "portal/error.html",
            error="No se pudo obtener información del usuario.",
        )

    email = userinfo.get("email", "")
    name = userinfo.get("name", email)
    picture = userinfo.get("picture", "")
    domain = email.split("@")[-1].lower() if "@" in email else ""

    allowed = AllowedDomain.query.filter_by(
        domain=domain, is_active=True
    ).first()
    if not allowed:
        return render_template(
            "portal/error.html",
            error=f"El dominio '{domain}' no está autorizado para acceder a esta red.",
        )

    portal_user = PortalUser.query.filter_by(email=email).first()
    is_new = portal_user is None

    if is_new:
        portal_user = PortalUser(
            email=email,
            full_name=name,
            picture_url=picture,
            domain=domain,
            group_name=allowed.default_group_name,
        )
        db.session.add(portal_user)
        db.session.flush()
    else:
        portal_user.full_name = name
        portal_user.picture_url = picture

    if not portal_user.is_enabled:
        return render_template(
            "portal/error.html",
            error="Tu cuenta ha sido deshabilitada por el administrador.",
        )

    # Generate password for new users or those without one
    if is_new or not portal_user.wifi_password_encrypted:
        wifi_password = _generate_password()
        portal_user.set_wifi_password(wifi_password)
    else:
        wifi_password = portal_user.get_wifi_password()

    portal_user.last_auth_at = datetime.now(timezone.utc)

    # Sync to RADIUS
    sync_user_authorize(email, wifi_password, portal_user.group_name)

    db.session.commit()

    session["portal_email"] = email
    ssid = current_app.config.get("WIFI_SSID_NAME", "Gaman-WiFi")

    return render_template(
        "portal/success.html",
        name=name,
        email=email,
        picture=picture,
        wifi_password=wifi_password,
        ssid=ssid,
        is_new=is_new,
    )


@portal_bp.route("/regenerar", methods=["POST"])
def regenerate():
    """Regenera la contraseña WiFi del usuario autenticado."""
    portal_email = session.get("portal_email")
    if not portal_email:
        return redirect(url_for("portal.landing"))

    portal_user = PortalUser.query.filter_by(email=portal_email).first()
    if not portal_user or not portal_user.is_enabled:
        return redirect(url_for("portal.landing"))

    wifi_password = _generate_password()
    portal_user.set_wifi_password(wifi_password)

    sync_user_authorize(portal_email, wifi_password, portal_user.group_name)
    db.session.commit()

    ssid = current_app.config.get("WIFI_SSID_NAME", "Gaman-WiFi")

    return render_template(
        "portal/success.html",
        name=portal_user.full_name,
        email=portal_email,
        picture=portal_user.picture_url,
        wifi_password=wifi_password,
        ssid=ssid,
        is_new=False,
        regenerated=True,
    )
