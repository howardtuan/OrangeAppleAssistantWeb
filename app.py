import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from ai_client import configured_providers, polish_contact_book
from contact_book import (
    compose_contact_book,
    ensure_current_questions,
    restore_previous_opening,
)
from course_data import (
    DISPLAY_COURSE_OPTIONS,
    LESSON_OPTIONS,
    get_previous_lesson_code,
    list_courses,
)
from question_bank import draw_lesson_questions, format_numbered_questions


load_dotenv()

app = Flask(__name__)
app.json.ensure_ascii = False


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/courses")
def courses():
    return jsonify(
        {
            "courses": list_courses(),
            "lessonOptions": LESSON_OPTIONS,
            "displayCourseOptions": DISPLAY_COURSE_OPTIONS,
            "defaults": {
                "courseCode": "Scratch1",
                "lessonCode": "L2",
                "displayCourse": "(原始課名)",
                "displayLesson": "2",
                "schedule": "fixed",
                "hasPrevious": False,
                "useAI": True,
            },
            "providers": configured_providers(),
        }
    )


@app.get("/api/questions")
def questions():
    course_code = request.args.get("course", "Scratch1").strip()
    lesson_code = request.args.get("lesson", "L2").strip()

    try:
        drawn = draw_lesson_questions(course_code, lesson_code)
    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"questions": drawn, "formatted": format_numbered_questions(drawn)})


@app.get("/api/previous-lesson")
def previous_lesson():
    lesson_code = request.args.get("lesson", "L2").strip()
    return jsonify({"lessonCode": get_previous_lesson_code(lesson_code)})


@app.post("/api/generate")
def generate():
    payload = request.get_json(silent=True) or {}
    composed = compose_contact_book(payload)
    output = composed["draft"]
    ai_meta = None

    if composed["useAI"]:
        try:
            ai_meta = polish_contact_book(output)
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 502

        output = restore_previous_opening(
            ai_meta["output"],
            composed["opening"],
            composed["hasPrevious"],
        )

    output = ensure_current_questions(output, composed["questions"])

    return jsonify(
        {
            "output": output,
            "ai": ai_meta,
        }
    )


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "providers": configured_providers()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)
