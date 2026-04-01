import uuid
from queue import Queue

jobs = {}

def create_job():

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "queue": Queue(),
        "done": False
    }

    return job_id

def push_event(job_id, event, data):

    jobs[job_id]["queue"].put({
        "event": event,
        "data": data
    })

def finish_job(job_id):

    jobs[job_id]["done"] = True
