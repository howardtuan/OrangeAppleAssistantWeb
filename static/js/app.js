const els = {};
let courses = [];
let latestOutput = "";
let toastTimer = null;

function $(id) {
  return document.getElementById(id);
}

function bindElements() {
  [
    "providerStrip",
    "lessonPreviewLabel",
    "studentName",
    "courseCode",
    "lessonCode",
    "lessonPreview",
    "displayCourse",
    "displayLesson",
    "hasPrevious",
    "useAI",
    "drawCourseCode",
    "drawLessonCode",
    "standaloneQuestions",
    "drawStandaloneBtn",
    "pasteCurrentBtn",
    "pastePreviousBtn",
    "copyStandaloneBtn",
    "performance",
    "questions",
    "previousQuestions",
    "drawCurrentBtn",
    "drawPreviousBtn",
    "aiResultMeta",
    "resultBox",
    "generateBtn",
    "copyResultBtn",
    "toast",
  ].forEach((id) => {
    els[id] = $(id);
  });
}

function option(value, label = value) {
  const item = document.createElement("option");
  item.value = value;
  item.textContent = label;
  return item;
}

function setOptions(select, values, selectedValue) {
  select.replaceChildren(...values.map((item) => option(item.value ?? item, item.label ?? item)));
  if (selectedValue) {
    select.value = selectedValue;
  }
}

function showToast(message, type = "info") {
  window.clearTimeout(toastTimer);
  els.toast.textContent = message;
  els.toast.className = `toast show${type === "error" ? " error" : ""}`;
  toastTimer = window.setTimeout(() => {
    els.toast.className = "toast";
  }, 3200);
}

function selectedSchedule() {
  return document.querySelector('input[name="schedule"]:checked')?.value || "fixed";
}

function getCourse(code) {
  return courses.find((course) => course.code === code);
}

function syncLessonPreview() {
  const course = getCourse(els.courseCode.value);
  const lessonCode = els.lessonCode.value;
  const lesson = course?.lessons.find((item) => item.code === lessonCode);
  els.lessonPreviewLabel.textContent = lessonCode || "";
  els.lessonPreview.textContent = lesson?.topic || "（未找到課程內容）";
}

function syncDisplayLesson() {
  const lessonCode = els.lessonCode.value;
  if (lessonCode?.startsWith("L")) {
    els.displayLesson.value = lessonCode.slice(1);
  }
}

function previousLessonCode(lessonCode) {
  if (lessonCode?.startsWith("L")) {
    const number = Number.parseInt(lessonCode.slice(1), 10);
    if (Number.isFinite(number)) {
      return `L${Math.max(1, number - 1)}`;
    }
  }
  return lessonCode;
}

function renderProviderStrip(providers) {
  if (!providers?.length) {
    els.providerStrip.textContent = "";
    return;
  }

  els.providerStrip.replaceChildren(
    ...providers.map((provider) => {
      const pill = document.createElement("span");
      pill.className = `provider-pill ${provider.configured ? "ready" : "missing"}`;
      pill.textContent = `${provider.label}${provider.configured ? " 已設定" : " 未設定"}`;
      return pill;
    }),
  );
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

async function drawQuestions(courseCode, lessonCode, target, successText) {
  const query = new URLSearchParams({ course: courseCode, lesson: lessonCode });
  const data = await fetchJson(`/api/questions?${query.toString()}`);
  target.value = data.formatted;
  showToast(successText);
}

async function copyText(text, successText = "已複製到剪貼簿") {
  if (!text.trim()) {
    showToast("目前沒有可複製的內容", "error");
    return false;
  }

  try {
    await navigator.clipboard.writeText(text);
    showToast(successText);
    return true;
  } catch (_error) {
    showToast("瀏覽器暫時無法自動複製，請手動選取內容", "error");
    return false;
  }
}

function setLoading(button, isLoading, loadingText) {
  if (isLoading) {
    button.dataset.originalHtml = button.innerHTML;
    button.disabled = true;
    button.textContent = loadingText;
  } else {
    button.disabled = false;
    if (button.dataset.originalHtml) {
      button.innerHTML = button.dataset.originalHtml;
    }
  }
}

function generationPayload() {
  return {
    name: els.studentName.value,
    courseCode: els.courseCode.value,
    lessonCode: els.lessonCode.value,
    displayCourse: els.displayCourse.value,
    displayLesson: els.displayLesson.value,
    schedule: selectedSchedule(),
    hasPrevious: els.hasPrevious.checked,
    useAI: els.useAI.checked,
    performance: els.performance.value,
    questions: els.questions.value,
    previousQuestions: els.previousQuestions.value,
  };
}

function renderOutput(output, aiMeta) {
  latestOutput = output;
  els.resultBox.textContent = output;

  if (aiMeta?.providerLabel) {
    const fallbackCount = aiMeta.fallbackErrors?.length || 0;
    els.aiResultMeta.textContent = fallbackCount
      ? `${aiMeta.providerLabel} / ${aiMeta.model}（已 fallback）`
      : `${aiMeta.providerLabel} / ${aiMeta.model}`;
  } else {
    els.aiResultMeta.textContent = "未使用 AI";
  }
}

async function generateContactBook() {
  setLoading(els.generateBtn, true, "產生中");
  els.aiResultMeta.textContent = els.useAI.checked ? "AI 潤飾中" : "產生中";

  try {
    const data = await fetchJson("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(generationPayload()),
    });
    renderOutput(data.output, data.ai);
    const copied = await copyText(data.output, "已產生並複製到剪貼簿");
    if (!copied) {
      showToast("已產生內容，可用右下方複製按鈕再試一次");
    }
  } catch (error) {
    els.aiResultMeta.textContent = "產生失敗";
    showToast(error.message, "error");
  } finally {
    setLoading(els.generateBtn, false);
  }
}

