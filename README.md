# Flask GCP Pub/Sub

Lite distributed task queue using GCP Pub/Sub

[![GNU GPLv3](https://img.shields.io/github/license/wildsys/flask-pubsub)](https://www.gnu.org/licenses/gpl-3.0.html) [![PyPI version](https://img.shields.io/pypi/v/flask-gcp-pubsub)](https://github.com/raicheff/flask-gcp-pubsub)

<!-- TOC depthfrom:2 -->

- [🤔 What does this package does?](#-what-does-this-package-does)
- [🚀 Getting started](#-getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Full example](#full-example)
- [🔮 Roadmap](#-roadmap)
    - [TO BE CONFIRMED](#to-be-confirmed)

<!-- /TOC -->

## 🤔 What does this package does?

As Celery, but in a lighter version, this package allows you to run operations asynchronously in your Flask project, but without the choice of the broker: it only uses GCP Pub/Sub.

Technically, this package can run without Flask, but, historically, it comes to have a quick-win for migrating to GCP Cloud Run using the Pub/Sub system, from an existing project using Flask + Celery.

This package aims to remove some painful useless tasks by:
- Creating one dedicated topic for each function
- Creating one dedicated subscription for each function

We **do not recommand** this package for the following cases:
- You need to reuse your development in a multi-cloud context
- You have high volume of messages to process (not tested)

This package is given "as it", without garantees, under the GPLv3 License.

## 🚀 Getting started

### Prerequisites

- A [Google Cloud account](https://console.cloud.google.com/)
- A GCP project ([here to create a new one](https://console.cloud.google.com/projectcreate)), with [Pub/Sub API enabled](https://console.cloud.google.com/apis/library/pubsub.googleapis.com) (take care to select the good one)
- A local environment with Python >= 3.8

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

**WARNING**: do not forget to replace `<project_id>` with you GCP project ID (not number).

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

## 🔮 Roadmap

- [ ] Priority in the treatment of messages per functions
- [ ] Logging instead of print (+ option to format as JSON)

### TO BE CONFIRMED

- [ ] Region selection (default: all regions) - can be edited in Storage Rules of Topic for the moment
