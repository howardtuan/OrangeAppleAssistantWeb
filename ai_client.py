import os
from dataclasses import dataclass

from openai import OpenAI


SYSTEM_PROMPT = (
    "你是老師，請把輸入內容整理成聯絡簿文章。"
    "語氣自然、口語一點，不要官腔，不要敬語或客套語。"
    "保持成段落、不要條列或標題。"
    "若開頭包含「已完成上週內容，驗收問題為：【...】。」這句，請原封不動保留在最前面。"
    "內容需包含：學生、課程、課堂內容、學習表現、驗收問題、進度狀態。"
    "若有資訊不足，請用自然語句帶過，不要出現「未填寫」字樣。"
)


@dataclass(frozen=True)
class ProviderConfig:
    key: str
    label: str
    api_key_env: str
    base_url_env: str
    default_base_url: str | None = None


PROVIDERS = {
    "ikuncode": ProviderConfig(
        key="ikuncode",
        label="iKunCode",
        api_key_env="IKUNCODE_API_KEY",
        base_url_env="IKUNCODE_BASE_URL",
        default_base_url="https://api.ikuncode.cc/v1",
    ),
    "openai": ProviderConfig(
        key="openai",
        label="OpenAI",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
    ),
}


def _provider_order():
    raw = os.getenv("AI_PROVIDER_ORDER", "ikuncode,openai")
    order = [item.strip().lower() for item in raw.split(",") if item.strip()]
    return [item for item in order if item in PROVIDERS]


def _safe_error(exc):
    message = str(exc).replace("\n", " ").strip()
    if len(message) > 260:
        message = message[:257] + "..."
    return f"{exc.__class__.__name__}: {message}"


def configured_providers():
    result = []
    for key in _provider_order():
        provider = PROVIDERS[key]
        result.append(
            {
                "key": provider.key,
                "label": provider.label,
                "configured": bool(os.getenv(provider.api_key_env)),
                "baseUrl": os.getenv(provider.base_url_env, provider.default_base_url or ""),
            }
        )
    return result


def _make_client(provider):
    api_key = os.getenv(provider.api_key_env)
    if not api_key:
        return None

    base_url = os.getenv(provider.base_url_env, provider.default_base_url or "").strip()
    kwargs = {
        "api_key": api_key,
        "timeout": float(os.getenv("AI_TIMEOUT_SECONDS", "45")),
        "max_retries": int(os.getenv("AI_MAX_RETRIES", "0")),
    }
    if base_url:
        kwargs["base_url"] = base_url

    return OpenAI(**kwargs)


def polish_contact_book(draft):
    model = os.getenv("AI_MODEL", "gpt-5.4-mini")
    errors = []

    for key in _provider_order():
        provider = PROVIDERS[key]
        client = _make_client(provider)
        if client is None:
            errors.append(f"{provider.label}: 未設定 {provider.api_key_env}")
            continue

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": draft},
                ],
            )
            content = completion.choices[0].message.content
            if not content:
                raise RuntimeError("AI 回應內容為空。")
            return {
                "output": content,
                "provider": provider.key,
                "providerLabel": provider.label,
                "model": model,
                "fallbackErrors": errors,
            }
        except Exception as exc:  # Fallback should cover provider/network/API failures.
            errors.append(f"{provider.label}: {_safe_error(exc)}")

    raise RuntimeError("AI 潤飾失敗，已嘗試所有可用供應商：" + "；".join(errors))
