from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, TextAreaField, RadioField, DateField
from wtforms.validators import DataRequired, EqualTo, Optional
from wtforms import ValidationError


class LoginForm(Form):
    """
    Login form for project accounts. Rendered on /login page
    """
    project_name = StringField('Project Name', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])


class CreateForm(Form):
    """
    Project account creation form
    """
    project_name = StringField('Project Name', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    confirm = PasswordField('Confirm Password', [
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    description = StringField('Account Description', [DataRequired()])


class SetupForm(Form):
    """
    Admin account setup form
    """
    project_name = StringField('Project Name', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    confirm = PasswordField('Confirm Password', [
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])


class NewCollectorForm(Form):
    """
    Collector creation form
    """
    # Universal Collector Information
    collector_name = StringField('Collector Name', [DataRequired()])
    network = RadioField(
        'Network',
        [DataRequired()],
        choices=[('twitter', 'Twitter')]
    )

    """ Facebook Info """
    # Collection type will become valid for all networks eventually
    collection_type = RadioField('Collection Type', [required_if_network(network, 'facebook')],
                                 choices=[('realtime', 'Real Time'), ('historical', 'Historical')])

    # Since & Until
    start_date = DateField('Start Date (optional)', [Optional()])
    end_date = DateField('End Date (optional)', [Optional()])

    # Facebook OAuth Info
    client_id = StringField('Client ID', [required_if_network(network, 'facebook')])
    client_secret = StringField('Client Secret', [required_if_network(network, 'facebook')])

    # Terms
    facebook_terms = TextAreaField('Collection Terms', [required_if_network(network, 'facebook')])

    """ Twitter Info """
    # Twitter API filter info
    api = RadioField(
        'Twitter API Filter',
        [required_if_network(network, 'twitter')],
        choices=[('track', 'Track'), ('follow', 'Follow'), ('none', 'None')]
    )

    # OAuth Info
    consumer_key = StringField('Consumer Key', [required_if_network(network, 'twitter')])
    consumer_secret = StringField('Consumer Secret', [required_if_network(network, 'twitter')])
    access_token = StringField('Access Token', [required_if_network(network, 'twitter')])
    access_token_secret = StringField('Access Token Secret', [required_if_network(network, 'twitter')])

    # Languages & Location
    languages = TextAreaField('Languages (optional)', [Optional()])
    locations = TextAreaField('Locations (optional)', [Optional()])

    # Terms
    twitter_terms = TextAreaField('Terms List', [Optional()])


class ProcessControlForm(Form):
    """
    A base class for collector start/stop/restart buttons
    """
    pass


def required_if_network(required_network, network):
    """
    Custom validator to set required fields only for a given network
    """
    message = 'Field is required for %s collectors.' % network

    def _required_if_network(form, field):
        if field.data is None and required_network == network:
            raise ValidationError(message)

    return _required_if_network