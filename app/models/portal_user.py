from cryptography.fernet import Fernet
from flask import current_app
from app.extensions import db


class PortalUser(db.Model):
    __tablename__ = "gaman_portal_user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    picture_url = db.Column(db.Text, default="")
    domain = db.Column(db.String(255), nullable=False)
    group_name = db.Column(
        db.String(80),
        db.ForeignKey("gaman_wifi_group.group_name"),
        nullable=False,
    )
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    last_auth_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
    wifi_password_encrypted = db.Column(db.LargeBinary, nullable=True)

    group = db.relationship("WifiGroup", backref="portal_users")

    def set_wifi_password(self, cleartext):
        key = current_app.config["FERNET_KEY"].encode()
        self.wifi_password_encrypted = Fernet(key).encrypt(cleartext.encode())

    def get_wifi_password(self):
        if not self.wifi_password_encrypted:
            return None
        key = current_app.config["FERNET_KEY"].encode()
        return Fernet(key).decrypt(self.wifi_password_encrypted).decode()

    def __repr__(self):
        return f"<PortalUser {self.email}>"
