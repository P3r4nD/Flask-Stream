# Flask-Stream change log

## Release 1.2.1 - 2026-04-14
- SSHDownloadProvider must extend BaseProvider to be able to correctly propagate all events. Fixes [#1](https://github.com/P3r4nD/Flask-Stream/issues/1)
- Differentiate the scop in the on_done event
- 
## Release 1.1 - 2026-04-10

### New: CustomSyncProvider

A sample CustomSyncProvider is included directly in flask_stream.providers.custom_sync, designed as a learning reference for developers who want to extend flask-stream with custom business logic.

Key features:

- Full implementation of all lifecycle hooks (on_start, on_batch, on_file, on_progress, on_file_done, on_done).

- SSE event emission using the standard ProviderEvent type, compatible with the existing UI.
