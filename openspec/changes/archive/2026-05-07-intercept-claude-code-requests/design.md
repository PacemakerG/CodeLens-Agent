## Context

Claude Code 通过 Anthropic SDK 与 `https://api.anthropic.com` 通信，发送包含用户对话、工具调用等内容的 HTTP 请求，并接收流式（SSE）或非流式 JSON 响应。目前这些原始通信内容对用户不可见，无法用于调试、分析或研究目的。

Anthropic SDK 支持通过 `ANTHROPIC_BASE_URL` 环境变量配置 API 端点，这为透明代理提供了入口。

## Goals / Non-Goals

**Goals:**
- 实现一个本地 HTTP/HTTPS 代理，透明转发 Claude Code 与 Anthropic API 之间的所有流量
- 完整记录请求头、请求体（含 system prompt、messages、tools 等）
- 完整记录响应内容，包括流式 SSE 响应的每个 chunk 以及重组后的完整响应
- 将记录内容存储为结构化的 JSON Lines 格式，按会话/时间分组
- 提供查看和检索已记录日志的工具

**Non-Goals:**
- 修改请求/响应内容（只记录，不篡改）
- 支持多用户并发（单用户本地工具）
- 实时流式监控 UI（基础 CLI 查看即可）
- 云端存储或远程访问

## Decisions

### 决策 1：代理实现方式 — 反向代理 vs MITM 代理

**选择：反向代理（利用 `ANTHROPIC_BASE_URL`）**

通过设置 `ANTHROPIC_BASE_URL=http://localhost:PORT`，Claude Code 的 Anthropic SDK 会将所有请求发往本地代理。代理记录请求后，再转发到真实的 `https://api.anthropic.com`，将响应原样返回。

**放弃：MITM 代理（mitmproxy 等）**

MITM 代理需要安装 CA 证书、修改系统代理设置，配置复杂且有安全风险。反向代理方式更简洁，无需证书操作。

### 决策 2：实现语言 — Node.js vs Python

**选择：Node.js（TypeScript）**

- Claude Code 本身基于 Node.js，环境天然兼容
- `http-proxy` / 原生 `http` 模块对流式响应（SSE）支持成熟
- 与项目现有技术栈一致

**放弃：Python（mitmproxy/httpx）**

需要额外安装 Python 环境，且 mitmproxy 的 SSE 流处理需要额外配置。

### 决策 3：存储格式 — JSON Lines vs SQLite

**选择：JSON Lines（.jsonl）**

- 无需数据库依赖，直接文件读写
- 每行一条完整记录，易于 `grep`、`jq` 等工具处理
- 支持追加写入，不需要事务管理
- 文件按日期分割（`logs/YYYY-MM-DD.jsonl`）

**放弃：SQLite**

对于日志场景，SQLite 的查询优势不如 JSON Lines 的简单性。

### 决策 4：流式响应处理策略

**选择：双重记录（chunk + 重组）**

SSE 流响应以多个 `data:` 事件传输。代理将：
1. 实时转发每个 chunk 给客户端（不影响延迟）
2. 在内存中累积所有 chunks
3. 流结束后，重组为完整响应并写入日志

这样日志中既有原始 chunks（用于研究），也有重组后的完整内容（用于快速查阅）。

## Risks / Trade-offs

- **API Key 泄露风险** → 日志文件包含完整请求头（含 `x-api-key`）。缓解：日志文件权限设为 600，提供 `--redact-keys` 选项可脱敏
- **磁盘空间占用** → 长会话的完整对话历史体积较大。缓解：提供日志轮转和清理命令，默认保留 7 天
- **代理单点故障** → 代理崩溃导致 Claude Code 无法使用。缓解：代理进程崩溃时错误信息清晰，恢复方式简单（重启代理或取消环境变量）
- **SSE 超时** → 长时间流式响应可能触发代理超时。缓解：代理层不设请求超时，依赖 Anthropic SDK 的超时策略

## Migration Plan

1. 安装代理工具（`npm install` 或单文件脚本）
2. 启动代理：`node proxy.js --port 9999 --log-dir ./logs`
3. 设置环境变量：`export ANTHROPIC_BASE_URL=http://localhost:9999`
4. 正常使用 Claude Code，所有请求自动被记录
5. 查看日志：`node viewer.js --date today` 或直接 `jq . logs/YYYY-MM-DD.jsonl`

**回滚**：`unset ANTHROPIC_BASE_URL` 即可恢复直连，无需其他操作。

## Open Questions

- 是否需要支持 HTTPS 监听（针对某些强制 HTTPS 的客户端场景）？目前假设 localhost HTTP 足够。
- 日志查看器是否需要 Web UI？初期 CLI 优先，后续可选。
- 是否需要记录 Claude Code 自身的工具调用结果（非 API 层面）？当前范围仅限 HTTP 层。
