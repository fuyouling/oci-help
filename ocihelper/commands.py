from __future__ import annotations

import logging
import re
import time

import oci

from .config import AppConfig, MonitorConfig
from .notifier import Notifier
from .oci_client import OciClient, STOPPED_STATE

logger = logging.getLogger(__name__)


def _match_name(instance, name_filter: str) -> bool:
    if not name_filter:
        return True
    return re.search(name_filter, instance.display_name or "") is not None


def list_instances(client: OciClient, compartments: list[str], name_filter: str = "") -> None:
    targets = client.get_compartments(compartments)
    total = 0
    for compartment_id in targets:
        instances = client.list_instances(compartment_id)
        for instance in instances:
            if not _match_name(instance, name_filter):
                continue
            total += 1
            print(
                f"{instance.id}\t{instance.display_name}\t"
                f"{instance.lifecycle_state}\t{compartment_id}"
            )
    logger.info("共列出 %d 个实例", total)


def _collect_stopped(client: OciClient, compartments: list[str], name_filter: str):
    stopped = []
    for compartment_id in client.get_compartments(compartments):
        for instance in client.list_instances(compartment_id):
            if instance.lifecycle_state == STOPPED_STATE and _match_name(instance, name_filter):
                stopped.append(instance)
    return stopped


def run_monitor(app: AppConfig, stop_event=None, once: bool = False) -> None:
    """按配置的时间间隔轮询，自动开启处于 STOPPED 状态的实例。"""
    cfg: MonitorConfig = app.monitor
    client = OciClient(app.oci)
    notifier = Notifier(app.telegram)

    logger.info(
        "开始轮询：间隔 %ds, compartments=%s, dry_run=%s",
        cfg.poll_interval,
        cfg.compartments or "tenancy-root",
        cfg.dry_run,
    )

    if app.telegram.notify_on_start:
        notifier.send(f"✅ oci-help 已启动（间隔 {cfg.poll_interval}s）")

    while True:
        if stop_event is not None and stop_event.is_set():
            logger.info("收到停止信号，退出轮询")
            break

        stopped = _collect_stopped(client, cfg.compartments, cfg.name_filter)
        if stopped:
            logger.info("发现 %d 个已停止的实例，准备开启", len(stopped))
            for instance in stopped:
                try:
                    client.start_instance(instance, dry_run=cfg.dry_run)
                    if app.telegram.notify_on_success:
                        notifier.send(
                            f"🚀 已启动：{instance.display_name}"
                            + ("（dry_run）" if cfg.dry_run else "")
                        )
                except oci.exceptions.ServiceError as exc:
                    logger.error("开启实例失败 %s: %s", instance.id, exc)
                    if app.telegram.notify_on_failure:
                        notifier.send(
                            f"❌ 启动失败：{instance.display_name}\n{exc.code}: {exc.message}"
                        )
        else:
            logger.debug("本次轮询未发现已停止的实例")

        if once:
            logger.info("已完成单次轮询，退出")
            break

        if stop_event is not None and stop_event.is_set():
            break

        time.sleep(cfg.poll_interval)
