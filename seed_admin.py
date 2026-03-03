"""Crear usuario admin inicial."""
import sys
from getpass import getpass
from app import create_app
from app.extensions import db
from app.models.admin import AdminUser

app = create_app()

with app.app_context():
    if AdminUser.query.first():
        print("Ya existe un admin. Abortando.")
        sys.exit(0)

    username = input("Username admin: ").strip() or "admin"
    full_name = input("Nombre completo: ").strip() or "Administrador"
    password = getpass("Password: ")
    if not password:
        print("Password requerido.")
        sys.exit(1)

    admin = AdminUser(username=username, full_name=full_name)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Admin '{username}' creado exitosamente.")
