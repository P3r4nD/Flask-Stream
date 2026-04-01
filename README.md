# Flask Stream

Extensión de Flask para descargas remotas y streaming de progreso vía SSE.

## Instalación

```bash
pip install flask-stream
```

## Basic usage
```python
from flask import Flask
from flask_stream import Stream

app = Flask(__name__)
stream = Stream(app)

# Configuración mínima
app.config["STREAM_SERVERS"] = [
    {"name": "server1", "host": "1.2.3.4", "user": "ubuntu", "key": "~/.ssh/id_rsa", "remote_base": "logs"}
]
```

### Template
```jinja
{{ stream_button() }}
```

