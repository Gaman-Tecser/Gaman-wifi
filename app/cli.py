import click
from flask.cli import with_appcontext


@click.command("portal-cleanup")
@with_appcontext
def portal_cleanup_cmd():
    """Elimina sesiones de portal expiradas y desautoriza MACs huérfanas."""
    from app.services.portal_sync import cleanup_expired_sessions
    removed = cleanup_expired_sessions()
    click.echo(f"Limpieza completada: {removed} MAC(s) desautorizadas.")
