import click
from flask.cli import with_appcontext


@click.command("portal-cleanup")
@with_appcontext
def portal_cleanup_cmd():
    """Elimina usuarios del portal deshabilitados y limpia sus entries RADIUS."""
    from app.extensions import db
    from app.models.portal_user import PortalUser
    from app.services.portal_sync import sync_user_deauthorize

    disabled = PortalUser.query.filter_by(is_enabled=False).all()
    removed = 0
    for user in disabled:
        sync_user_deauthorize(user.email)
        db.session.delete(user)
        removed += 1
    db.session.commit()
    click.echo(f"Limpieza completada: {removed} usuario(s) eliminados.")
