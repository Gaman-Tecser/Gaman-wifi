from flask import Blueprint, render_template
from flask_login import login_required
from app.extensions import db
from app.models.wifi_user import WifiUser
from app.models.wifi_group import WifiGroup
from app.models.access_point import GamanAccessPoint
from app.models.portal_user import PortalUser
from app.models.portal_session import PortalSession
from app.models.radius import Radacct, Radpostauth

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")


@dashboard_bp.before_request
@login_required
def require_login():
    pass


@dashboard_bp.route("/")
def index():
    total_users = WifiUser.query.count()
    enabled_users = WifiUser.query.filter_by(is_enabled=True).count()
    total_groups = WifiGroup.query.count()
    total_aps = GamanAccessPoint.query.count()

    # Sesiones activas (radacct sin acctstoptime)
    active_sessions = (
        Radacct.query
        .filter(Radacct.acctstoptime.is_(None))
        .order_by(Radacct.acctstarttime.desc())
        .limit(50)
        .all()
    )

    # Últimas autenticaciones
    recent_auths = (
        Radpostauth.query
        .order_by(Radpostauth.authdate.desc())
        .limit(20)
        .all()
    )

    # Portal cautivo
    total_portal_users = PortalUser.query.count()
    active_portal_sessions = PortalSession.query.filter(
        PortalSession.expires_at >= db.func.now()
    ).count()

    return render_template(
        "dashboard/index.html",
        total_users=total_users,
        enabled_users=enabled_users,
        total_groups=total_groups,
        total_aps=total_aps,
        active_sessions=active_sessions,
        recent_auths=recent_auths,
        total_portal_users=total_portal_users,
        active_portal_sessions=active_portal_sessions,
    )
