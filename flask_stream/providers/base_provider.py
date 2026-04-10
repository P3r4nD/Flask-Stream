# flask_stream/providers/base_provider.py

class BaseProvider:
    """
    Base provider class for business logic extensions.
    Defines the lifecycle hooks but does not implement any behavior.
    """

    def on_start(self, app, job_id, server):
        """Called before processing a server."""
        pass

    def on_batch(self, app, job_id, server, files, base, download_dir):
        """Called after listing all files."""
        pass

    def on_file(self, app, job_id, server, rel, remote_path, local_path, size):
        """Called before downloading a file."""
        pass

    def on_progress(self, app, job_id, server, rel, local_path, percent):
        """Called during file download."""
        pass

    def on_file_done(self, app, job_id, server, rel, local_path):
        """Called after a file is downloaded."""
        pass

    def on_done(self, app, job_id, servers):
        """Called after all servers are processed."""
        pass
