from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class APForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    ip_address = StringField("Dirección IP", validators=[DataRequired()])
    secret = StringField("Secret RADIUS", validators=[DataRequired()])
    model = StringField("Modelo")
    location = StringField("Ubicación")
