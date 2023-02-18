#!/usr/bin/env python
# coding: utf-8


class BucketCatcher:
    cli = None
    topic = None

    def __init__(self, cli, topic, bucket_name, **kwargs):
        self.cli = cli
        self.topic = topic
        bucket = self.cli.bucket(bucket_name)
        topic_name = topic.split('/')[-1]

        filter_event = kwargs.get('events', None)

        notifications = bucket.list_notifications()
        for ntf in notifications:
            if ntf.topic_name != topic_name:
                continue
            if filter_event is None and ntf.event_types is None:
                ntf.delete()
            elif filter_event and ntf.event_types and sorted(filter_event) == sorted(ntf.event_types):
                ntf.delete()

        notification = bucket.notification(topic_name=topic_name, event_types=filter_event)
        notification.create()
