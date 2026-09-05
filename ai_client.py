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
    model_env: str
    default_model: str
    default_base_url: str | None = None
    use_legacy_model: bool = True


PROVIDERS = {
    "ikuncode": ProviderConfig(
        key="ikuncode",
        label="iKunCode",
        api_key_env="IKUNCODE_API_KEY",
        base_url_env="IKUNCODE_BASE_URL",
        model_env="IKUNCODE_MODEL",
        default_model="gpt-5.4-mini",
        default_base_url="https://api.ikuncode.cc/v1",
    ),
    "ikuncode_fallback": ProviderConfig(
        key="ikuncode_fallback",
        label="iKunCode 備援",
        api_key_env="IKUNCODE_FALLBACK_API_KEY",
        base_url_env="IKUNCODE_FALLBACK_BASE_URL",
        model_env="IKUNCODE_FALLBACK_MODEL",
        default_model="gemini-3.8-flash",
        default_base_url="https://api.ikuncode.cc/v1",
        use_legacy_model=False,
    ),
    "openai": ProviderConfig(
        key="openai",
        label="OpenAI",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
        model_env="OPENAI_MODEL",
        default_model="gpt-5.4-mini",
    ),
}


def _provider_order():
    raw = os.getenv("AI_PROVIDER_ORDER", "ikuncode,ikuncode_fallback,openai")
    requested = [item.strip().lower() for item in raw.split(",") if item.strip()]
    order = []
    for item in requested:
        if item not in PROVIDERS or item in order:
            continue
        order.append(item)
        # Keep old AI_PROVIDER_ORDER=ikuncode,openai deployments compatible.
        if item == "ikuncode" and "ikuncode_fallback" not in requested:
            order.append("ikuncode_fallback")
    return order


def _safe_error(exc):
    message = str(exc).replace("\n", " ").strip()
    if len(message) > 260:
        message = message[:257] + "..."
    return f"{exc.__class__.__name__}: {message}"


def _provider_model(provider):
    provider_model = os.getenv(provider.model_env, "").strip()
    legacy_model = os.getenv("AI_MODEL", "").strip()
    if provider.use_legacy_model:
        return provider_model or legacy_model or provider.default_model
    return provider_model or provider.default_model


def configured_providers():
    result = []
    for key in _provider_order():
        provider = PROVIDERS[key]
        result.append(
            {
                "key": provider.key,
                "label": provider.label,
                "configured": bool(os.getenv(provider.api_key_env)),
                "baseUrl": os.getenv(
                    provider.base_url_env, provider.default_base_url or ""
                ),
                "model": _provider_model(provider),
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
    errors = []

    for key in _provider_order():
        provider = PROVIDERS[key]
        client = _make_client(provider)
        if client is None:
            errors.append(f"{provider.label}: 未設定 {provider.api_key_env}")
            continue

        model = _provider_model(provider)
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
        except Exception as exc:  # Try the next model/provider on API failures.
            errors.append(f"{provider.label} ({model}): {_safe_error(exc)}")

    raise RuntimeError("AI 潤飾失敗，已嘗試所有可用供應商：" + "；".join(errors))
