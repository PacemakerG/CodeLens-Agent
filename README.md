# deep-ai-analysis

拦截并分析 AI 服务 HTTP/HTTPS 流量的 CLI 工具包。

## 环境要求

- Python 3.10+
- [mitmproxy](https://mitmproxy.org/)（作为依赖自动安装）

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

### 从源码安装（开发模式）

```bash
git clone ssh://git@git.sankuai.com/~zhoukang04/deep-ai-analysis.git
cd deep-ai-analysis
pip install -e .
```

### 从 .whl 文件安装（离线分发）

如果没有 pip 仓库访问，可以先在有源码的机器上打包，再把 `.whl` 文件发给对方安装。

**打包：**

```bash
python3 -m pip wheel . --no-deps --no-build-isolation -w dist/
# 生成 dist/deep_ai_analysis-0.1.0-py3-none-any.whl
```

**安装：**

```bash
pip install deep_ai_analysis-0.1.0-py3-none-any.whl
```

> **依赖说明：** wheel 不内嵌依赖包，安装环境需能安装 `click>=8.0` 和 `mitmproxy>=10.0`。

## 快速开始 ⭐️⭐️⭐️⭐️⭐️

两步拦截 `mc` 流量：

```bash
# 终端 1 — 启动代理
deep-ai-analysis proxy

# 终端 2 — 通过代理启动 mc
deep-ai-analysis start-mc
```

## 命令说明

### `proxy`

启动 HTTP/HTTPS 拦截代理，将匹配的流量记录到每日 JSONL 日志文件。

```
用法: deep-ai-analysis proxy [OPTIONS]

选项:
  --port INTEGER      代理监听端口  [默认: 7788]
  --output DIRECTORY  JSONL 日志文件写入目录  [默认: ~/.deep-ai-analysis/raw-req-resp]
  --help              显示帮助信息
```

**示例：**

```bash
deep-ai-analysis proxy
deep-ai-analysis proxy --port 9000 --output ~/ai-logs
```

启动后会打印监听地址、过滤域名、日志目录和 CA 证书路径。

---

### `start-mc`

自动注入代理环境变量后启动 `mc --code`，支持透传额外参数给 `mc`。

```
用法: deep-ai-analysis start-mc [OPTIONS] [EXTRA_ARGS]...

选项:
  --port INTEGER  HTTPS_PROXY 指向的代理端口  [默认: 7788]
  --help          显示帮助信息
```

会为 `mc` 进程设置以下环境变量：

| 变量 | 值 |
|---|---|
| `HTTPS_PROXY` | `http://127.0.0.1:<port>` |
| `NODE_EXTRA_CA_CERTS` | `~/.mitmproxy/mitmproxy-ca-cert.pem` |

```bash
deep-ai-analysis start-mc
deep-ai-analysis start-mc --port 9000
deep-ai-analysis start-mc --resume /path/to/session   # 额外参数透传给 mc
```

---

### `clear-req-resp`

将代理原始 JSONL 日志清洗为结构化记录。解析 `request.body` 为 JSON，从 SSE 事件重建 `response_json`，并从请求头提取 `claude_session_id`。非 SSE 记录会被跳过。

```
用法: deep-ai-analysis clear-req-resp [OPTIONS] INPUT

参数:
  INPUT  .jsonl 文件路径或包含 .jsonl 文件的目录

选项:
  -o, --output PATH  输出路径（仅单文件模式）
  --help             显示帮助信息
```

**输出格式**（JSONL，每行一条记录）：

```json
{
  "timestamp": "2026-05-08T05:06:43.598393+00:00",
  "domain": "mcli.sankuai.com",
  "method": "POST",
  "url": "https://mcli.sankuai.com/v1/messages",
  "claude_session_id": "e75940a3-3a79-41bd-be4d-6d0fb1a5a307",
  "request_json": { "model": "...", "messages": [...] },
  "response_json": {
    "message": {
      "id": "msg_...", "model": "...", "stop_reason": "end_turn",
      "content": { "text": "..." },
      "usage": { "input_tokens": 206, "output_tokens": 79 }
    }
  }
}
```

**示例：**

```bash
# 单文件 → logs/2026-05-08_parsed.jsonl
deep-ai-analysis clear-req-resp logs/2026-05-08.jsonl

# 自定义输出路径
deep-ai-analysis clear-req-resp logs/2026-05-08.jsonl -o parsed.jsonl

# 目录模式 — 处理所有 .jsonl 文件
deep-ai-analysis clear-req-resp logs/
```

---

### `web-server`

启动本地 HTTP 服务器，提供基于浏览器的 Claude Code 会话日志查看器。无需上传文件，直接读取 `~/.claude/projects`。

```
用法: deep-ai-analysis web-server [OPTIONS]

选项:
  --port INTEGER      查看器 API 服务端口  [默认: 7789]
  --projects-dir PATH Claude Code 项目目录  [默认: ~/.claude/projects]
  --req-resp-dir PATH 原始请求响应 JSONL 文件目录  [默认: ~/.deep-ai-analysis/raw-req-resp]
  --help              显示帮助信息
```

```bash
deep-ai-analysis web-server
```

启动后自动在浏览器中打开 `http://127.0.0.1:7789/claude-log.html`。也可手动访问：

- `http://127.0.0.1:7789/claude-log.html` — Claude Code 会话日志查看器
- `http://127.0.0.1:7789/` — 会话对话查看器
- `http://127.0.0.1:7789/req-resp.html` — 原始请求响应查看器

查看器功能：
- 按项目浏览所有 Claude Code 会话
- 查看主会话对话（用户消息、助手回复、工具调用）
- 在独立 tab 中查看每个 subagent
- 查看每次会话的 token 用量统计

## 域名过滤

需要记录的域名在 `deep_ai_analysis/config.py` 中配置：

```python
RECORD_DOMAINS: list[str] = [
    "mcli.sankuai.com",
]
```

只有列表中的域名流量才会写入磁盘，其他流量透明转发不记录。

## HTTPS 设置

mitmproxy 使用本地 CA 证书解密 HTTPS 流量，需要信任一次：

```bash
# CA 证书在首次运行时生成于：
~/.mitmproxy/mitmproxy-ca-cert.pem

# macOS — 系统级信任证书：
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
```

然后配置 HTTP 客户端使用代理：

```bash
export http_proxy=http://127.0.0.1:7788
export https_proxy=http://127.0.0.1:7788
```

## 日志格式

### 原始代理日志（`proxy` 命令）

写入 `~/.deep-ai-analysis/raw-req-resp/<sessionId>/YYYY-MM-DD.jsonl`，每行一个 JSON 对象。

**SSE（流式）请求：**

```json
{
  "timestamp": "2026-05-08T10:31:00.000000+00:00",
  "domain": "mcli.sankuai.com",
  "method": "POST",
  "url": "https://mcli.sankuai.com/v1/messages",
  "request": {
    "headers": { "Content-Type": "application/json" },
    "body": "{\"model\": \"...\", \"messages\": [...]}"
  },
  "response": {
    "status": 200,
    "headers": { "content-type": "text/event-stream" },
    "body": "event: message_start\ndata: {...}\n\n..."
  },
  "is_sse": true,
  "sse_events": ["event: message_start\ndata: {...}", "..."]
}
```

> 注意：`Authorization` 请求头已从 `request.headers` 中排除，防止 token 泄露。

### 清洗日志（`clear-req-resp` 命令）

输出格式见上方 [`clear-req-resp`](#clear-req-resp) 章节。

**用 `jq` 查询清洗日志：**

```bash
# 查看所有 session ID
jq -r '.claude_session_id' logs/2026-05-08_parsed.jsonl | sort -u

# 查看模型使用情况
jq -r '.response_json.message.model' logs/2026-05-08_parsed.jsonl | sort | uniq -c

# 查看每次请求的 token 用量
jq '{url, usage: .response_json.message.usage}' logs/2026-05-08_parsed.jsonl
```
