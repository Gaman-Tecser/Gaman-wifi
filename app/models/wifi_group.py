from app.extensions import db


class WifiGroup(db.Model):
    __tablename__ = "gaman_wifi_group"

    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), default="")
    vlan_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )

    users = db.relationship("WifiUser", backref="group", lazy="dynamic")

    def __repr__(self):
        return f"<WifiGroup {self.group_name} VLAN={self.vlan_id}>"
