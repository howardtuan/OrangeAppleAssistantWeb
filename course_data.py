from collections import OrderedDict

import db


COURSE_MAPPING = OrderedDict(
    [
        ("Scratch0", ("Scratch 入門", db.Scratch0)),
        ("Scratch1", ("Scratch 進階", db.Scratch1)),
        ("Python", ("Python 基礎", db.Python)),
        ("Python2", ("Python 進階", db.Python2)),
        ("JavaScript", ("JavaScript 基礎", db.JavaScript)),
        ("JavaScript_New", ("JavaScript 進階", db.JavaScript_New)),
        ("HTML", ("HTML5 基礎", db.HTML)),
        ("DB", ("資料庫與 SQL", db.DB)),
        ("Algorithm", ("演算法與邏輯", db.Algorithm)),
        ("AI", ("AI 基礎", db.AI)),
    ]
)

DISPLAY_COURSE_OPTIONS = ["(原始課名)", "線上菁英初階", "線上菁英中階", "線上菁英高階"]
LESSON_OPTIONS = [f"L{i}" for i in range(1, 16)]


def get_course_details(course_code):
    return COURSE_MAPPING.get(course_code, ("未知課程", []))


def get_lesson_topic(course_code, lesson_code):
    _course_name, lesson_list = get_course_details(course_code)
    lesson_index = 0

    if lesson_code and lesson_code.startswith("L") and lesson_code[1:].isdigit():
        lesson_index = int(lesson_code[1:]) - 1

    if 0 <= lesson_index < len(lesson_list):
        return lesson_list[lesson_index]

    return "（未找到課程內容）"


def list_courses():
    courses = []
    for code, (name, lessons) in COURSE_MAPPING.items():
        courses.append(
            {
                "code": code,
                "name": name,
                "lessons": [
                    {"code": f"L{index}", "topic": topic}
                    for index, topic in enumerate(lessons, start=1)
                ],
            }
        )
    return courses


def get_previous_lesson_code(lesson_code):
    if lesson_code and lesson_code.startswith("L") and lesson_code[1:].isdigit():
        previous_number = max(1, int(lesson_code[1:]) - 1)
        return f"L{previous_number}"
    return lesson_code
