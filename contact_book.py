from course_data import get_course_details, get_lesson_topic


def build_contact_book(
    name,
    course_name,
    lesson_number,
    lesson_topic,
    schedule_text,
    performance,
    questions,
):
    performance_text = performance if performance else "未提供"
    questions_text = questions if questions else "未提供"

    return (
        f"{name}今天在{course_name}完成第 {lesson_number} 課〈{lesson_topic}〉。"
        f"本堂課內容是{lesson_topic}。"
        f"{name}上課表現：{performance_text}。"
        f"進度狀態：{schedule_text}。"
        "\n\n"
        f"本堂課驗收問題：【{questions_text}】。"
    )


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _resolve_display_lesson(display_lesson, lesson_code):
    value = _clean_text(display_lesson)
    if value.isdigit():
        number = int(value)
        if 1 <= number <= 45:
            return number

    if lesson_code and lesson_code.startswith("L") and lesson_code[1:].isdigit():
        return int(lesson_code[1:])

    return 1


def compose_contact_book(payload):
    name = _clean_text(payload.get("name")) or "學生"
    course_code = _clean_text(payload.get("courseCode")) or "Scratch1"
    lesson_code = _clean_text(payload.get("lessonCode")) or "L2"
    display_course = _clean_text(payload.get("displayCourse")) or "(原始課名)"
    display_lesson = _clean_text(payload.get("displayLesson"))
    schedule = _clean_text(payload.get("schedule")) or "fixed"
    performance = _clean_text(payload.get("performance"))
    questions = _clean_text(payload.get("questions"))
    previous_questions = _clean_text(payload.get("previousQuestions"))
    has_previous = bool(payload.get("hasPrevious"))

    course_name, _lesson_list = get_course_details(course_code)
    lesson_topic = get_lesson_topic(course_code, lesson_code)
    schedule_text = "進度正常" if schedule == "fixed" else "進度落後"

    if display_course and display_course != "(原始課名)":
        output_course_name = display_course
    else:
        output_course_name = course_name

    display_number = _resolve_display_lesson(display_lesson, lesson_code)

    contact_body = build_contact_book(
        name,
        output_course_name,
        display_number,
        lesson_topic,
        schedule_text,
        performance,
        questions,
    )

    previous_text = " ".join(previous_questions.split()) if previous_questions else "未提供"
    opening = ""
    if has_previous:
        opening = f"已完成上週內容，驗收問題為：【{previous_text}】。\n\n"

    return {
        "draft": opening + contact_body,
        "opening": opening,
        "hasPrevious": has_previous,
        "questions": questions,
        "useAI": bool(payload.get("useAI")),
    }


def restore_previous_opening(output, opening, has_previous):
    if not has_previous:
        return output

    marker = "已完成上週內容，驗收問題為：【"
    cleaned = output.lstrip()
    if marker in cleaned:
        idx = cleaned.find(marker)
        cleaned = cleaned[idx + len(marker) :]
        end_idx = cleaned.find("】")
        if end_idx != -1:
            cleaned = cleaned[end_idx + 1 :].lstrip("。\n ")

    return opening + cleaned


def ensure_current_questions(output, questions):
    if "本堂課驗收問題" in output:
        return output

    questions_fallback = questions if questions else "未提供"
    return output.rstrip() + f"\n\n本堂課驗收問題：【{questions_fallback}】。"
