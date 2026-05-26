"""
兼容层：保留旧模块导出，内部统一转向新的 settings 配置体系。
"""
from __future__ import annotations

import os
import sys

from openai import AsyncOpenAI

from src.infrastructure.config.settings import ai_settings, scraper_settings, settings


STATE_FILE = scraper_settings.state_file
IMAGE_SAVE_DIR = settings.image_save_dir
CONFIG_FILE = settings.config_file
TASK_IMAGE_DIR_PREFIX = settings.task_image_dir_prefix

API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search"
DETAIL_API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail"

API_KEY = ai_settings.api_key
BASE_URL = ai_settings.base_url
MODEL_NAME = ai_settings.model_name
PROXY_URL = ai_settings.proxy_url
RUN_HEADLESS = scraper_settings.run_headless
LOGIN_IS_EDGE = scraper_settings.login_is_edge
RUNNING_IN_DOCKER = scraper_settings.running_in_docker
AI_DEBUG_MODE = ai_settings.debug_mode
SKIP_AI_ANALYSIS = ai_settings.skip_analysis
ENABLE_THINKING = ai_settings.enable_thinking
ENABLE_RESPONSE_FORMAT = ai_settings.enable_response_format

NTFY_TOPIC_URL = os.getenv("NTFY_TOPIC_URL")
GOTIFY_URL = os.getenv("GOTIFY_URL")
GOTIFY_TOKEN = os.getenv("GOTIFY_TOKEN")
BARK_URL = os.getenv("BARK_URL")
WX_BOT_URL = os.getenv("WX_BOT_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_METHOD = os.getenv("WEBHOOK_METHOD", "POST").upper()
WEBHOOK_HEADERS = os.getenv("WEBHOOK_HEADERS")
WEBHOOK_CONTENT_TYPE = os.getenv("WEBHOOK_CONTENT_TYPE", "JSON").upper()
WEBHOOK_QUERY_PARAMETERS = os.getenv("WEBHOOK_QUERY_PARAMETERS")
WEBHOOK_BODY = os.getenv("WEBHOOK_BODY")
PCURL_TO_MOBILE = os.getenv("PCURL_TO_MOBILE", "false").lower() == "true"

IMAGE_DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)


def _build_legacy_client():
    if not BASE_URL or not MODEL_NAME:
        print("警告：未在 .env 文件中完整设置 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。AI相关功能可能无法使用。")
        return None
    try:
        if PROXY_URL:
            os.environ["HTTP_PROXY"] = PROXY_URL
            os.environ["HTTPS_PROXY"] = PROXY_URL
        return AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    except Exception as exc:  # pragma: no cover - compatibility path
        print(f"初始化 OpenAI 客户端时出错: {exc}")
        return None


client = _build_legacy_client()

if not all([BASE_URL, MODEL_NAME]) and "prompt_generator.py" in sys.argv[0]:
    sys.exit("错误：请确保在 .env 文件中完整设置了 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。(OPENAI_API_KEY 对于某些服务是可选的)")


def get_ai_request_params(**kwargs):
    if ENABLE_THINKING:
        kwargs["extra_body"] = {"enable_thinking": False}

    if not ENABLE_RESPONSE_FORMAT and "text" in kwargs:
        text_config = kwargs.get("text")
        if isinstance(text_config, dict):
            text_config = dict(text_config)
            text_config.pop("format", None)
            if text_config:
                kwargs["text"] = text_config
            else:
                del kwargs["text"]
    return kwargs
