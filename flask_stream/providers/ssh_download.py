import os
import stat
import paramiko
from concurrent.futures import ThreadPoolExecutor

from ..jobs import push_event, finish_job


class SSHDownloadProvider:

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

    def download_file(self, app, job_id, server, rel, base, download_dir):
        """
        Download a single file from the remote server.

        Each worker creates its own SSH/SFTP connection
        to avoid thread-safety issues with Paramiko.
        """

        client = self.connect(server)
        sftp = client.open_sftp()

        try:

            remote_path = f"{base}/{rel}"
            local_path = os.path.join(download_dir, server["name"], rel)

            statinfo = sftp.stat(remote_path)
            size = statinfo.st_size

            push_event(job_id, "File", {
                "file": rel,
                "size": size,
                "server": server["name"]
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

                    push_event(job_id, "Progress", {
                        "percent": percent,
                        "file": rel,
                        "server": server["name"]
                    })

            push_event(job_id, "FileDone", {
                "file": rel,
                "server": server["name"]
            })

        finally:

            sftp.close()
            client.close()

    def run_server(self, app, job_id, server):
        """
        Handle download process for a single server.
        """

        download_dir = app.config["STREAM_DOWNLOAD_DIR"]
        bulk = app.config.get("STREAM_BULK_DOWNLOAD", False)
        max_sim = app.config.get("STREAM_MAX_SIMULTANEOUS", 2)

        push_event(job_id, "debug", {
            "msg": f"Connecting {server['name']}",
            "server": server["name"]
        })

        base = server["remote_base"]

        # List files using a temporary connection
        client = self.connect(server)
        sftp = client.open_sftp()

        files = self.list_recursive(sftp, base)

        sftp.close()
        client.close()

        total_files = len(files)

        push_event(job_id, "Batch", {
            "server": server["name"],
            "total": total_files
        })

        push_event(job_id, "debug", {
            "msg": f"{total_files} files found",
            "server": server["name"]
        })

        # Download files
        if bulk:

            # Parallel file downloads
            with ThreadPoolExecutor(max_workers=max_sim) as executor:

                for rel in files:

                    executor.submit(
                        self.download_file,
                        app,
                        job_id,
                        server,
                        rel,
                        base,
                        download_dir
                    )

        else:

            # Sequential downloads
            for rel in files:

                self.download_file(
                    app,
                    job_id,
                    server,
                    rel,
                    base,
                    download_dir
                )

    # Main entrypoint
    def run(self, app, job_id):
        """
        Main execution entrypoint.

        Supports sequential or parallel execution across servers.
        """

        servers = app.config["STREAM_SERVERS"]

        strategy = app.config.get(
            "STREAM_SERVER_STRATEGY",
            "sequential"
        )

        max_servers = app.config.get(
            "STREAM_MAX_SERVERS",
            len(servers)
        )

        # Sequential server execution (default)
        if strategy == "sequential":

            for server in servers:

                self.run_server(app, job_id, server)

        # Parallel server execution
        elif strategy == "parallel":

            with ThreadPoolExecutor(max_workers=max_servers) as executor:

                for server in servers:

                    executor.submit(
                        self.run_server,
                        app,
                        job_id,
                        server
                    )

        # Unknown strategy fallback
        else:

            for server in servers:

                self.run_server(app, job_id, server)

        # Signal completion

        push_event(job_id, "done", {})
        finish_job(job_id)
