from flask import render_template
from markupsafe import Markup
from .config import DefaultConfig
from .manager import StreamManager
from .blueprint import bp
from .i18n import load_translations

class Stream:

    def __init__(self, app=None):

        self.manager = StreamManager()

        if app:
            self.init_app(app)

    def init_app(self, app):

        for k, v in DefaultConfig.__dict__.items():
            if k.isupper():
                app.config.setdefault(k, v)

        app.extensions["stream"] = self

        lang = app.config.get("STREAM_LANG", "en")
        translations = load_translations(lang)

        app.register_blueprint(bp)

        app.context_processor(lambda: {
            "stream_button": self.button,
            "stream_config": {
                "bulk": app.config["STREAM_BULK_DOWNLOAD"],
                "max_simultaneous": app.config["STREAM_MAX_SIMULTANEOUS"],
                "max_reconnect": app.config["STREAM_MAX_RECONNECT_ATTEMPTS"]
            },
            "stream_i18n": translations
        })

    def button(self):
        return Markup(render_template("stream_button.html"))
