"""Consulta equipos del Active Directory via LDAP."""
import logging
from ldap3 import Server, Connection, ALL, SUBTREE

logger = logging.getLogger(__name__)


def fetch_ad_computers(host, base_dn, bind_user, bind_password):
    """Consulta AD y devuelve lista de equipos (computer accounts) habilitados.

    Returns:
        list[dict]: cada dict tiene keys: name, sam_account_name, dns_hostname, os, ou
    """
    server = Server(host, get_info=ALL)
    conn = Connection(server, user=bind_user, password=bind_password, auto_bind=True)

    # Filter: computer accounts, not disabled
    # userAccountControl bit 2 = ACCOUNTDISABLE
    search_filter = (
        "(&(objectClass=computer)"
        "(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
    )

    conn.search(
        search_base=base_dn,
        search_filter=search_filter,
        search_scope=SUBTREE,
        attributes=[
            "cn", "sAMAccountName", "dNSHostName",
            "operatingSystem", "distinguishedName", "description",
        ],
    )

    computers = []
    for entry in conn.entries:
        name = str(entry.cn) if entry.cn else ""
        sam = str(entry.sAMAccountName) if entry.sAMAccountName else ""
        if not sam:
            continue

        dns_hostname = str(entry.dNSHostName) if entry.dNSHostName else ""
        os_name = str(entry.operatingSystem) if entry.operatingSystem else ""
        dn = str(entry.distinguishedName) if entry.distinguishedName else ""
        description = str(entry.description) if entry.description else ""

        # Extract OU from DN
        ou = ""
        parts = dn.split(",")
        ou_parts = [p.replace("OU=", "") for p in parts if p.startswith("OU=")]
        if ou_parts:
            ou = " > ".join(reversed(ou_parts))

        computers.append({
            "name": name,
            "sam_account_name": sam,  # e.g. PC-RECEPCION$
            "dns_hostname": dns_hostname,
            "os": os_name,
            "ou": ou,
            "description": description,
        })

    conn.unbind()
    logger.info(f"[AD_SYNC] fetched {len(computers)} computers from AD")
    return computers
