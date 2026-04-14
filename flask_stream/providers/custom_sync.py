# flask_stream/providers/custom_sync.py

from ..jobs import push_event
from .base_provider import BaseProvider


class CustomSyncProvider(BaseProvider):
    """
    Example provider used in the basic demo application.

    This provider does NOT implement any real business logic.
    It simply logs each lifecycle event so developers can see
    when and how providers are invoked by flask-stream.
    """

    def __init__(self, app):
        self.state = {}
        self.app = app
        self.prefix = self.__class__.__name__

    def _should_log(self, event_name):
        cfg = self.app.config.get("STREAM_BUSINESS_LOG_EVENTS", "all")

        if cfg == "all":
            return True

        if isinstance(cfg, (list, tuple, set)):
            return event_name in cfg

        return False

    def _log(self, job_id, server_id, msg, event_name):
        if not self._should_log(event_name):
            return

        push_event(job_id, "ProviderEvent", {
            "server": server_id,
            "msg": msg
        })

    def on_start(self, app, job_id, server):
        server_id = server["id"]
        self._log(job_id, server_id, f"[{self.prefix}] on_start: {server['name']}", "on_start")

    def on_batch(self, app, job_id, server, files, base, download_dir):
        server_id = server["id"]
        self._log(job_id, server_id, f"[{self.prefix}] on_batch: {len(files)} files found", "on_batch")

    def on_file(self, app, job_id, server, rel, remote_path, local_path, size):
        server_id = server["id"]
        self._log(job_id, server_id, f"[{self.prefix}] on_file: {rel} ({size} bytes)", "on_file")

    def on_progress(self, app, job_id, server, rel, local_path, percent):
        server_id = server["id"]
        self._log(job_id, server_id, f"[{self.prefix}] on_progress: {rel} {percent}%", "on_progress")

    def on_file_done(self, app, job_id, server, rel, local_path):
        server_id = server["id"]
        self._log(job_id, server_id, f"[{self.prefix}] on_file_done: {rel}", "on_file_done")

    def on_done(self, app, job_id, servers, scope="server"):
        for server in servers:
            server_id = server["id"]
            self._log(job_id, server_id, f"[{self.prefix}] on_done: ({scope}) all servers complete", "on_done")
