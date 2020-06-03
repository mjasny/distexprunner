
import os
import json
import urllib.request
import logging



def get_user():
    if 'SUDO_USER' in os.environ:
        return os.environ['SUDO_USER']
    else:
        return os.environ['USER']


def send_slack_notification(webhook, num_exps):
    # curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' <hook-url>
    data = {
        'text': f'_Status report:_\n*{num_exps}* experiments from *{get_user()}* finished.'
    }

    req = urllib.request.Request(
        webhook,
        data=json.dumps(data).encode('utf8'),
        headers={
            'content-type': 'application/json'
        }
    )
    response = urllib.request.urlopen(req)
    logging.info(f'Slack API: {response.read().decode("utf8")}')

