from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, NumberRange


class GroupForm(FlaskForm):
    group_name = StringField("Nombre del grupo", validators=[DataRequired()])
    description = TextAreaField("Descripción")
    vlan_id = IntegerField(
        "VLAN ID", validators=[DataRequired(), NumberRange(min=1, max=4094)]
    )
