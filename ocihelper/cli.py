from __future__ import annotations

import argparse
import logging
import sys

from .commands import list_instances, run_monitor
from .config import load_config

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oci-help", description="OCI 操作辅助工具")
    parser.add_argument("-c", "--config", help="配置文件路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出调试日志")

    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="查询当前用户下的实例")
    p_list.add_argument("--compartment", action="append", default=[], help="指定 compartment OCID（可多次）")
    p_list.add_argument("--name-filter", help="按 display name 过滤（正则）")

    p_mon = sub.add_parser("monitor", help="轮询并自动开启已停止的实例")
    p_mon.add_argument("--poll-interval", type=int, help="轮询间隔（秒）")
    p_mon.add_argument("--compartment", action="append", default=[], help="指定 compartment OCID（可多次）")
    p_mon.add_argument("--name-filter", help="按 display name 过滤（正则）")
    p_mon.add_argument("--dry-run", action="store_true", help="只记录不实际开启")
    p_mon.add_argument("--once", action="store_true", help="只执行一次轮询后退出")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = load_config(args.config)

    if args.command == "list":
        if args.compartment:
            app.monitor.compartments = args.compartment
        if args.name_filter:
            app.monitor.name_filter = args.name_filter
        from .oci_client import OciClient

        client = OciClient(app.oci)
        list_instances(client, app.monitor.compartments, app.monitor.name_filter)
        return 0

    if args.command == "monitor":
        if args.poll_interval is not None:
            app.monitor.poll_interval = args.poll_interval
        if args.compartment:
            app.monitor.compartments = args.compartment
        if args.name_filter:
            app.monitor.name_filter = args.name_filter
        if args.dry_run:
            app.monitor.dry_run = True
        run_monitor(app, once=args.once)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
