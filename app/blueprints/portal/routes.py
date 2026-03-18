import json
import logging
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, redirect, url_for,
    session, request,
)

logger = logging.getLogger(__name__)
from app.extensions import db, oauth
from app.models.allowed_domain import AllowedDomain
from app.models.portal_user import PortalUser
from app.models.oauth_state import OAuthState

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


@portal_bp.route("/")
def landing():
    # Capture Aruba params
    aruba_params = {}
    for key in ("cmd", "mac", "network", "ip", "apmac", "site", "post", "url"):
        val = request.args.get(key, "")
        if val:
            aruba_params[key] = val

    mac = aruba_params.get("mac", "")
    logger.info(f"[PORTAL LANDING] mac={mac}, aruba_params={aruba_params}")

    if aruba_params:
        session["aruba_params"] = aruba_params

    return render_template("portal/landing.html", mac=mac)


@portal_bp.route("/login")
def login():
    mac = request.args.get("mac", session.get("aruba_params", {}).get("mac", ""))
    aruba_params = session.get("aruba_params", {})

    redirect_uri = url_for("portal.callback", _external=True)
    resp = oauth.google.authorize_redirect(redirect_uri)

    # Save OAuth state to DB (survives cookie/session loss in captive portals)
    for key in list(session.keys()):
        if key.startswith("_state_google_"):
            state_value = key.replace("_state_google_", "")
            state_data = session[key]
            db.session.merge(OAuthState(
                state=state_value,
                data=json.dumps(state_data),
                mac=mac,
                aruba_params=json.dumps(aruba_params),
            ))
            db.session.commit()
            logger.info(f"[PORTAL LOGIN] state={state_value} saved to DB, mac={mac}")
            break

    return resp


@portal_bp.route("/callback")
def callback():
    state_value = request.args.get("state", "")

    # Restore OAuth state from DB if not in session (cookie lost)
    session_key = f"_state_google_{state_value}"

    if session_key not in session and state_value:
        oauth_state = db.session.get(OAuthState, state_value)
        if oauth_state:
            session[session_key] = json.loads(oauth_state.data)
            logger.info(f"[PORTAL CALLBACK] state restored from DB, mac={oauth_state.mac}")
            db.session.delete(oauth_state)
            db.session.commit()
        else:
            logger.error(f"[PORTAL CALLBACK] state {state_value} not found in DB or session")

    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        logger.error(f"[PORTAL CALLBACK] OAuth error: {e}")
        return render_template(
            "portal/error.html",
            error=f"Error de autenticación: {e}",
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

    logger.info(f"[PORTAL CALLBACK] success: user={email}")

    return render_template(
        "portal/success.html",
        name=name,
        email=email,
        picture=picture,
    )
