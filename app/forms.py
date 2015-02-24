from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, TextAreaField, RadioField
from wtforms.validators import Required, EqualTo, Optional

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

class NewCollectorForm(Form):
    """
    Collector creation form
    """
    # Main info
    collector_name = TextField('Collector Name', [Required()])
    network = RadioField('Network',
        [Required()],
        choices=[('twitter', 'Twitter')]
    )
    api = RadioField('API',
        [Required()],
        choices=[('track', 'Track'), ('follow', 'Follow'), ('none', 'None')]
    )

    # OAuth Info
    consumer_key = TextField('Consumer Key', [Required()])
    consumer_secret = TextField('Consumer Secret', [Required()])
    access_token = TextField('Access Token', [Required()])
    access_token_secret = TextField('Access Token Secret', [Required()])

    # Languages & Location
    languages = TextAreaField('Languages', [Optional()])
    locations = TextAreaField('Locations', [Optional()])

    # Terms
    terms = TextAreaField('Terms List', [Optional()])

class ProcessControlForm(Form):
    """
    A base class for collector start/stop/restart buttons
    """
    pass
