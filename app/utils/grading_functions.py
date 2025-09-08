# app/utils/grading_functions.py
def _compare_generic(student_fields: dict, answer_key: dict):
    score = 0
    total = 0
    incorrect = []
    lines = []

    for k, expected in (answer_key or {}).items():
        total += 1
        got = str(student_fields.get(k, "")).strip().lower()
        exp = str(expected).strip().lower()
        if got == exp and got != "":
            score += 1
        else:
            incorrect.append(k)
            lines.append(f"❌ {k}: expected '{expected}', got '{student_fields.get(k, '')}'")

    lines.append(f"\n✅ Score: {score} / {total}")
    return {
        "score": score,
        "total": total,
        "feedback": "\n".join(lines) if lines else "No differences found.",
        "incorrect_fields": incorrect,
    }

def compare_fields_n400(student_fields, answer_key_json):
    return _compare_generic(student_fields, answer_key_json)

def compare_fields_i765(student_fields, answer_key_json):
    return _compare_generic(student_fields, answer_key_json)

def compare_fields_i130a(student_fields, answer_key_json):
    return _compare_generic(student_fields, answer_key_json)
