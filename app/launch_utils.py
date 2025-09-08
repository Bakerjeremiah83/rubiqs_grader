# app/launch_utils.py
# Replace with your real lookup that pulls assignments from Supabase.
# For now, a safe default so routes won't crash.
def load_assignment_config(assignment_title: str):
    # Return a dict with keys your grader expects. You can fill from DB later.
    return {
        "total_points": 100,
        "gpt_model": "gpt-4",   # or "json" for NoMas mode
        "delay_posting": "immediate",
        "feedback_tone": "supportive",
        "grading_difficulty": "balanced",
        "student_level": "college",
        "rubric_file": "",      # supply a URL if you have one
        "ai_notes": "",
    }
