from flask import Flask
from flask_stream import Stream


def test_init_app():

    app = Flask(__name__)

    stream = Stream()
    stream.init_app(app)

    # the extension is registered
    assert "stream" in app.extensions


def test_blueprint_registered():

    app = Flask(__name__)
    Stream(app)

    assert "stream" in app.blueprints


def test_stream_button_context():

    app = Flask(__name__)
    Stream(app)

    with app.app_context():

        # the context processor should expose stream_button
        ctx = app.template_context_processors[None]

        found = False

        for processor in ctx:
            result = processor()
            if "stream_button" in result:
                found = True
                break

        assert found
