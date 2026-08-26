from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG_PATHS = (
    "config/config.yaml",
    "config/config.yml",
    "config.yaml",
    "config.yml",
    "~/.config/oci-help/config.yaml",
)


def _resolve(path: str) -> str:
    """展开 ~ 与变量；相对路径按项目根目录解析。"""
    expanded = os.path.expanduser(os.path.expandvars(path))
    if not os.path.isabs(expanded):
        expanded = os.path.join(str(PROJECT_ROOT), expanded)
    return expanded


@dataclass
class OciConfig:
    config_file: str = "config/oci_config"
    profile: str = "DEFAULT"


@dataclass
class MonitorConfig:
    poll_interval: int = 300
    compartments: list[str] = field(default_factory=list)
    name_filter: str = ""
    dry_run: bool = False


@dataclass
class TelegramConfig:
    token: str = ""
    user_id: str = ""
    notify_on_start: bool = True
    notify_on_failure: bool = True
    notify_on_success: bool = True


@dataclass
class AppConfig:
    oci: OciConfig = field(default_factory=OciConfig)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)


def _expand(path: str) -> str:
    return os.path.expanduser(os.path.expandvars(path))


def load_config(path: str | None = None) -> AppConfig:
    raw: dict[str, Any] = {}
    candidates = [path] + list(DEFAULT_CONFIG_PATHS) if path else list(DEFAULT_CONFIG_PATHS)
    for candidate in candidates:
        candidate = _resolve(candidate)
        if os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
            break

    oci_raw = raw.get("oci", {}) or {}
    monitor_raw = raw.get("monitor", {}) or {}
    tg_raw = raw.get("telegram", {}) or {}

    return AppConfig(
        oci=OciConfig(
            config_file=_resolve(oci_raw.get("config_file", OciConfig.config_file)),
            profile=oci_raw.get("profile", OciConfig.profile),
        ),
        monitor=MonitorConfig(
            poll_interval=int(monitor_raw.get("poll_interval", MonitorConfig.poll_interval)),
            compartments=list(monitor_raw.get("compartments", []) or []),
            name_filter=monitor_raw.get("name_filter", MonitorConfig.name_filter) or "",
            dry_run=bool(monitor_raw.get("dry_run", MonitorConfig.dry_run)),
        ),
        telegram=TelegramConfig(
            token=tg_raw.get("token", TelegramConfig.token) or "",
            user_id=tg_raw.get("user_id", TelegramConfig.user_id) or "",
            notify_on_start=bool(tg_raw.get("notify_on_start", TelegramConfig.notify_on_start)),
            notify_on_failure=bool(tg_raw.get("notify_on_failure", TelegramConfig.notify_on_failure)),
            notify_on_success=bool(tg_raw.get("notify_on_success", TelegramConfig.notify_on_success)),
        ),
    )
