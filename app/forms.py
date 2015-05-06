from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, TextAreaField, RadioField, SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, EqualTo, Optional
from wtforms import ValidationError


class RequiredIfNetwork(object):
    """
    Custom validator to set required fields only for a given network
    """
    def __init__(self, network_valid):
        self.network_valid = network_valid
        self.message = 'Field is required for network: %s' % self.network_valid

    def __call__(self, form, field):
        network = form['network'].data
        if self.network_valid == network:
            if field.data is None or field.data == '':
                raise ValidationError(self.message)


class TwitterTermsVal(object):
    """
    Custom validator for Twitter terms. They are required if an API is selected
    """
    def __init__(self):
        self.message = 'Terms are required if a Twitter API filter is selected.'

    def __call__(self, form, field):
        api_filter = form['api'].data
        network = form['network'].data
        if network == 'twitter' and api_filter == 'track' or api_filter == 'follow':
            if field.data is None or field.data == '':
                raise ValidationError(self.message)


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
        choices=[('twitter', 'Twitter'), ('facebook', 'Facebook')]
    )

    """ Facebook Info """
    # Collection type will become valid for all networks eventually
    collection_type = SelectField(
        'Collection Type',
        [RequiredIfNetwork('facebook')],
        choices=[('realtime', 'Real Time'), ('historical', 'Historical')]
    )

    # Since & Until
    start_date = DateField('Start Date (optional)', [Optional()])
    end_date = DateField('End Date (optional)', [Optional()])

    # Facebook OAuth Info
    client_id = StringField('Client ID', [RequiredIfNetwork('facebook')])
    client_secret = StringField('Client Secret', [RequiredIfNetwork('facebook')])

    # Terms
    facebook_terms = TextAreaField('Facebook Terms List', [RequiredIfNetwork('facebook')])

    """ Twitter Info """
    # Twitter API filter info
    api = SelectField(
        'Twitter API Filter',
        [RequiredIfNetwork('twitter')],
        choices=[('track', 'Track'), ('follow', 'Follow'), ('none', 'None')]
    )

    # OAuth Info
    consumer_key = StringField('Consumer Key', [RequiredIfNetwork('twitter')])
    consumer_secret = StringField('Consumer Secret', [RequiredIfNetwork('twitter')])
    access_token = StringField('Access Token', [RequiredIfNetwork('twitter')])
    access_token_secret = StringField('Access Token Secret', [RequiredIfNetwork('twitter')])

    # Languages & Location
    languages = TextAreaField('Languages (optional)', [Optional()])
    locations = TextAreaField('Locations (optional)', [Optional()])

    # Terms
    twitter_terms = TextAreaField('Twitter Terms List', [TwitterTermsVal()])


class UpdateCollectorForm(Form):
    """
    Form for updating a collectors details. Terms are handled separately via form prefixes.
    """
    collector_name = StringField('Collector Name', [Optional()])
    new_terms = TextAreaField('New Terms', [Optional()])

    """ Facebook Fields """
    collection_type = SelectField(
        'Collection Type',
        [Optional()],
        choices=[('realtime', 'Real Time'), ('historical', 'Historical')]
    )
    start_date = DateField('Start Date', [Optional()])
    end_date = DateField('End Date', [Optional()])
    client_id = StringField('Client ID', [Optional()])
    client_secret = StringField('Client Secret', [Optional()])

    """ Twitter Fields """
    api = SelectField(
        'Twitter API Filter',
        [Optional()],
        choices=[('track', 'Track'), ('follow', 'Follow'), ('none', 'None')]
    )
    consumer_key = StringField('Consumer Key', [Optional()])
    consumer_secret = StringField('Consumer Secret', [Optional()])
    access_token = StringField('Access Token', [Optional()])
    access_token_secret = StringField('Access Token Secret', [Optional()])
    languages = TextAreaField('Languages', [Optional()])
    locations = TextAreaField('Locations', [Optional()])


class UpdateCollectorTermsForm(Form):
    """
    For for updating a collector term details. Rendered multiple times w/ prefixes, along with the UpdateCollectorForm()
    """
    term = StringField('Term', [Optional()])
    collect = SelectField(
        'Collect',
        [Optional()],
        choices=[(0, 'No'), (1, 'Yes')]
    )


class ProcessControlForm(Form):
    """
    A base class for collector start/stop/restart buttons
    """
    pass