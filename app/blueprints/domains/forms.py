from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField
from wtforms.validators import DataRequired


class DomainForm(FlaskForm):
    domain = StringField("Dominio", validators=[DataRequired()])
    default_group_name = SelectField(
        "Grupo/VLAN por defecto", validators=[DataRequired()]
    )
    is_active = BooleanField("Activo", default=True)
