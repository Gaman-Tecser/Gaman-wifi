from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, Length


class UserCreateForm(FlaskForm):
    username = StringField(
        "Nombre de usuario (login WiFi)",
        validators=[DataRequired(), Length(max=64)],
    )
    full_name = StringField("Nombre completo", validators=[DataRequired()])
    email = StringField("Email", validators=[Optional(), Email()])
    group_name = SelectField("Grupo", validators=[DataRequired()])
    password = PasswordField(
        "Contraseña WiFi", validators=[DataRequired(), Length(min=8)]
    )
    notes = TextAreaField("Notas", validators=[Optional()])


class UserEditForm(FlaskForm):
    full_name = StringField("Nombre completo", validators=[DataRequired()])
    email = StringField("Email", validators=[Optional(), Email()])
    group_name = SelectField("Grupo", validators=[DataRequired()])
    password = PasswordField(
        "Nueva contraseña (dejar vacío para no cambiar)",
        validators=[Optional(), Length(min=8)],
    )
    notes = TextAreaField("Notas", validators=[Optional()])
