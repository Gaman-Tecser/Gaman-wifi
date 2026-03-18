import logging
from datetime import datetime, timezone
from urllib.parse import urlencode

from flask import (
    Blueprint, render_template, redirect, url_for,
    session, request,
)

logger = logging.getLogger(__name__)
from app.extensions import db, oauth
from app.models.allowed_domain import AllowedDomain
from app.models.portal_user import PortalUser

portal2_bp = Blueprint("portal2", __name__, url_prefix="/portal2")


@portal2_bp.route("/")
def landing():
    # Save all Aruba params in session
    aruba_params = {}
    for key in ("cmd", "mac", "network", "ip", "apmac", "site", "post", "url"):
        val = request.args.get(key, "")
        if val:
            aruba_params[key] = val

    if aruba_params:
        session["aruba_params"] = aruba_params

    logger.info(f"[PORTAL2 LANDING] aruba_params={aruba_params}, full_url={request.url}")
    return render_template("portal2/landing.html", aruba_params=aruba_params)


@portal2_bp.route("/login")
def login():
    redirect_uri = url_for("portal2.callback", _external=True)
    logger.info(f"[PORTAL2 LOGIN] redirect_uri={redirect_uri}, session_keys={list(session.keys())}")
    resp = oauth.google.authorize_redirect(redirect_uri)
    logger.info(f"[PORTAL2 LOGIN] after redirect, session_keys={list(session.keys())}, session_state={session.get('_state_google_')}")
    return resp


@portal2_bp.route("/callback")
def callback():
    logger.info(f"[PORTAL2 CALLBACK] session_keys={list(session.keys())}, session_state={session.get('_state_google_')}, request_state={request.args.get('state')}")
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        logger.error(f"[PORTAL2 CALLBACK] OAuth error: {e}")
        return render_template(
            "portal/error.html",
            error=f"Error OAuth: {e}",
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
            error=f"El dominio '{domain}' no está autorizado.",
        )

    # Create or update portal user
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
    else:
        portal_user.full_name = name
        portal_user.picture_url = picture

    if not portal_user.is_enabled:
        return render_template(
            "portal/error.html",
            error="Tu cuenta ha sido deshabilitada por el administrador.",
        )

    portal_user.last_auth_at = datetime.now(timezone.utc)
    db.session.commit()

    # Retrieve Aruba params from session
    aruba = session.pop("aruba_params", {})
    post_host = aruba.get("post", "")

    logger.info(f"[PORTAL2 CALLBACK] user={email}, aruba_params={aruba}")

    if post_host:
        # Redirect back to Aruba to authenticate the client
        auth_params = {
            "cmd": "authenticate",
            "mac": aruba.get("mac", ""),
            "network": aruba.get("network", ""),
            "ip": aruba.get("ip", ""),
            "apmac": aruba.get("apmac", ""),
            "site": aruba.get("site", ""),
            "url": aruba.get("url", "http://wifi.apps.grupogaman.com.ar"),
        }
        auth_url = f"https://{post_host}/?{urlencode(auth_params)}"
        logger.info(f"[PORTAL2 CALLBACK] redirecting to Aruba: {auth_url}")
        return redirect(auth_url)

    # No Aruba params - show success page
    return render_template(
        "portal2/success.html",
        name=name,
        email=email,
        picture=picture,
    )
