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

    group = db.relationship("WifiGroup", backref="portal_users")
    sessions = db.relationship(
        "PortalSession", backref="portal_user", lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<PortalUser {self.email}>"
