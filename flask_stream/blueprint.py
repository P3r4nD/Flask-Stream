from flask import Blueprint, Response, current_app, jsonify
import json
import threading
from .jobs import create_job, jobs

bp = Blueprint(
    "stream",
    __name__,
    url_prefix="/stream",
    template_folder="templates",
    static_folder="static"
)


@bp.route("/start", methods=["POST"])
def start():
    job_id = create_job()

    provider_name = current_app.config["STREAM_PROVIDER"]
    # use the app.extensions manager
    provider = current_app.extensions["stream"].manager.get(provider_name)

    thread = threading.Thread(
        target=provider.run,
        args=(current_app._get_current_object(), job_id),
        daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id})


@bp.route("/events/<job_id>")
def events(job_id):
    def generator():
        q = jobs[job_id]["queue"]
        while True:
            item = q.get()
            yield f"event: {item['event']}\n"
            yield f"data: {json.dumps(item['data'])}\n\n"
            if jobs[job_id]["done"] and q.empty():
                break
    return Response(generator(), mimetype="text/event-stream")
