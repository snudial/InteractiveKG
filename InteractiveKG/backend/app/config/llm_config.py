import os
from typing import Optional
from dotenv import load_dotenv
from ..services.llm_service import LLMConfig, LLMProvider

load_dotenv()
def get_llm_config() -> Optional[LLMConfig]:
    provider = LLMProvider.OPENAI_GPT4O_MINI

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("Warning: LLM_API_KEY not set for OpenAI provider, disabling LLM")
        return None

    forced_model_name = "gpt-4o-mini-2024-07-18"

    env_model = os.getenv("LLM_MODEL_NAME")
    if env_model and env_model != forced_model_name:
        print(f"Warning: 环境变量中设置的模型 '{env_model}' 被强制覆盖为 '{forced_model_name}'")
    return LLMConfig(
        provider=provider,
        api_key=api_key,
        model_name=forced_model_name,
        timeout=int(os.getenv("LLM_TIMEOUT", "30")),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "2"))
    )
def is_llm_enabled() -> bool:

    config = get_llm_config()
    return config is not None

DEFAULT_CONFIGS = {
    "openai_gpt4o_mini": LLMConfig(
        provider=LLMProvider.OPENAI_GPT4O_MINI,
        api_key="your-api-key-here",
        model_name="gpt-4o-mini-2024-07-18",
        timeout=30,
        max_retries=2
    ),

    "disabled": LLMConfig(
        provider=LLMProvider.DISABLED
    )
}