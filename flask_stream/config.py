class DefaultConfig:

    STREAM_PROVIDER = "ssh"

    STREAM_SERVER_STRATEGY = "sequential" # sequential or parallel

    STREAM_DOWNLOAD_DIR = "downloads"

    STREAM_BULK_DOWNLOAD = True
    STREAM_MAX_SIMULTANEOUS = 4

    STREAM_MAX_RECONNECT_ATTEMPTS = 5

    STREAM_SERVERS = []
    STREAM_MAX_SERVERS = 2
