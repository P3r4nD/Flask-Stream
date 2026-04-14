from flask import render_template
from markupsafe import Markup
from .config import DefaultConfig
from flask import current_app
from .manager import StreamManager
from .blueprint import bp
from .i18n import load_translations
import json

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

        servers = app.config.get("STREAM_SERVERS", [])

        app.config["STREAM_SERVERS"] = self._normalize_servers(servers)

        lang = app.config.get("STREAM_LANG", "en")
        translations = load_translations(lang)

        app.stream_i18n = translations

        app.register_blueprint(bp)

        app.context_processor(lambda: {
            "stream": self,
            "stream_button": self.button,
            "stream_config": {
                "ui_framework": app.config["STREAM_UI_FRAMEWORK"],
                "bulk": app.config["STREAM_BULK_DOWNLOAD"],
                "max_simultaneous": app.config["STREAM_MAX_SIMULTANEOUS"],
                "max_reconnect": app.config["STREAM_MAX_RECONNECT_ATTEMPTS"]
            },
            "stream_i18n": translations
        })

    def _normalize_servers(self, servers):

        normalized = []

        for i, server in enumerate(servers, start=1):

            s = dict(server)

            # Auto id
            if "id" not in s:
                s["id"] = i

            # Default name
            if "name" not in s:
                s["name"] = f"server-{s['id']}"

            normalized.append(s)

        return normalized

    def button(self):

        # custom override
        custom_template = current_app.config.get("STREAM_UI_TEMPLATE")

        if custom_template:
            return Markup(render_template(custom_template))

        framework = current_app.config.get(
            "STREAM_UI_FRAMEWORK",
            "bootstrap5"
        ).lower()

        template = f"{framework}/stream_button.html"

        return Markup(render_template(template))


    def stream_scripts(self, config=None, i18n=None):
        """
        Returns the scripts and global configuration for the extension.
        Allows you to overwrite the configuration or translations if desired.
        """
        from flask import url_for
        from markupsafe import Markup

        # Usamos config/i18n pasado o el del contexto global
        cfg = config or getattr(current_app, "stream_config", {
            "ui_framework": current_app.config.get("STREAM_UI_FRAMEWORK"),
            "bulk": current_app.config.get("STREAM_BULK_DOWNLOAD"),
            "max_simultaneous": current_app.config.get("STREAM_MAX_SIMULTANEOUS"),
            "max_reconnect": current_app.config.get("STREAM_MAX_RECONNECT_ATTEMPTS")
        })

        translations = i18n or getattr(current_app, "stream_i18n", {})

        framework = cfg.get("ui_framework", "bootstrap5").lower()

        cfg_json = json.dumps(cfg)
        i18n_json = json.dumps(translations)

        html = f"""
            <script>
            window.STREAM_CONFIG = {cfg_json};
            window.STREAM_I18N = {i18n_json};
            </script>

            <script src="{url_for('stream.static', filename=f'ui/{framework}.js')}"></script>
            <script src="{url_for('stream.static', filename='stream.js')}"></script>
        """

        return Markup(html)
