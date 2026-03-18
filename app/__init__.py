from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    from app.extensions import db, login_manager, csrf, migrate, oauth

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db, include_schemas=False)
    oauth.init_app(app)

    # Registrar proveedor Google OAuth
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    from app.models.admin import AdminUser

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(AdminUser, int(user_id))

    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.dashboard.routes import dashboard_bp
    from app.blueprints.users.routes import users_bp
    from app.blueprints.groups.routes import groups_bp
    from app.blueprints.access_points.routes import ap_bp
    from app.blueprints.domains.routes import domains_bp
    from app.blueprints.portal_users.routes import portal_users_bp
    from app.blueprints.portal.routes import portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(ap_bp)
    app.register_blueprint(domains_bp)
    app.register_blueprint(portal_users_bp)
    app.register_blueprint(portal_bp)

    # Excluir portal público de CSRF
    csrf.exempt(portal_bp)

    # CLI commands
    from app.cli import portal_cleanup_cmd
    app.cli.add_command(portal_cleanup_cmd)

    return app
