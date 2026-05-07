## Why

在使用 Claude Code 进行 AI 辅助编程时，我们无法看到底层与 Anthropic API 之间传输的原始请求和响应内容，导致难以调试、分析和优化 AI 交互过程。通过拦截并记录这些原始数据，可以实现深度分析、审计和研究目的。

## What Changes

- 新增一个 HTTP 代理/拦截层，位于 Claude Code 与 Anthropic API 之间
- 捕获所有进出流量的原始 HTTP 请求头、请求体和响应体
- 将拦截到的数据持久化存储到本地文件或数据库中
- 提供可配置的过滤和格式化选项
- 支持流式响应（SSE/streaming）的完整记录

## Capabilities

### New Capabilities

- `request-interceptor`: 代理服务器，透明地转发 Claude Code 请求到 Anthropic API 并捕获完整的请求/响应内容
- `request-logger`: 将拦截到的请求和响应内容结构化存储，支持 JSON Lines 格式和按会话分组
- `request-viewer`: 查看和检索已记录的请求/响应日志的 CLI 工具或简单 Web 界面

### Modified Capabilities

<!-- No existing capabilities are being modified -->

## Impact

- **运行环境**: 需要设置 `ANTHROPIC_BASE_URL` 环境变量指向本地代理，或通过系统代理设置拦截
- **依赖**: 需要 Node.js/Python 代理库（如 `mitmproxy`、`http-proxy` 或自定义实现）
- **存储**: 本地文件系统或 SQLite 数据库存储拦截记录
- **安全**: 记录内容包含 API Key 和对话内容，需注意访问控制和数据安全
- **性能**: 代理层引入的延迟应最小化，不影响正常使用体验
