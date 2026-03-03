"""Sincronización entre tablas gaman_* y tablas FreeRADIUS."""
from app.extensions import db
from app.models.radius import (
    Radcheck, Radusergroup, Radgroupreply, Nas,
)


def sync_user_create(username, password, group_name):
    """Inserta en radcheck + radusergroup al crear un usuario WiFi."""
    db.session.add(Radcheck(
        username=username,
        attribute="Cleartext-Password",
        op=":=",
        value=password,
    ))
    db.session.add(Radusergroup(
        username=username,
        groupname=group_name,
        priority=1,
    ))


def sync_user_delete(username):
    """Elimina todas las entradas de radcheck y radusergroup para el usuario."""
    Radcheck.query.filter_by(username=username).delete()
    Radusergroup.query.filter_by(username=username).delete()


def sync_user_update_password(username, new_password):
    """Actualiza la contraseña en radcheck."""
    row = Radcheck.query.filter_by(
        username=username, attribute="Cleartext-Password"
    ).first()
    if row:
        row.value = new_password


def sync_user_update_group(username, old_group, new_group):
    """Cambia el grupo en radusergroup."""
    row = Radusergroup.query.filter_by(
        username=username, groupname=old_group
    ).first()
    if row:
        row.groupname = new_group


def sync_user_disable(username):
    """Agrega Auth-Type := Reject para bloquear al usuario."""
    existing = Radcheck.query.filter_by(
        username=username, attribute="Auth-Type"
    ).first()
    if not existing:
        db.session.add(Radcheck(
            username=username,
            attribute="Auth-Type",
            op=":=",
            value="Reject",
        ))


def sync_user_enable(username):
    """Elimina Auth-Type Reject para rehabilitar al usuario."""
    Radcheck.query.filter_by(
        username=username, attribute="Auth-Type", value="Reject"
    ).delete()


def sync_group_create(group_name, vlan_id):
    """Inserta las 3 entradas de radgroupreply para asignación VLAN."""
    entries = [
        ("Tunnel-Type", "VLAN"),
        ("Tunnel-Medium-Type", "IEEE-802"),
        ("Tunnel-Private-Group-Id", str(vlan_id)),
    ]
    for attr, val in entries:
        db.session.add(Radgroupreply(
            groupname=group_name,
            attribute=attr,
            op=":=",
            value=val,
        ))


def sync_group_update_vlan(group_name, new_vlan_id):
    """Actualiza el VLAN ID en radgroupreply."""
    row = Radgroupreply.query.filter_by(
        groupname=group_name, attribute="Tunnel-Private-Group-Id"
    ).first()
    if row:
        row.value = str(new_vlan_id)


def sync_group_delete(group_name):
    """Elimina todas las entradas de radgroupreply para el grupo."""
    Radgroupreply.query.filter_by(groupname=group_name).delete()


def sync_ap_create(ip_address, name, secret):
    """Inserta en la tabla nas y devuelve el id."""
    nas = Nas(
        nasname=ip_address,
        shortname=name,
        type="other",
        secret=secret,
        description="Managed by Gaman WiFi",
    )
    db.session.add(nas)
    db.session.flush()
    return nas.id


def sync_ap_delete(nas_id):
    """Elimina la entrada NAS."""
    if nas_id:
        Nas.query.filter_by(id=nas_id).delete()
