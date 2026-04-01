import os
import stat
import paramiko
from concurrent.futures import ThreadPoolExecutor

from ..jobs import push_event, finish_job


class SSHDownloadProvider:

    def connect(self, server):

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
        return stat.S_ISDIR(entry.st_mode)

    def list_recursive(self, sftp, base):

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

    def run(self, app, job_id):

        download_dir = app.config["STREAM_DOWNLOAD_DIR"]
        servers = app.config["STREAM_SERVERS"]
        bulk = app.config.get("STREAM_BULK_DOWNLOAD", False)
        max_sim = app.config.get("STREAM_MAX_SIMULTANEOUS", 2)

        for server in servers:

            push_event(job_id, "debug", {
                "msg": f"Connecting {server['name']}",
                "server": server["name"]
            })

            base = server["remote_base"]

            # Creamos un client temporal solo para listar archivos
            client_list = self.connect(server)
            sftp_list = client_list.open_sftp()
            files = self.list_recursive(sftp_list, base)
            sftp_list.close()
            client_list.close()

            total_files = len(files)

            push_event(job_id, "Batch", {
                "server": server["name"],
                "total": total_files
            })

            push_event(job_id, "debug", {
                "msg": f"{len(files)} files found",
                "server": server["name"]
            })

            def download_file(rel):

                # Each worker creates their own connection
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

            # Bulk: parallel downloads
            if bulk:
                with ThreadPoolExecutor(max_workers=max_sim) as executor:
                    executor.map(download_file, files)
            else:
                # Sequential
                for f in files:
                    download_file(f)

        push_event(job_id, "done", {})
        finish_job(job_id)
