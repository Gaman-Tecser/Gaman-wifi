from app.extensions import db


class AllowedDomain(db.Model):
    __tablename__ = "gaman_allowed_domain"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    default_group_name = db.Column(
        db.String(80),
        db.ForeignKey("gaman_wifi_group.group_name"),
        nullable=False,
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )

    group = db.relationship("WifiGroup", backref="allowed_domains")

    def __repr__(self):
        return f"<AllowedDomain {self.domain}>"
