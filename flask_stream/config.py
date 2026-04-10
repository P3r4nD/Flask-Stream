class DefaultConfig:

    STREAM_PROVIDER = "ssh"

    STREAM_SERVER_STRATEGY = "parallel" # sequential or parallel

    STREAM_DOWNLOAD_DIR = "downloads"

    STREAM_BULK_DOWNLOAD = True
    STREAM_MAX_SIMULTANEOUS = 4

    STREAM_MAX_RECONNECT_ATTEMPTS = 5

    STREAM_SERVERS = []
    STREAM_MAX_SERVERS = 1

    # Default lang
    STREAM_LANG = "en"

    # UI framework | bootstrap5 | tailwind | custom
    STREAM_UI_FRAMEWORK = "tailwind"

    # optional custom template
    STREAM_UI_TEMPLATE = None

    # Support extensible business logic and inheritance from custom providers.
    STREAM_BUSINESS_ENABLED = False

    # ["on_start", "on_batch", "on_file", "on_progress", "on_file_done", "on_done"]
    STREAM_BUSINESS_LOG_EVENTS = "all"

    # Default SyncProvider //Flask-Stream/flask_stream/providers/custom_sync.py
    # STREAM_BUSINESS_PROVIDERS = [CustomSyncProvider(app)]
    STREAM_BUSINESS_PROVIDERS = []
