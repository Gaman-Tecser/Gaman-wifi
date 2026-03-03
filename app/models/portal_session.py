from app.extensions import db


class PortalSession(db.Model):
    __tablename__ = "gaman_portal_session"

    id = db.Column(db.Integer, primary_key=True)
    portal_user_id = db.Column(
        db.Integer,
        db.ForeignKey("gaman_portal_user.id"),
        nullable=False,
    )
    mac_address = db.Column(db.String(17), nullable=False)
    authorized_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<PortalSession {self.mac_address}>"
