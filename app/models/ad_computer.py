from app.extensions import db


class AdComputer(db.Model):
    __tablename__ = "gaman_ad_computer"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  # CN (PC-RECEPCION)
    sam_account_name = db.Column(db.String(255), unique=True, nullable=False)  # PC-RECEPCION$
    dns_hostname = db.Column(db.String(255), default="")
    os = db.Column(db.String(255), default="")
    ou = db.Column(db.String(500), default="")
    description = db.Column(db.String(500), default="")
    group_name = db.Column(
        db.String(80),
        db.ForeignKey("gaman_wifi_group.group_name"),
        nullable=False,
    )
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )

    group = db.relationship("WifiGroup", backref="ad_computers")

    @property
    def radius_username(self):
        """Username que FreeRADIUS recibe en machine auth PEAP.

        Formato: host/computername.domain (sin el $).
        """
        if self.dns_hostname:
            return f"host/{self.dns_hostname}"
        # Fallback: sAMAccountName sin $
        return self.sam_account_name

    def __repr__(self):
        return f"<AdComputer {self.name}>"
