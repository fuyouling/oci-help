from __future__ import annotations

import configparser
import logging
import os
import tempfile

import oci

from .config import OciConfig, PROJECT_ROOT

logger = logging.getLogger(__name__)

STOPPED_STATE = "STOPPED"


class OciClient:
    """封装 OCI 配置与 Compute 客户端，提供实例查询与启动能力。"""

    def __init__(self, oci_config: OciConfig):
        self.oci_config = oci_config
        # OCI SDK 仅对 key_file 做 expanduser，相对路径按 cwd 解析，且与
        # 配置文件所在目录无关。为保持与 config_file 一致（相对项目根），
        # 这里把相对 key_file 解析为基于 PROJECT_ROOT 的绝对路径，再写入
        # 临时文件交给 from_file，从而与运行目录（cwd）无关。
        resolved_config_file = self._resolve_key_file(oci_config.config_file, oci_config.profile)
        self._config = oci.config.from_file(
            file_location=resolved_config_file,
            profile_name=oci_config.profile,
        )
        self._compute = oci.core.ComputeClient(self._config)

    @staticmethod
    def _resolve_key_file(config_file: str, profile: str) -> str:
        """解析 OCI 配置中的相对 key_file（相对 PROJECT_ROOT）为绝对路径。

        返回写入临时文件（已替换为绝对 key_file）的路径；若无需替换则直接
        返回原配置路径。临时文件在进程退出时自动清理。
        """
        parser = configparser.ConfigParser(interpolation=None)
        if not parser.read(config_file):
            return config_file

        try:
            key_file = parser.get(profile, "key_file", fallback=None)
        except (configparser.NoSectionError, configparser.NoOptionError):
            key_file = None

        if not key_file or os.path.isabs(os.path.expanduser(key_file)):
            return config_file

        resolved = os.path.join(str(PROJECT_ROOT), key_file)
        parser[profile]["key_file"] = resolved
        fd, tmp_path = tempfile.mkstemp(prefix="oci-help-config-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                parser.write(fh)
        except Exception:
            os.unlink(tmp_path)
            raise
        return tmp_path

    @property
    def tenancy(self) -> str:
        return self._config["tenancy"]

    def get_compartments(self, explicit: list[str]) -> list[str]:
        """返回要扫描的 compartment 列表；未显式指定时使用 tenancy 根。"""
        if explicit:
            return explicit
        return [self.tenancy]

    def list_instances(self, compartment_id: str) -> list[oci.core.models.Instance]:
        instances: list[oci.core.models.Instance] = []
        try:
            for instance in self._compute.list_instances(compartment_id).data:
                instances.append(instance)
        except oci.exceptions.ServiceError as exc:
            logger.warning("列出实例失败 compartment=%s: %s", compartment_id, exc)
        return instances

    def start_instance(self, instance: oci.core.models.Instance, dry_run: bool = False) -> None:
        if dry_run:
            logger.info("[dry-run] 将对实例 %s (%s) 执行 START", instance.display_name, instance.id)
            return
        self._compute.instance_action(instance.id, "START")
        logger.info("已对实例 %s (%s) 发送 START 指令", instance.display_name, instance.id)
