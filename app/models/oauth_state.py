from app.extensions import db


class OAuthState(db.Model):
    __tablename__ = "gaman_oauth_state"

    state = db.Column(db.String(100), primary_key=True)
    data = db.Column(db.Text, nullable=False)
    mac = db.Column(db.String(17), default="")
    aruba_params = db.Column(db.Text, default="{}")
    created_at = db.Column(
        db.DateTime, server_default=db.func.now(), nullable=False
    )
