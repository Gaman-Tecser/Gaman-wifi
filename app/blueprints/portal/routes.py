import logging
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    session, request, current_app,
)

logger = logging.getLogger(__name__)
from app.extensions import db, oauth
from app.models.allowed_domain import AllowedDomain
from app.models.portal_user import PortalUser
from app.models.portal_session import PortalSession
from app.services.portal_sync import normalize_mac, sync_mac_authorize

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


@portal_bp.route("/")
def landing():
    mac = request.args.get("mac", "")
    if mac:
        session["portal_mac"] = mac
    logger.info(f"[PORTAL LANDING] mac param={mac}, session keys={list(session.keys())}, full_url={request.url}, headers={dict(request.headers)}")
    return render_template("portal/landing.html", mac=mac)


@portal_bp.route("/login")
def login():
    # Capture MAC from query param (survives captive portal browser switch)
    mac = request.args.get("mac", "")
    if mac:
        session["portal_mac"] = mac
    logger.info(f"[PORTAL LOGIN] mac param={mac}, session portal_mac={session.get('portal_mac')}, session keys={list(session.keys())}")
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

    # Verificar dominio permitido
    allowed = AllowedDomain.query.filter_by(
        domain=domain, is_active=True
    ).first()
    if not allowed:
        return render_template(
            "portal/error.html",
            error=f"El dominio '{domain}' no está autorizado para acceder a esta red.",
        )

    # Obtener MAC de la sesión
    logger.info(f"[PORTAL CALLBACK] session keys={list(session.keys())}, portal_mac={session.get('portal_mac')}")
    mac_raw = session.pop("portal_mac", "")
    if not mac_raw:
        return render_template(
            "portal/error.html",
            error="No se detectó la dirección MAC del dispositivo. Conéctese al SSID nuevamente.",
        )

    try:
        mac = normalize_mac(mac_raw)
    except ValueError:
        return render_template(
            "portal/error.html",
            error=f"Dirección MAC inválida: {mac_raw}",
        )

    # Crear o actualizar portal_user
    portal_user = PortalUser.query.filter_by(email=email).first()
    if not portal_user:
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

    portal_user.last_auth_at = datetime.now(timezone.utc)

    # Registrar MAC en FreeRADIUS
    sync_mac_authorize(mac, portal_user.group_name)

    # Crear sesión portal
    hours = current_app.config["PORTAL_SESSION_HOURS"]
    now = datetime.now(timezone.utc)
    portal_session = PortalSession(
        portal_user_id=portal_user.id,
        mac_address=mac,
        authorized_at=now,
        expires_at=now + timedelta(hours=hours),
    )
    db.session.add(portal_session)
    db.session.commit()

    return render_template(
        "portal/success.html",
        name=name,
        email=email,
        picture=picture,
        mac=mac,
        hours=hours,
    )
