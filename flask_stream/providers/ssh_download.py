# flask_stream/providers/ssh_download.py

import os
import stat
import time
import queue
import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..jobs import push_event, finish_job
from .base_provider import BaseProvider


class SSHDownloadProvider(BaseProvider):
    """
    Core download provider for flask-stream.

    - Inherits from BaseProvider to be consistent with the other providers.
    - Triggers business hooks (on_start, on_batch, on_file, on_progress, on_file_done, on_done) on the STREAM_BUSINESS_PROVIDERS.
    """

    def connect(self, server):
        """Create and return a Paramiko SSH client."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
            server["host"],
            port=server.get("port", 22),
            username=server["user"],
            key_filename=os.path.expanduser(server["key"])
        )

        return client

    def _get_business_providers(self, app):
        """
        Return business providers only if enabled.
        """
        if not app.config.get("STREAM_BUSINESS_ENABLED", False):
            return []
        return app.config.get("STREAM_BUSINESS_PROVIDERS", [])

    def is_dir(self, entry):
        """Check if an SFTP entry is a directory."""
        return stat.S_ISDIR(entry.st_mode)

    def list_recursive(self, sftp, base):
        """Recursively list files from a remote base directory."""
        files = []

        def walk(path, prefix=""):
            for entry in sftp.listdir_attr(path):
                name = entry.filename

                if name in (".", ".."):
                    continue

                full = f"{path}/{name}"
                rel = f"{prefix}{name}"

                if self.is_dir(entry):
                    walk(full, rel + "/")
                else:
                    files.append(rel)

        walk(base)
        return files

    # -------------------------
    # Provider event dispatch (main thread)
    # -------------------------
    def _dispatch_provider_event(self, app, job_id, event_name, payload):
        for p in self._get_business_providers(app):
            if hasattr(p, event_name):
                try:
                    getattr(p, event_name)(app, job_id, **payload)
                except Exception as e:
                    # We don't let this kill run_server
                    push_event(job_id, "debug", {
                        "msg": f"Provider error in {event_name}: {e}",
                        "provider": getattr(p, "provider_name", type(p).__name__),
                    })

    # -------------------------
    # File download (worker threads)
    # -------------------------
    def download_file(self, app, job_id, server, rel, base, download_dir, provider_queue):
        """
        Download a file in a thread worker.

        - Business hooks are queued in the provider_queue.
        - Push_events are emitted directly.
        """
        client = self.connect(server)
        sftp = client.open_sftp()

        try:
            remote_path = f"{base}/{rel}"
            local_path = os.path.join(download_dir, str(server["id"]), rel)

            statinfo = sftp.stat(remote_path)
            size = statinfo.st_size

            if os.path.exists(local_path):

                local_size = os.path.getsize(local_path)

                if local_size == size:
                    # Provider: on_file
                    provider_queue.put((
                        "on_file",
                        {
                            "server": server,
                            "rel": rel,
                            "remote_path": remote_path,
                            "local_path": local_path,
                            "size": size,
                        },
                    ))

                    # SSE: File
                    push_event(job_id, "File", {
                        "server": server["id"],
                        "name": server["name"],
                        "file": rel,
                        "size": size
                    })

                    # SSE: Progress 100%
                    push_event(job_id, "Progress", {
                        "percent": 100,
                        "file": rel,
                        "server": server["id"]
                    })
                    # Provider: on_file_done
                    provider_queue.put((
                        "on_file_done",
                        {
                            "server": server,
                            "rel": rel,
                            "local_path": local_path,
                        },
                    ))

                    # SSE: FileDone
                    push_event(job_id, "FileDone", {
                        "file": rel,
                        "server": server["id"]
                    })

                    return
            # Provider: on_file (in queue)
            provider_queue.put((
                "on_file",
                {
                    "server": server,
                    "rel": rel,
                    "remote_path": remote_path,
                    "local_path": local_path,
                    "size": size,
                },
            ))

            # SSE: File
            push_event(job_id, "File", {
                "server": server["id"],
                "name": server["name"],
                "file": rel,
                "size": size
            })

            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            with sftp.open(remote_path, "rb") as remote_file, open(local_path, "wb") as f:
                downloaded = 0
                chunk = 32768

                while True:
                    data = remote_file.read(chunk)
                    if not data:
                        break

                    f.write(data)
                    downloaded += len(data)

                    percent = int(downloaded / size * 100)

                    # Provider: on_progress (in queue)
                    provider_queue.put((
                        "on_progress",
                        {
                            "server": server,
                            "rel": rel,
                            "local_path": local_path,
                            "percent": percent,
                        },
                    ))

                    # SSE: Progress
                    push_event(job_id, "Progress", {
                        "percent": percent,
                        "file": rel,
                        "server": server["id"]
                    })

            # Provider: on_file_done (in queue)
            provider_queue.put((
                "on_file_done",
                {
                    "server": server,
                    "rel": rel,
                    "local_path": local_path,
                },
            ))

            # SSE: FileDone
            push_event(job_id, "FileDone", {
                "file": rel,
                "server": server["id"]
            })

        finally:
            sftp.close()
            client.close()

    # -------------------------
    # Per-server run
    # -------------------------
    def run_server(self, app, job_id, server):
        download_dir = app.config["STREAM_DOWNLOAD_DIR"]
        bulk = app.config.get("STREAM_BULK_DOWNLOAD", False)
        max_sim = app.config.get("STREAM_MAX_SIMULTANEOUS", 2)

        provider_queue = queue.Queue()

        # Provider: on_start (in run_server thread)
        self._dispatch_provider_event(app, job_id, "on_start", {
            "server": server
        })

        # SSE: debug
        push_event(job_id, "debug", {
            "msg": f"Connecting {server['name']}",
            "server": server["id"],
            "name": server["name"]
        })

        base = server["remote_base"]

        # List files recursively
        client = self.connect(server)
        sftp = client.open_sftp()
        files = self.list_recursive(sftp, base)
        sftp.close()
        client.close()

        total_files = len(files)

        # Provider: on_batch (in run_server thread)
        self._dispatch_provider_event(app, job_id, "on_batch", {
            "server": server,
            "files": files,
            "base": base,
            "download_dir": download_dir
        })

        # SSE: Batch + debug
        push_event(job_id, "Batch", {
            "server": server["id"],
            "name": server["name"],
            "total": total_files
        })
        push_event(job_id, "debug", {
            "msg": f"{total_files} files found",
            "server": server["id"],
            "name": server["name"]
        })

        # Download files
        if bulk:
            futures = []
            with ThreadPoolExecutor(max_workers=max_sim) as executor:
                for rel in files:
                    futures.append(
                        executor.submit(
                            self.download_file,
                            app,
                            job_id,
                            server,
                            rel,
                            base,
                            download_dir,
                            provider_queue,
                        )
                    )

                while True:
                    # Drain queue (multiple events per iteration to prevent accumulation)
                    for _ in range(100):
                        if provider_queue.empty():
                            break
                        event_name, payload = provider_queue.get()
                        self._dispatch_provider_event(app, job_id, event_name, payload)

                    # If any workers remain alive
                    any_running = any(not f.done() for f in futures)

                    # Exit condition: no one alive + empty queue
                    if not any_running and provider_queue.empty():
                        break

                    time.sleep(0.01)
        else:
            # Sequential, but also using the tail to unify the model
            for rel in files:
                self.download_file(
                    app,
                    job_id,
                    server,
                    rel,
                    base,
                    download_dir,
                    provider_queue,
                )
                while not provider_queue.empty():
                    event_name, payload = provider_queue.get()
                    self._dispatch_provider_event(app, job_id, event_name, payload)

        # Provider: on_done (per server, in run_server thread)
        self._dispatch_provider_event(app, job_id, "on_done", {
            "servers": [server],
            "scope": "server"
        })

    # -------------------------
    # Global run
    # -------------------------
    def run(self, app, job_id):
        servers = app.config["STREAM_SERVERS"]

        strategy = app.config.get("STREAM_SERVER_STRATEGY", "sequential")
        max_servers = app.config.get("STREAM_MAX_SERVERS", len(servers))

        if strategy == "sequential":
            for server in servers:
                self.run_server(app, job_id, server)

        elif strategy == "parallel":
            with ThreadPoolExecutor(max_workers=max_servers) as executor:
                futures = [
                    executor.submit(self.run_server, app, job_id, server)
                    for server in servers
                ]
                for _ in as_completed(futures):
                    pass
        else:
            for server in servers:
                self.run_server(app, job_id, server)

        # Provider: on_done global
        for p in self._get_business_providers(app):
            if hasattr(p, "on_done"):
                p.on_done(app, job_id, servers, scope="global")

        # SSE: done
        push_event(job_id, "done", {})
        finish_job(job_id)
