class StreamManager:

    def __init__(self):

        from .providers.ssh_download import SSHDownloadProvider

        self.providers = {
            "ssh": SSHDownloadProvider()
        }

    def get(self, name):

        return self.providers[name]
