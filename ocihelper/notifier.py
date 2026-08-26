from __future__ import annotations

import json
import logging
import subprocess

from .config import TelegramConfig

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org/bot"


class Notifier:
    """通过 Telegram Bot API 发送文本通知。

    发送方式与参考项目 oracle-freetier-instance-creation 的 send_telegram_message
    保持一致（curl POST 到相同端点），未配置 token/user_id 时自动禁用。
    """

    def __init__(self, tg: TelegramConfig):
        self.token = (tg.token or "").strip()
        self.user_id = (tg.user_id or "").strip()
        self.enabled = bool(self.token and self.user_id)
        if not self.enabled:
            logger.debug("Telegram 未配置（缺少 token 或 user_id），通知已禁用")

    def send(self, text: str) -> None:
        if not self.enabled:
            return

        url = f"{_API_BASE}{self.token}/sendMessage"
        cmd = [
            "curl",
            "-s",
            "-X",
            "POST",
            url,
            "-d",
            f"chat_id={self.user_id}",
            "-d",
            f"text={text}",
            "-d",
            "disable_web_page_preview=true",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            out = (result.stdout or "").strip()
            if not out:
                logger.warning("Telegram 通知无返回（curl exit=%s）", result.returncode)
                return
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                logger.warning("Telegram 通知返回非预期内容: %s", out[:200])
                return
            if not data.get("ok"):
                logger.warning("Telegram 通知发送失败: %s", data.get("description"))
        except Exception as exc:  # noqa: BLE001 - 通知失败不应中断主流程
            logger.warning("Telegram 通知发送异常: %s", exc)
