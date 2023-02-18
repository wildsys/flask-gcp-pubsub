#!/usr/bin/env python
# coding: utf-8

# Imports
from flask import Flask
from google.api_core import retry
from google import pubsub
from google.oauth2 import service_account
from .publisher import PubCatcher
import threading
import traceback
import time
import json


# Overload Flask
class PubSub:
    flask = None
    gcp_pub_client = None
    gcp_sub_client = None
    project_id = None
    topic_prefix = None
    concurrent_consumers = 4
    concurrent_messages = 2
    gcp_credentials_json = None
    gcp_credentials_file = None
    requests = []
    callbacks = {}
    configuration_table = {
        'PUBSUB_PROJECT_ID': 'project_id',
        'PUBSUB_CREDENTIALS_JSON': 'gcp_credentials_json',
        'PUBSUB_CREDENTIALS_FILE': 'gcp_credentials_file',
        'PUBSUB_CONCURRENT_CONSUMERS': 'concurrent_consumers',
        'PUBSUB_CONCURRENT_MESSAGES': 'concurrent_messages',
        'PUBSUB_TOPIC_PREFIX': 'topic_prefix'
    }

    def __init__(self, app: Flask = None, **kwargs):
        if app:
            self.init_app(app)
        cfgtable = self.configuration_table.values()
        for cfgkey in kwargs:
            assert cfgkey in cfgtable, f'Unknown option "{cfgkey}"'
            setattr(self, cfgkey, kwargs.get(cfgkey))

    def init_app(self, app: Flask):
        """Initialize with Flask application context"""
        self.flask = app
        self.init_config()

    def init_config(self):
        """Get configuration from Flask application context"""
        for cfgkey in self.configuration_table:
            setattr(self, cfgkey, self.flask.config.get(cfgkey, None))

    def check_configuration(self):
        """Ensure configuration is ready"""
        check_keys = {
            'project_id': {
                'type': (str, )
            }
        }
        for cfgkey, cfgparams in check_keys.items():
            assert isinstance(getattr(self, cfgkey), cfgparams['type']), f'Invalid type expected for "{cfgkey}'

    def get_pub_client(self):
        """Client Publisher to GCP Pub/Sub"""
        if not self.gcp_pub_client:
            creds = None
            if self.gcp_credentials_json:
                creds = service_account.Credentials.from_service_account_info(self.gcp_credentials_json)
            elif self.gcp_credentials_file:
                creds = service_account.Credentials.from_service_account_file(self.gcp_credentials_file)
            self.gcp_pub_client = pubsub.PublisherClient(credentials=creds)
        return self.gcp_pub_client

    def get_sub_client(self):
        """Client Subscriber from GCP Pub/Sub"""
        if not self.gcp_sub_client:
            creds = None
            if self.gcp_credentials_json:
                creds = service_account.Credentials.from_service_account_info(self.gcp_credentials_json)
            elif self.gcp_credentials_file:
                creds = service_account.Credentials.from_service_account_file(self.gcp_credentials_file)
            self.gcp_sub_client = pubsub.SubscriberClient(credentials=creds)
        return self.gcp_sub_client

    def create_topic(self, name):
        """Create a dedicated topic if needed"""
        if self.topic_prefix:
            name = f'{self.topic_prefix}_{name}'
        cli = self.get_pub_client()
        topic_path = cli.topic_path(self.project_id, name)
        topics = cli.list_topics(
            request={
                'project': f'projects/{self.project_id}'
            }
        )
        found = False
        for topic in topics:
            if topic.name == topic_path:
                found = True
                break
        if not found:
            topic = cli.create_topic(
                request={
                    'name': topic_path
                }
            )
        return topic_path

    def callback_subscription(self, message):
        print('received', message)
        message.ack()

    def register_subscriber(self, func):
        """Create a subscription to the function"""
        identifier = func.__name__
        if self.topic_prefix:
            identifier = f'{self.topic_prefix}_{identifier}'
        cli_pub = self.get_pub_client()
        cli_sub = self.get_sub_client()
        topic_path = cli_pub.topic_path(self.project_id, identifier)
        subscription_path = cli_sub.subscription_path(self.project_id, identifier)

        subscriptions = cli_sub.list_subscriptions(
            request={
                'project': f'projects/{self.project_id}'
            }
        )

        sub = None
        for regsub in subscriptions:
            if regsub.name == subscription_path:
                sub = regsub
                break
        if not sub:
            sub = cli_sub.create_subscription(
                request={
                    'name': subscription_path,
                    'topic': topic_path
                }
            )

        self.requests.append({
            'name': subscription_path,
            'topic': topic_path,
            'callback': func,
            'weight': 5
        })

    def pull_item(self):
        cli = self.get_sub_client()
        requests = sorted(self.requests, key=lambda x: x['weight'])
        for request in requests:
            response = cli.pull(
                request={
                    'subscription': request['name'],
                    'max_messages': self.concurrent_messages
                },
                retry=retry.Retry(deadline=300)
            )
            if len(response.received_messages) > 0:
                ack_ids = []
                funcref = request['topic'].split('/')[-1]
                for message in response.received_messages:
                    ack_ids.append(message.ack_id)
                    data = json.loads(message.message.data)
                    args = data.get('args', [])
                    kwargs = data.get('kwargs', {})
                    result = None
                    exec_time = time.time()
                    print(f'status=received message_id={message.message.message_id} function={funcref}')
                    try:
                        result = request['callback'](*args, **kwargs)
                    except Exception:
                        result = 'crash'
                        traceback.print_exc()
                    exec_time = time.time() - exec_time
                    print(f'status=processed message_id={message.message.message_id} function={funcref} result={result} execution_time={exec_time}')

                cli.acknowledge(
                    request={
                        'subscription': request['name'],
                        'ack_ids': ack_ids
                    }
                )
                return

    def run(self):
        print('Start consumers')
        while True:
            slots = (self.concurrent_consumers + 1) - threading.active_count()
            for slot in range(slots):
                thr = threading.Thread(target=self.pull_item)
                thr.start()
            time.sleep(0.5)

    def task(self, f):
        """Register a new task"""
        self.check_configuration()
        topic = self.create_topic(f.__name__)
        self.register_subscriber(f)
        return PubCatcher(self.get_pub_client(), topic)
