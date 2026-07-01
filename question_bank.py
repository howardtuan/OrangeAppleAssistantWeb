import json
import random
import sys
from pathlib import Path


QUESTION_BANK_FILE = "question_bank.json"


def resolve_question_bank_path(file_path=QUESTION_BANK_FILE):
    path = Path(file_path)
    if path.is_absolute():
        return path

    editable_path = Path.cwd() / path
    if editable_path.exists():
        return editable_path

    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_dir / path


def load_question_bank(file_path=QUESTION_BANK_FILE):
    path = resolve_question_bank_path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到題庫檔案：{path}")

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"題庫 JSON 格式錯誤：{exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValueError("題庫根層級必須是物件，格式為：課程 -> 課次 -> 題目清單。")

    return data


def get_lesson_questions(course_code, lesson_code, file_path=QUESTION_BANK_FILE):
    bank = load_question_bank(file_path)
    course_questions = bank.get(course_code)
    if not isinstance(course_questions, dict):
        raise ValueError(f"題庫找不到課程：{course_code}")

    lesson_questions = course_questions.get(lesson_code)
    if not isinstance(lesson_questions, list):
        raise ValueError(f"題庫找不到 {course_code} {lesson_code} 的題目清單。")

    return [str(question).strip() for question in lesson_questions if str(question).strip()]


def draw_lesson_questions(course_code, lesson_code, count=3):
    questions = get_lesson_questions(course_code, lesson_code)
    if len(questions) < count:
        raise ValueError(
            f"{course_code} {lesson_code} 至少需要 {count} 題可抽，目前只有 {len(questions)} 題。"
        )

    return random.sample(questions, count)


def format_numbered_questions(questions):
    return "\n".join(f"{index}.{question}" for index, question in enumerate(questions, start=1))
