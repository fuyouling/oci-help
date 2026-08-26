#!/usr/bin/env bash
#
# setup_init.sh - 一次性初始化 oci-help 运行环境
#
# 用途：在目标服务器上第一次部署时执行，完成：
#   1. 创建 Python 虚拟环境 (.venv)
#   2. 安装项目依赖（pip install -e .）
#   3. 复制配置示例文件，准备真实配置
#
# 使用方法：
#   bash setup_init.sh
#
# 注意：虚拟环境与真实凭证不会提交到仓库，部署后请按需编辑：
#   config/config.yaml       应用配置
#   config/oci_config        OCI SDK 配置
#   config/oci_api_private_key.pem  API 私钥
#
set -euo pipefail

# 进入脚本所在目录，确保相对路径正确
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"

echo "==> 检查 Python 版本（要求 >= 3.11）"
"$PYTHON" - <<'PY'
import sys
if sys.version_info < (3, 11):
    sys.exit(f"需要 Python >= 3.11，当前版本为 {sys.version.split()[0]}")
print(f"Python {sys.version.split()[0]} 满足要求")
PY

echo "==> 创建虚拟环境：$VENV_DIR"
if [ -d "$VENV_DIR" ]; then
    echo "    已存在，跳过创建。"
else
    "$PYTHON" -m venv "$VENV_DIR"
    echo "    创建完成。"
fi

# 激活虚拟环境（仅本次脚本进程内生效）
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> 升级 pip"
pip install --upgrade pip

echo "==> 安装项目依赖（可编辑模式）"
pip install -e .

echo "==> 准备配置文件"
for pair in "config/config.example.yaml:config/config.yaml" \
            "config/oci_config.example:config/oci_config"; do
    src="${pair%%:*}"
    dst="${pair##*:}"
    if [ -f "$dst" ]; then
        echo "    $dst 已存在，跳过。"
    else
        cp "$src" "$dst"
        echo "    已复制 $src -> $dst"
    fi
done

echo
echo "==> 初始化完成。"
echo "    请编辑以下文件填入真实值（如尚未填写）："
echo "      - config/config.yaml   （应用配置，可选 telegram 通知）"
echo "      - config/oci_config    （OCI SDK 配置，含凭证）"
echo "      - config/oci_api_private_key.pem （如示例使用，请替换为真实私钥）"
echo
echo "    验证安装："
echo "      .venv/bin/oci-help --help"
echo
echo "    初始化完成后，使用 setup.sh 后台启动服务。"
