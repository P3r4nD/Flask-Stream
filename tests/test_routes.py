# tests/test_routes.py
import time
import json
import pytest
from flask import Flask
from flask_stream import Stream
from flask_stream.jobs import jobs

# ---------- Dummy provider for testing ----------
class DummyProvider:
    """Simulate downloads without SSHing"""
    def run(self, app, job_id):
        # We simulated 3 files of different sizes.
        files = [
            {"file": "file1.txt", "size": 1000, "server": "dummy1"},
            {"file": "file2.txt", "size": 2000, "server": "dummy1"},
            {"file": "file3.txt", "size": 1500, "server": "dummy1"},
        ]

        # sent the Batch event
        app.logger.debug("DummyProvider: starting run")
        from flask_stream.jobs import push_event, finish_job
        push_event(job_id, "Batch", {"server": "dummy1", "total": len(files)})

        for f in files:
            push_event(job_id, "File", f)
            # simulate progress
            for p in range(0, 101, 25):
                push_event(job_id, "Progress", {"percent": p, **f})
            push_event(job_id, "FileDone", f)

        push_event(job_id, "done", {})
        finish_job(job_id)


# ---------- Fixture for the app ----------
@pytest.fixture
def app():
    app = Flask(__name__)
    stream_ext = Stream(app)

    # We registered DummyProvider in the app manager
    stream_ext.manager.providers["dummy"] = DummyProvider()
    app.config["STREAM_PROVIDER"] = "dummy"

    yield app


# ---------- Test /stream/start ----------
def test_start_route(app):
    client = app.test_client()
    r = client.post("/stream/start")
    assert r.status_code == 200
    data = r.get_json()
    assert "job_id" in data
    job_id = data["job_id"]
    assert job_id in jobs


# ---------- Test /stream/events/<job_id> ----------
def test_events_stream(app):
    client = app.test_client()
    r = client.post("/stream/start")
    job_id = r.get_json()["job_id"]

    # consume the event stream
    r2 = client.get(f"/stream/events/{job_id}", buffered=True)
    assert r2.status_code == 200
    data = r2.data.decode("utf-8")

    # verify that some Dummy events were received
    assert "event: File" in data
    assert "event: Progress" in data
    assert "event: FileDone" in data
    assert "event: done" in data
