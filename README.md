# deep-ai-analysis

拦截并分析 AI 服务 HTTP/HTTPS 流量的 CLI 工具包。

## 环境要求

- Python 3.10+
- [mitmproxy](https://mitmproxy.org/)（通过 `brew install mitmproxy` 安装）

## 安装

### 一键安装脚本（推荐⭐️⭐️⭐️⭐️⭐️）

```bash
bash <(curl -s https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/install.sh)
```

或者手动下载后执行：

```bash
curl -O https://msstest.sankuai.com/ad-dqe-public/ai-coding-analysis/install.sh
bash install.sh
```

### 从源码安装（开发模式，使用 uv）

```bash
git clone ssh://git@git.sankuai.com/~zhoukang04/deep-ai-analysis.git
cd deep-ai-analysis
uv sync --extra dev
source .venv/bin/activate
```

环境管理改为 uv，但**命令写法保持不变**。无论是当前命令还是后续新增命令，均保持：

```bash
deep-ai-analysis <subcommand>
```

也就是说，uv 只负责创建和同步环境，不改变 CLI 的使用风格。

## 快速开始 ⭐️⭐️⭐️⭐️⭐️

每个终端都先进入项目目录并激活环境：

```bash
cd deep-ai-analysis
source .venv/bin/activate
```

然后分别运行：

```bash
# 终端 1 — 启动代理
deep-ai-analysis proxy

# 终端 2 — 通过代理启动 mc，开始AI Coding
deep-ai-analysis start-mc

# 终端 3 — 浏览器查看AI工作内容
deep-ai-analysis web-server
```

## 数据导出

导出指定 Claude Code session 的本地日志和原始请求响应到一个压缩包：

```bash
# 先激活 uv 创建的环境
source .venv/bin/activate

# 查看当前可导出的 session
deep-ai-analysis export --list

# 导出一个 session 的数据
# 压缩包内包含：
# - claude-log.jsonl
# - subagents/*（如果存在）
# - raw-req-resp/*.jsonl（如果存在）
deep-ai-analysis export <session-id> -o /tmp/deep-ai-analysis-export.tar.gz
```

## 命令说明

```bash
source .venv/bin/activate
deep-ai-analysis --help
```

也可以直接查看 export 子命令帮助：

```bash
source .venv/bin/activate
deep-ai-analysis export --help
```

注意：不要在项目目录外执行 `source .venv/bin/activate`。需要先进入仓库根目录再激活环境。

```bash
cd deep-ai-analysis
source .venv/bin/activate
```

这样可以确保你运行的是 uv 管理的最新版本，而不是系统里旧的全局命令。