"""Sincronización de usuarios del portal con tablas FreeRADIUS."""
from app.extensions import db
from app.models.radius import Radcheck, Radusergroup


def sync_user_authorize(email, password, group_name):
    """Registra email+password en radcheck + radusergroup."""
    existing = Radcheck.query.filter_by(
        username=email, attribute="Cleartext-Password"
    ).first()
    if not existing:
        db.session.add(Radcheck(
            username=email,
            attribute="Cleartext-Password",
            op=":=",
            value=password,
        ))
    else:
        existing.value = password

    existing_group = Radusergroup.query.filter_by(username=email).first()
    if not existing_group:
        db.session.add(Radusergroup(
            username=email,
            groupname=group_name,
            priority=1,
        ))
    else:
        existing_group.groupname = group_name


def sync_user_deauthorize(email):
    """Elimina email de radcheck y radusergroup."""
    Radcheck.query.filter_by(username=email).delete()
    Radusergroup.query.filter_by(username=email).delete()


def sync_user_update_group(email, new_group):
    """Actualiza el grupo del usuario en radusergroup."""
    row = Radusergroup.query.filter_by(username=email).first()
    if row:
        row.groupname = new_group


def sync_user_update_password(email, new_password):
    """Actualiza password en radcheck."""
    row = Radcheck.query.filter_by(
        username=email, attribute="Cleartext-Password"
    ).first()
    if row:
        row.value = new_password
