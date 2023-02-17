# Flask GCP Pub/Sub

Lite distributed task queue using Google Cloud Platform (GCP) Pub/Sub

[![PyPI version](https://img.shields.io/pypi/v/flask-gcp-pubsub)](https://github.com/wildsys/flask-gcp-pubsub) [![PyPI downloads](https://img.shields.io/pypi/dm/flask-gcp-pubsub)](https://github.com/wildsys/flask-gcp-pubsub) [![GNU GPLv3](https://img.shields.io/github/license/wildsys/flask-gcp-pubsub)](https://www.gnu.org/licenses/gpl-3.0.html)

<!-- TOC depthfrom:2 -->

- [🤔 What does this package does?](#-what-does-this-package-does)
- [🚀 Getting started](#-getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Full example](#full-example)
    - [Configuration](#configuration)
- [🔮 Roadmap](#-roadmap)
    - [TO BE CONFIRMED](#to-be-confirmed)

<!-- /TOC -->

## 🤔 What does this package does?

As Celery, but in a lighter version, this package allows you to run operations asynchronously in your Flask project, but without the choice of the broker: it only uses GCP Pub/Sub.

Technically, this package can run without Flask, but, historically, it comes to have a quick-win for migrating to GCP Cloud Run using the Pub/Sub system, from an existing project using Flask + Celery.

This package aims to remove some painful tasks by:
- Creating one dedicated topic for each function
- Creating one dedicated reusable subscription for each function

We **do not recommand** this package for the following cases:
- You need to reuse your development in a multi-cloud context
- You have high volume of messages to process (not tested)

This package is given "as it", without garantees, under the GPLv3 License.

## 🚀 Getting started

### Prerequisites

- A [Google Cloud account](https://console.cloud.google.com/)
- A GCP project ([here to create a new one](https://console.cloud.google.com/projectcreate)), with [Pub/Sub API enabled](https://console.cloud.google.com/apis/library/pubsub.googleapis.com) (take care to select the good one)
- A [Service Account](https://console.cloud.google.com/iam-admin/serviceaccounts) for which one you need a credential JSON file (`creds.json` in example below), with roles:
  - Pub/Sub Admin
- A local environment with Python >= 3.9

### Installation

```python
pip install flask-gcp-pubsub
```

### Full example

`demo.py`
```python
#!/usr/bin/env python
# coding: utf-8

from flask import Flask, make_response
from flask_gcp_pubsub import PubSub

app = Flask(__name__)
pubsub = PubSub(
    app,
    project_id='<project_id>',
    gcp_credentials_file='./creds.json'
)

@pubsub.task
def my_task(msg1, msg2):
    """Awesome delayed execution"""
    print('test', msg1, msg2)
    return 'ok'

@app.route('/test')
def route_test():
    """Launch delayed execution"""
    my_task.delay('test1', 'test2')
    return make_response('ok', 200)
```

**WARNING**: do not forget to replace `<project_id>` with you GCP project ID (not number) and to downloed the JSON-formatted key from GCP Console.

`wsgi.py`
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Imports
from demo import app

# Start
if __name__ == '__main__':
    app.run()
```

`wsgi_delayed.py`
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Imports
from demo import pubsub

# Start
if __name__ == '__main__':
    pubsub.run()
```

This command will launch the Flask server:
```shell
flask run --port 9090
```

This command will launch the asynchronous tasks manager:
```shell
python wsgi_delayed.py
```

You can now navigate to http://localhost:9090/test
And if everything goes OK, you just have to check the content of the output in console, which should look something like that:
```
Start consumers
status=received message_id=6860318059876990 function=my_task
test test1 test2
status=processed message_id=6860318059876990 function=my_task result=ok execution_time=6.818771362304688e-05
```

### Configuration

Configuration can be done using keyword arguments in class instantiation and/or flask environment variable (set with `config.update`).
If both method used for one configuration key, the class instanciation is primary.

| Flask env variable | Keyword argument | Usage | How-to get? |
|-|-|-|-|
| `PUBSUB_PROJECT_ID` | `project_id` | GCP project ID | See [console.cloud.google.com](https://console.cloud.google.com/) |
| `PUBSUB_CREDENTIALS_JSON` | `gcp_credentials_json` | Service account credentials, as JSON string format | See IAM in [console.cloud.google.com](https://console.cloud.google.com/) |
| `PUBSUB_CREDENTIALS_FILE` | `gcp_credentials_file` | Servicce account credentials, as JSON local file | See IAM in [console.cloud.google.com](https://console.cloud.google.com/) |
| `PUBSUB_CONCURRENT_CONSUMERS` | `concurrent_consumers` | Number of simultaneous consumer (default: `4`) | |
| `PUBSUB_CONCURRENT_MESSAGES` | `concurrent_messages` | Number of messages pull from topic per consumer per call (default: `2`) | |
| `PUBSUB_TOPIC_PREFIX` | `topic_prefix` | Prefix for all topic used in the instance, useful for feature branches using same project. | |


## 🔮 Roadmap

- [ ] Priority in the treatment of messages per functions
- [ ] Logging instead of print (+ option to format as JSON)
- [ ] Contributing manual
- [ ] Documentation about Flask configuration keys and their counterpart on PubSub direct call

### TO BE CONFIRMED

- [ ] Region selection (default: all regions) - can be edited in Storage Rules of Topic for the moment
