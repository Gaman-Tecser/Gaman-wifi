import json
import logging
import secrets
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, redirect, url_for,
    session, request, current_app,
)

logger = logging.getLogger(__name__)
from app.extensions import db, oauth
from app.models.allowed_domain import AllowedDomain
from app.models.portal_user import PortalUser
from app.models.oauth_state import OAuthState
from app.services.portal_sync import sync_user_authorize

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


def _generate_password(length=12):
    """Genera una contraseña aleatoria segura."""
    return secrets.token_urlsafe(length)[:length]


@portal_bp.route("/")
def landing():
    return render_template("portal/landing.html")


@portal_bp.route("/login")
def login():
    redirect_uri = url_for("portal.callback", _external=True)
    resp = oauth.google.authorize_redirect(redirect_uri)

    # Save OAuth state to DB (survives cookie/session loss)
    for key in list(session.keys()):
        if key.startswith("_state_google_"):
            state_value = key.replace("_state_google_", "")
            state_data = session[key]
            db.session.merge(OAuthState(
                state=state_value,
                data=json.dumps(state_data),
                mac="",
                aruba_params="{}",
            ))
            db.session.commit()
            logger.info(f"[PORTAL LOGIN] state={state_value} saved to DB")
            break

    return resp


@portal_bp.route("/callback")
def callback():
    state_value = request.args.get("state", "")

    # Restore OAuth state from DB
    session_key = f"_state_google_{state_value}"

    if state_value:
        oauth_state = db.session.get(OAuthState, state_value)
        if oauth_state:
            session[session_key] = json.loads(oauth_state.data)
            db.session.delete(oauth_state)
            db.session.commit()

    try:
        token = oauth.google.authorize_access_token()
        logger.info("[PORTAL CALLBACK] token obtained OK")
    except Exception as e:
        logger.error(f"[PORTAL CALLBACK] OAuth error: {e}")
        return render_template(
            "portal/error.html",
            error=f"Error de autenticación: {e}",
        )

    userinfo = token.get("userinfo")
    if not userinfo:
        logger.error("[PORTAL CALLBACK] No userinfo in token")
        return render_template(
            "portal/error.html",
            error="No se pudo obtener información del usuario.",
        )

    email = userinfo.get("email", "")
    name = userinfo.get("name", email)
    picture = userinfo.get("picture", "")
    domain = email.split("@")[-1].lower() if "@" in email else ""
    logger.info(f"[PORTAL CALLBACK] email={email}, domain={domain}")

    allowed = AllowedDomain.query.filter_by(
        domain=domain, is_active=True
    ).first()
    if not allowed:
        logger.warning(f"[PORTAL CALLBACK] domain NOT allowed: {domain}")
        return render_template(
            "portal/error.html",
            error=f"El dominio '{domain}' no está autorizado.",
        )

    # Create or update portal user
    portal_user = PortalUser.query.filter_by(email=email).first()
    is_new = portal_user is None

    if is_new:
        logger.info(f"[PORTAL CALLBACK] creating new user: {email}")
        portal_user = PortalUser(
            email=email,
            full_name=name,
            picture_url=picture,
            domain=domain,
            group_name=allowed.default_group_name,
            is_enabled=True,
        )
        db.session.add(portal_user)
    else:
        logger.info(f"[PORTAL CALLBACK] existing user: {email}, enabled={portal_user.is_enabled}")
        portal_user.full_name = name
        portal_user.picture_url = picture

    if not portal_user.is_enabled:
        logger.warning(f"[PORTAL CALLBACK] user DISABLED: {email}")
        return render_template(
            "portal/error.html",
            error="Tu cuenta ha sido deshabilitada por el administrador.",
        )

    # Generate WiFi credentials if new user or no password yet
    wifi_password = None
    if is_new or not portal_user.wifi_password_encrypted:
        wifi_password = _generate_password()
        portal_user.set_wifi_password(wifi_password)
        sync_user_authorize(email, wifi_password, portal_user.group_name)
        logger.info(f"[PORTAL CALLBACK] WiFi credentials generated for {email}")
    else:
        wifi_password = portal_user.get_wifi_password()
        logger.info(f"[PORTAL CALLBACK] existing WiFi credentials recovered for {email}")

    portal_user.last_auth_at = datetime.now(timezone.utc)
    db.session.commit()

    # Store email in session for regeneration
    session["portal_email"] = email

    ssid_name = current_app.config.get("WIFI_SSID_NAME", "Gaman-WiFi")

    return render_template(
        "portal/success.html",
        name=name,
        email=email,
        picture=picture,
        wifi_password=wifi_password,
        ssid_name=ssid_name,
    )


@portal_bp.route("/regenerar", methods=["POST"])
def regenerar():
    email = session.get("portal_email")
    if not email:
        return redirect(url_for("portal.landing"))

    portal_user = PortalUser.query.filter_by(email=email).first()
    if not portal_user or not portal_user.is_enabled:
        return redirect(url_for("portal.landing"))

    # Generate new password
    wifi_password = _generate_password()
    portal_user.set_wifi_password(wifi_password)
    sync_user_authorize(email, wifi_password, portal_user.group_name)
    db.session.commit()

    logger.info(f"[PORTAL REGENERAR] new WiFi password for {email}")

    ssid_name = current_app.config.get("WIFI_SSID_NAME", "Gaman-WiFi")

    return render_template(
        "portal/success.html",
        name=portal_user.full_name,
        email=email,
        picture=portal_user.picture_url,
        wifi_password=wifi_password,
        ssid_name=ssid_name,
        regenerated=True,
    )
