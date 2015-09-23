from sendgrid import SendGridClient, Mail, SendGridError, SendGridClientError, SendGridServerError
from jinja2 import Template

# TODO - Set as os.environ var
API_KEY = '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'

def process_system_stats(system_stats):
    stats = {
        'total': 0,
        'critical': None,
        'total_critical': 0,
        'warn': None,
        'total_warn': 0,
        'info': None,
        'total_info': 0,
    }

    # A) Critical
    critical = []
    if system_stats['avail_space'] < 20:
        critical.append({
            'title': 'Storage Space Low - %d' % system_stats['avail_space'],
            'message': 'System storage space is below 20GB, now at %dGB' % system_stats['avail_space'],
        })

    if not system_stats['mongo_running']:
        critical.append({
            'title': 'Mongo Error',
            'message': 'MongoDB has stopped running on the server!',
        })

    stats['critical'] = critical if critical else None

    # TODO B & C - warn & info
    warn = []
    info = []

    # D) Counts
    stats['total_critical'] = len(critical)
    stats['total_warn'] = len(warn)
    stats['total_info'] = len(info)
    stats['total'] = stats['total_critical'] + stats['total_warn'] + stats['total_info']

    return stats

def process_project_stats(project_stats):
    stats = {
        'collectors': {
            'total': 0,
            'critical': None,
            'total_critical': 0,
            'warn': None,
            'total_warn': 0,
            'info': None,
            'total_info': 0,
        }
    }

    # A) Critical
    critical = []
    for collector in project_stats['collectors']:
        if collector['flags']['run'] and not collector['daemon_running']:
            critical.append({
                'title': 'Unexpected process termination',
                'message': 'Collector "%s" has stopped without being flagged to do so.' % collector['collector_name'],
            })

        if collector['flags']['collect'] and collector['network'] == 'twitter' and not collector['listener_running']:
            critical.append({
                'title': 'Collector running without listener',
                'message': 'Collector "%s" is running without a connection to the Streaming API' % collector['collector_name'],
            })

    stats['collectors']['critical'] = critical if critical else None
    stats['collectors']['total_critical'] = len(critical)
    stats['collectors']['total'] = len(critical)

    # TODO in future - warn & info
    # TODO in future - stats for processor & inserter

    return stats

def generate_email_text(report):
    template = Template("""
        <html>
        <body>
        <h1>STACKS System Status Update</h1>

        <hr />

        {% if report['system']['total'] %}
            <h2>System Issues - {{ report['system']['total'] }}</h2>

            {% if report['system']['critical'] %}
            <h3>CRITICAL System Issues - {{ report['system']['total_critical'] }}</h3>
            {% for issue in report['system']['critical'] %}
                <p><strong>{{ issue['title'] }}</strong><br />{{ issue['message'] }}</p>
            {% endfor %}
            {% endif %}

            {% if report['system']['warn'] %}
            <h3>WARN System Issues - {{ report['system']['total_warn'] }}</h3>
            {% for issue in report['system']['warn'] %}
                <p><strong>{{ issue['title'] }}</strong><br />{{ issue['message'] }}</p>
            {% endfor %}
            {% endif %}

            {% if report['system']['info'] %}
            <h3>INFO System Issues - {{ report['system']['total_info'] }}</h3>
            {% for issue in report['system']['info'] %}
                <p><strong>{{ issue['title'] }}</strong><br />{{ issue['message'] }}</p>
            {% endfor %}
            {% endif %}
        {% endif %}

        {% if report['project']['collectors']['total'] %}
            <h2>Collector Issues - {{ report['project']['collectors']['total'] }}</h2>

            {% if report['project']['collectors']['critical'] %}
            <h3>CRITICAL System Issues - {{ report['project']['collectors']['total_critical'] }}</h3>
            {% for issue in report['project']['collectors']['critical'] %}
                <p><strong>{{ issue['title'] }}</strong><br />{{ issue['message'] }}</p>
            {% endfor %}
            {% endif %}

            {% if report['project']['collectors']['warn'] %}
            <h3>WARN System Issues - {{ report['project']['collectors']['total_warn'] }}</h3>
            {% for issue in report['project']['collectors']['warn'] %}
                <p><strong>{{ issue['title'] }}</strong><br />{{ issue['message'] }}</p>
            {% endfor %}
            {% endif %}

            {% if report['project']['collectors']['info'] %}
            <h3>INFO System Issues - {{ report['project']['collectors']['total_info'] }}</h3>
            {% for issue in report['project']['collectors']['info'] %}
                <p><strong>{{ issue['title'] }}</strong><br />{{ issue['message'] }}</p>
            {% endfor %}
            {% endif %}
        {% endif %}

        </body>
        </html>
    """)

    return template.render(report=report)

def send_email(report):
    sg = SendGridClient(API_KEY, raise_errors=True)

    message = Mail()
    message.add_to('Billy Ceskavich <bceskavich@gmail.com>')
    message.set_subject('STACKS Status Update')
    message.set_html(generate_email_text(report))
    message.set_from('STACKS <noreply@bits.ischool.syr.edu>')

    try:
        sg.send(message)
    except SendGridError as e:
        print e
    except SendGridClientError as e:
        print e
    except SendGridServerError as e:
        print e

def process_and_notify(system_stats, project_stats):
    # Empty report dict to be populated with stats
    report = {}
    report['system'] = process_system_stats(system_stats)
    report['project'] = process_project_stats(project_stats)

    send_email(report) #, project_stats['email'])
