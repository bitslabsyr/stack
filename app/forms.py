from flask.ext.wtf import Form
from wtforms import TextField, PasswordField
from wtforms.validators import Required

class LoginForm(Form):
    """
    Login form for project accounts. Rendered on /login page
    """
    project_name = TextField('Project Name', [Required()])
    password = PasswordField('Password', [Required()])
