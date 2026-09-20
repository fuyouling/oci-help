# oci-help

OCI（Oracle Cloud Infrastructure）操作辅助工具。

## 功能

- **查询实例**：列出当前用户可见 compartment 下的计算实例及其状态。
- **轮询自动开启**：按可配置的时间间隔轮询，自动将处于 `STOPPED` 状态的实例开启。

## 安装与虚拟环境（.venv）

本项目使用 Python 虚拟环境隔离依赖，所有依赖（含 OCI Python SDK）都安装在 `.venv/`
中，不影响系统 Python。

### 1. 创建虚拟环境

```bash
python -m venv .venv
```

> 若提示缺少 `venv` 模块，Debian/Ubuntu 可先执行 `sudo apt install python3-venv`。

### 2. 激活虚拟环境

激活后，终端提示符前通常会出现 `(.venv)` 字样，此后 `python` / `pip` / `oci-help`
都会指向虚拟环境内的版本。

- **Linux / macOS（bash/zsh）**：

  ```bash
  source .venv/bin/activate
  ```

- **Windows（CMD）**：

  ```bat
  .venv\Scripts\activate.bat
  ```

- **Windows（PowerShell）**：

  ```powershell
  .venv\Scripts\Activate.ps1
  ```

### 3. 安装项目依赖

```bash
pip install -e .
```

`-e` 表示以“可编辑”方式安装，后续修改代码无需重新安装。

### 4. 验证安装

```bash
oci-help --help
```

能正常打印帮助信息即说明安装与虚拟环境均就绪。

### 5. 不激活虚拟环境直接运行

若不想先 `source` 激活，也可以直接用虚拟环境里的可执行文件：

```bash
.venv/bin/oci-help --help          # Linux / macOS
.venv\Scripts\oci-help.exe --help  # Windows
```

### 6. 退出虚拟环境

```bash
deactivate
```

### 7. 代码更新后重新生效

修改了 `ocihelper/` 下的源码后，可编辑安装会自动同步；若改动涉及依赖或打包元数据，
重新执行一次：

```bash
pip install -e .
```

依赖 OCI Python SDK，需提前准备好 OCI 配置文件与 API 密钥（参考
https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm ）。

项目所有配置与凭证统一放在 `config/` 目录下：

```
config/
├── config.example.yaml     # 应用配置示例（提交到仓库）
├── config.yaml             # 应用实际配置（不提交，本地使用）
├── oci_config.example      # OCI SDK 配置示例（提交到仓库）
├── oci_config             # OCI SDK 实际配置（不提交，含凭证）
└── oci_api_private_key.pem # API 私钥（不提交）
```

复制示例并填入真实值：

```bash
cp config/config.example.yaml config/config.yaml
cp config/oci_config.example config/oci_config
```

应用配置（`config/config.yaml`）说明：

```yaml
oci:
  config_file: config/oci_config  # OCI SDK 配置文件路径
  profile: DEFAULT                # 配置中的 profile 名称

monitor:
  poll_interval: 300              # 轮询间隔（秒）
  compartments: []                # 要扫描的 compartment OCID；为空则使用 tenancy 根
  name_filter: ""                 # 仅作用于匹配的 display name（正则，可选）
  dry_run: false                  # true 时只记录不实际开启

telegram:
  token: ""            # 通过 @BotFather 获取的 token；留空则禁用通知
  user_id: ""          # 通过 @myidbot 获取的聊天 ID；留空则禁用通知
  notify_on_start: true      # 程序启动成功时发送通知
  notify_on_failure: true   # 启动实例失败时发送通知（可配置是否发送）
  notify_on_success: true   # 启动实例成功时发送通知
```

启用 Telegram 通知：`token` 通过 @BotFather 创建 bot 获取，`user_id` 通过 @myidbot 发送 `/start` 获取，填入上述配置即可。`token` 或 `user_id` 为空时不发送任何通知，也不影响主流程。

## 使用

### 快速开始（完整流程）

下面是从零到运行的一条完整命令流（假设已进入项目根目录）：

```bash
# 1) 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate          # Windows 见上文对应命令

# 2) 安装依赖
pip install -e .

# 3) 准备配置文件（复制示例后按需修改）
cp config/config.example.yaml config/config.yaml
cp config/oci_config.example config/oci_config
#    编辑 config/config.yaml 填入 telegram token/user_id（可选）
#    编辑 config/oci_config 确认 user/tenancy/region/key_file 正确

# 4) 查询当前实例（只读，安全）
oci-help list

# 5) 试运行：只记录将要开启的实例，不真正开机
oci-help monitor --dry-run

# 6) 真正开启一次后退出
oci-help monitor --once

# 7) 后台持续轮询（按 config 中的 poll_interval）
oci-help monitor
```

> 若未激活 venv，可把上面的 `oci-help` 替换为 `.venv/bin/oci-help`。

### 查询实例（list）

列出当前用户可见 compartment 下的实例（OCID / 名称 / 状态 / compartment）：

```bash
oci-help list
```

可选参数：
- `--compartment OCID`：指定要扫描的 compartment（可多次传入）；不指定时使用 tenancy 根。
- `--name-filter REGEX`：按实例 display name 正则过滤。

```bash
oci-help list --compartment ocid1.compartment.oc1..xxxx --name-filter '^web-'
```

### 轮询自动开启（monitor）

按配置的时间间隔轮询，自动对处于 `STOPPED` 状态的实例执行 `START`：

```bash
oci-help monitor
```

常用参数（均可覆盖配置文件中的对应项）：
- `--poll-interval 秒`：轮询间隔。
- `--compartment OCID`：指定 compartment（可多次）。
- `--name-filter REGEX`：仅对匹配的实例操作。
- `--dry-run`：只记录将要执行的操作，不真正开启实例（用于验证）。
- `--once`：只执行一次轮询后立即退出（用于单次手动触发 / 测试）。

示例：

```bash
oci-help monitor --dry-run                  # 试运行，不实际开机
oci-help monitor --once                     # 立即尝试开启一次后退出
oci-help monitor --poll-interval 120 --name-filter '^test-'
```

### 后台运行
```shell
bash setup.sh
```

### 配置优先级

命令行参数 > `config/config.yaml` > `config/config.example.yaml`/默认值。
未指定 compartment 时，默认扫描 tenancy 根 compartment。

### Telegram 通知

在 `config/config.yaml` 的 `telegram` 段填入 `token`（@BotFather 获取）与
`user_id`（@myidbot 发送 `/start` 获取）后即启用通知。`token` 或 `user_id`
为空时不发送任何通知，也不影响主流程。可分别通过 `notify_on_start` /
`notify_on_failure` / `notify_on_success` 控制启动成功、启动失败、每次成功开启
的通知开关。
