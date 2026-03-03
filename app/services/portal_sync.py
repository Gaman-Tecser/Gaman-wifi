"""Sincronización de MACs del portal cautivo con tablas FreeRADIUS."""
import re
from datetime import datetime, timezone

from app.extensions import db
from app.models.radius import Radcheck, Radusergroup
from app.models.portal_session import PortalSession


def normalize_mac(raw):
    """Normaliza una MAC a formato aa:bb:cc:dd:ee:ff (minúsculas, con dos puntos)."""
    clean = re.sub(r"[^0-9a-fA-F]", "", raw)
    if len(clean) != 12:
        raise ValueError(f"MAC inválida: {raw}")
    lower = clean.lower()
    return ":".join(lower[i:i+2] for i in range(0, 12, 2))


def sync_mac_authorize(mac, group_name):
    """Registra MAC en radcheck (Cleartext-Password) + radusergroup."""
    normalized = normalize_mac(mac)
    # Evitar duplicados
    existing = Radcheck.query.filter_by(
        username=normalized, attribute="Cleartext-Password"
    ).first()
    if not existing:
        db.session.add(Radcheck(
            username=normalized,
            attribute="Cleartext-Password",
            op=":=",
            value=normalized,
        ))
    existing_group = Radusergroup.query.filter_by(username=normalized).first()
    if not existing_group:
        db.session.add(Radusergroup(
            username=normalized,
            groupname=group_name,
            priority=1,
        ))
    else:
        existing_group.groupname = group_name


def sync_mac_deauthorize(mac):
    """Elimina MAC de radcheck y radusergroup."""
    normalized = normalize_mac(mac)
    Radcheck.query.filter_by(username=normalized).delete()
    Radusergroup.query.filter_by(username=normalized).delete()


def sync_mac_update_group(mac, new_group):
    """Actualiza el grupo de la MAC en radusergroup."""
    normalized = normalize_mac(mac)
    row = Radusergroup.query.filter_by(username=normalized).first()
    if row:
        row.groupname = new_group


def cleanup_expired_sessions():
    """Elimina sesiones expiradas y desautoriza MACs huérfanas."""
    now = datetime.now(timezone.utc)
    expired = PortalSession.query.filter(PortalSession.expires_at < now).all()
    removed = 0
    for session in expired:
        # Solo desautorizar si no tiene otra sesión activa para la misma MAC
        other_active = PortalSession.query.filter(
            PortalSession.mac_address == session.mac_address,
            PortalSession.id != session.id,
            PortalSession.expires_at >= now,
        ).first()
        if not other_active:
            sync_mac_deauthorize(session.mac_address)
            removed += 1
        db.session.delete(session)
    db.session.commit()
    return removed
