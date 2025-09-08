# app/storage.py
from datetime import datetime

def store_pending_feedback(assignment_title, student_id, feedback, score, release_time):
    # Minimal placeholder; write to your DB if needed.
    print("[store_pending_feedback]", {
        "assignment_title": assignment_title,
        "student_id": student_id,
        "feedback": feedback,
        "score": score,
        "release_time": release_time,
        "created_at": datetime.utcnow().isoformat()+"Z",
    })
