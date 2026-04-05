# Flask-Stream

[![PyPI](https://img.shields.io/pypi/v/flask-stream?cache_bust=1&cacheSeconds=20)](https://pypi.org/project/flask-stream/)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![CI](https://github.com/P3r4nD/flask-stream/actions/workflows/python-publish.yml/badge.svg?branch=main)

**Flask-Stream** is a Flask 3 extension that enables real-time streaming of file downloads from one or multiple remote servers directly in your web application's UI. It is designed to be easy to integrate, flexible, and extensible for future types of streams.

---

## Features

1. **SSH File Downloads**
   - Connect to remote servers via SSH key authentication.
   - Recursive file listing on remote servers.
   - Real-time file download progress updates.

2. **Multiple Servers Support**
   - Configure one or multiple servers in the Flask app.
   - Each server can have its own `remote_base` and download folder.
   - The UI clearly differentiates which server each file comes from.

3. **Smart Progress Bars**
   - **Individual file progress:** shows percentage and downloaded size (MB).
   - **Total progress:** tracks the progress over all files in the job.
   - For multiple simultaneous downloads, each active file has its own progress bar and filename.

4. **Parallel Downloads (Optional)**
   - Controlled via `STREAM_BULK_DOWNLOAD` and `STREAM_MAX_SIMULTANEOUS`.
   - Downloads multiple files at once respecting the concurrency limit.
   - Useful for large datasets or multiple servers.

5. **Ready-to-use HTML/JavaScript UI**
   - Includable download button via `{{ stream_button() }}`.
   - Tailwind, Bootstrap5 and custom UI template
   - Shows logs, errors, and dynamic progress using Server-Sent Events (SSE).
   - Fully compatible with Bootstrap 5 for responsive styling.

6. **Extensible Architecture**
   - Implements a `StreamProvider` base, enabling future stream types (HTTP, FTP, S3, etc.).
   - Supports `init_app()` pattern for multiple Flask apps in the same process.

7. **Asynchronous Job Management**
   - Each download job runs in a separate thread.
   - Event queues per job enable real-time UI updates and multiple concurrent jobs.

8. **Error Handling**
   - Stream errors reported in UI.
   - Disconnects from server or app are shown as "Server or App disconnected".

9. **Centralized Configuration**
   - Configure all parameters via `app.config` or a central config file.
   - Main configuration variables:
     ```python
     STREAM_PROVIDER          # Currently "ssh"
     STREAM_SERVERS           # List of servers with host, user, key, remote_base, name
     STREAM_DOWNLOAD_DIR      # Local download directory
     STREAM_BULK_DOWNLOAD     # Enable parallel downloads
     STREAM_MAX_SIMULTANEOUS  # Max simultaneous downloads
     ```

10. **Integrated Tests**
    - Unit tests with **pytest** covering routes, events, and basic functionality.
    - Installable in editable mode with `pip install -e .[dev]`.

---

## Installation

```bash
# Clone repository
git clone https://github.com/P3r4nD/flask-stream.git
cd flask-stream

# Install with dev dependencies
pip install -e .[dev]

# Or from PyPI
pip install flask-stream
```



## Basic usage

```python

from flask import Flask
from flask_stream import Stream

app = Flask(__name__)
app.config.update({
    "STREAM_SERVERS": [
        {"name": "server1", "host": "example.com", "user": "ubuntu", "key": "~/.ssh/id_rsa", "remote_base": "logs"},
        {"name": "server2", "host": "example2.com", "user": "ubuntu", "key": "~/.ssh/id_rsa", "remote_base": "logs"}
    ],
    "STREAM_DOWNLOAD_DIR": "downloads",
    "STREAM_BULK_DOWNLOAD": True,
    "STREAM_MAX_SIMULTANEOUS": 2
})

stream = Stream(app)

@app.route("/")
def index():
    return """
    <h3>Download Logs</h3>
    {{ stream_button() }}
    """
```
