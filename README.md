# OrangeAppleAssistantWeb

Flask web 版學生聯絡簿產生器，移植自 `howardtuan/OrangeAppleAssistant`。保留原桌面版的課程資料、題庫抽題、聯絡簿文字規則與 AI 潤飾流程，不需要資料庫。

## 功能

- 產生聯絡簿文字，保持文章格式
- 學生姓名、課程、課次、聯絡簿課程名稱、聯絡簿堂數、進度狀態
- 上週未完成與上週驗收問題開頭
- 學習表現、本堂課驗收問題、上週進度驗收問題
- 依目前課程與課次抽三題帶入本堂
- 依目前課程自動抽上一課三題
- 獨立抽題區，可貼到本堂、貼到上週或複製
- 產生後嘗試自動複製，並提供手動複製按鈕
- AI 潤飾，預設先用 iKunCode，連不上或失敗時自動 fallback 到 OpenAI
- RWD 單頁介面，桌面三欄、平板/手機自動重排

## 環境變數

所有密鑰都放在 `.env`。請先複製範例：

```bash
cp .env.example .env
```

填入需要的 key：

```env
AI_MODEL=gpt-5.4-mini
AI_PROVIDER_ORDER=ikuncode,openai

IKUNCODE_API_KEY=your-ikuncode-key
IKUNCODE_BASE_URL=https://api.ikuncode.cc/v1

OPENAI_API_KEY=your-openai-key
OPENAI_BASE_URL=
```

`AI_PROVIDER_ORDER=ikuncode,openai` 表示先呼叫 iKunCode；如果 iKunCode 未設定、連線失敗或 API 回傳錯誤，會自動改用 OpenAI。

## 本機啟動

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask --app app run --host 0.0.0.0 --port 5000 --debug
```

開啟：

```text
http://localhost:5000
```

## Docker 啟動

```bash
docker compose up --build
```

開啟：

```text
http://localhost:5000
```

也可以直接用 Docker：

```bash
docker build -t orange-apple-assistant-web .
docker run --rm --env-file .env -p 5000:5000 orange-apple-assistant-web
```

## 專案結構

- `app.py`：Flask routes
- `contact_book.py`：原桌面版聯絡簿文字規則
- `ai_client.py`：iKunCode/OpenAI fallback
- `course_data.py`：課程名稱與 `db.py` 映射
- `db.py`：原課程內容資料
- `question_bank.py`：原題庫讀取與抽題邏輯
- `question_bank.json`：原驗收問題題庫
- `templates/index.html`：Web UI
- `static/css/styles.css`：RWD 樣式
- `static/js/app.js`：前端互動