function wireEvents() {
  els.courseCode.addEventListener("change", () => {
    els.drawCourseCode.value = els.courseCode.value;
    syncLessonPreview();
  });

  els.lessonCode.addEventListener("change", () => {
    els.drawLessonCode.value = els.lessonCode.value;
    syncDisplayLesson();
    syncLessonPreview();
  });

  els.drawCurrentBtn.addEventListener("click", async () => {
    try {
      await drawQuestions(els.courseCode.value, els.lessonCode.value, els.questions, "已抽出本堂三題");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  els.drawPreviousBtn.addEventListener("click", async () => {
    try {
      await drawQuestions(
        els.courseCode.value,
        previousLessonCode(els.lessonCode.value),
        els.previousQuestions,
        "已抽出上一課三題",
      );
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  els.drawStandaloneBtn.addEventListener("click", async () => {
    try {
      await drawQuestions(
        els.drawCourseCode.value,
        els.drawLessonCode.value,
        els.standaloneQuestions,
        "已抽出獨立題目",
      );
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  els.pasteCurrentBtn.addEventListener("click", () => {
    if (!els.standaloneQuestions.value.trim()) {
      showToast("請先抽題", "error");
      return;
    }
    els.questions.value = els.standaloneQuestions.value;
    showToast("已貼到本堂驗收問題");
  });

  els.pastePreviousBtn.addEventListener("click", () => {
    if (!els.standaloneQuestions.value.trim()) {
      showToast("請先抽題", "error");
      return;
    }
    els.previousQuestions.value = els.standaloneQuestions.value;
    showToast("已貼到上週驗收問題");
  });

  els.copyStandaloneBtn.addEventListener("click", () => {
    copyText(els.standaloneQuestions.value, "抽題內容已複製");
  });

  els.generateBtn.addEventListener("click", generateContactBook);
  els.copyResultBtn.addEventListener("click", () => {
    copyText(latestOutput || els.resultBox.textContent, "聯絡簿內容已複製");
  });
}

async function init() {
  bindElements();
  wireEvents();

  try {
    const data = await fetchJson("/api/courses");
    courses = data.courses || [];
    const courseOptions = courses.map((course) => ({ value: course.code, label: course.code }));
    const lessonOptions = (data.lessonOptions || []).map((value) => ({ value, label: value }));
    const displayCourseOptions = (data.displayCourseOptions || []).map((value) => ({ value, label: value }));
    const defaults = data.defaults || {};

    setOptions(els.courseCode, courseOptions, defaults.courseCode);
    setOptions(els.drawCourseCode, courseOptions, defaults.courseCode);
    setOptions(els.lessonCode, lessonOptions, defaults.lessonCode);
    setOptions(els.drawLessonCode, lessonOptions, defaults.lessonCode);
    setOptions(els.displayCourse, displayCourseOptions, defaults.displayCourse);

    els.displayLesson.value = defaults.displayLesson || "2";
    els.hasPrevious.checked = Boolean(defaults.hasPrevious);
    els.useAI.checked = Boolean(defaults.useAI);
    document.querySelector(`input[name="schedule"][value="${defaults.schedule || "fixed"}"]`).checked = true;

    renderProviderStrip(data.providers);
    syncLessonPreview();
  } catch (error) {
    showToast(error.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", init);
