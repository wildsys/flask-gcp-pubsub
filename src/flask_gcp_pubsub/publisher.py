#!/usr/bin/env python
# coding: utf-8

# Imports
import json


class PubCatcher:
    cli = None
    topic = None

    def __init__(self, cli, topic):
        self.cli = cli
        self.topic = topic

    def delay(self, *args, **kwargs):
        data = {
            'args': args,
            'kwargs': kwargs
        }
        data = json.dumps(data).encode()
        self.cli.publish(request={
            'topic': self.topic,
            'messages': [{
                'data': data
            }]
        })
