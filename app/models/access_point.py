from app.extensions import db


class GamanAccessPoint(db.Model):
    __tablename__ = "gaman_access_point"

    id = db.Column(db.Integer, primary_key=True)
    nas_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    secret = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), default="")
    location = db.Column(db.String(200), default="")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )

    def __repr__(self):
        return f"<AP {self.name} ({self.ip_address})>"
