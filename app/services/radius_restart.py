"""Reiniciar FreeRADIUS vía SSH con paramiko."""
import paramiko
from flask import current_app


def restart_freeradius():
    """Ejecuta systemctl restart freeradius en el servidor RADIUS. Devuelve (ok, mensaje)."""
    host = current_app.config["RADIUS_SSH_HOST"]
    user = current_app.config["RADIUS_SSH_USER"]
    password = current_app.config["RADIUS_SSH_PASSWORD"]

    if not password:
        return False, "RADIUS_SSH_PASSWORD no configurado."

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password, timeout=10)
        _stdin, stdout, stderr = client.exec_command(
            "sudo systemctl restart freeradius", timeout=15
        )
        exit_code = stdout.channel.recv_exit_status()
        if exit_code == 0:
            return True, "FreeRADIUS reiniciado correctamente."
        err = stderr.read().decode().strip()
        return False, f"Error (código {exit_code}): {err}"
    except Exception as e:
        return False, f"Error SSH: {e}"
    finally:
        client.close()
