from flask.ext.wtf import Form
from wtforms import TextField, PasswordField
from wtforms.validators import Required, EqualTo

class LoginForm(Form):
    """
    Login form for project accounts. Rendered on /login page
    """
    project_name = TextField('Project Name', [Required()])
    password = PasswordField('Password', [Required()])

class CreateForm(Form):
    """
    Project account creation form
    """
    project_name = TextField('Project Name', [Required()])
    password = PasswordField('Password', [Required()])
    confirm = PasswordField('Confirm Password', [
        Required(),
        EqualTo('password', message='Passwords must match.')
    ])
    description = TextField('Account Description', [Required()])
