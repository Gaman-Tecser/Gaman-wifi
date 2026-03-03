from cryptography.fernet import Fernet
from flask import current_app
from app.extensions import db


class WifiUser(db.Model):
    __tablename__ = "gaman_wifi_user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), default="")
    group_name = db.Column(
        db.String(80),
        db.ForeignKey("gaman_wifi_group.group_name"),
        nullable=False,
    )
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    password_encrypted = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )
    notes = db.Column(db.Text, default="")

    def set_password(self, cleartext):
        key = current_app.config["FERNET_KEY"].encode()
        self.password_encrypted = Fernet(key).encrypt(cleartext.encode())

    def get_password(self):
        key = current_app.config["FERNET_KEY"].encode()
        return Fernet(key).decrypt(self.password_encrypted).decode()

    def __repr__(self):
        return f"<WifiUser {self.username}>"
