## 1. Project Setup

- [x] 1.1 初始化 Node.js 项目（`npm init`），添加依赖：`node-fetch`（或使用内置 `http`/`https` 模块）、`uuid`、`commander`
- [x] 1.2 创建项目目录结构：`src/proxy.js`、`src/logger.js`、`src/viewer.js`、`logs/`（gitignore）
- [x] 1.3 在 `package.json` 中添加 scripts：`"proxy": "node src/proxy.js"`、`"viewer": "node src/viewer.js"`

## 2. Request Interceptor（代理服务器）

- [x] 2.1 实现基础 HTTP 服务器，监听指定端口（默认 9999），支持 `--port` 参数
- [x] 2.2 实现请求转发逻辑：将收到的请求（方法、路径、headers、body）完整转发至 `https://api.anthropic.com`
- [x] 2.3 实现非流式响应透传：将上游响应（状态码、headers、body）原样返回给客户端
- [x] 2.4 实现 SSE 流式响应透传：检测 `Content-Type: text/event-stream`，逐 chunk 转发，保持低延迟
- [x] 2.5 实现上游错误处理：4xx/5xx 原样透传，网络不可达返回 502 并记录错误日志
- [x] 2.6 实现端口冲突检测：启动时若端口占用，打印明确错误信息并退出

## 3. Request Logger（日志记录器）

- [x] 3.1 实现 `generateLogEntry(request)` 函数，构建包含 `id`（UUID v4）、`timestamp`、`method`、`path`、`request_headers`、`request_body` 的日志对象
- [x] 3.2 实现非流式响应日志补全：在收到响应后追加 `status_code`、`response_headers`、`response_body`、`duration_ms` 到日志条目
- [x] 3.3 实现流式响应日志记录：在内存中累积所有 SSE chunks，流结束后写入 `stream_chunks` 数组和 `response_assembled`（合并所有 delta 文本）
- [x] 3.4 实现 JSON Lines 文件写入：按 `YYYY-MM-DD.jsonl` 命名，追加写入，每行一条完整 JSON
- [x] 3.5 实现 `--redact-keys` 选项：启用时将 `x-api-key` 和 `authorization` 头值替换为 `***REDACTED***`
- [x] 3.6 实现 `--cleanup --days N` 功能：删除 N 天前的 `.jsonl` 文件并打印文件列表

## 4. Request Viewer（日志查看器）

- [x] 4.1 实现 `list` 子命令：读取指定日期（默认今天）的 `.jsonl` 文件，输出请求摘要列表（ID 前8位、时间、方法、路径、状态码、耗时）
- [x] 4.2 实现 `show <id>` 子命令：支持完整 ID 和前缀匹配，以格式化 JSON 输出完整日志条目
- [x] 4.3 实现 `show` 的多匹配处理：前缀匹配多个时列出所有匹配 ID，要求用户指定完整 ID
- [x] 4.4 实现 `response <id>` 子命令：提取并输出 `response_assembled` 或 `response_body.content` 的纯文本内容
- [x] 4.5 实现 `search <keyword>` 子命令：在最近7天日志中全文搜索，支持 `--in request` 和 `--in response` 范围限定

## 5. Integration & Testing

- [x] 5.1 编写使用说明 `README.md`：包含快速启动步骤（安装、启动代理、设置环境变量、查看日志）
- [x] 5.2 手动集成测试：设置 `ANTHROPIC_BASE_URL=http://localhost:9999` 后运行 Claude Code，验证：请求被正常转发、日志文件生成、流式响应正常工作
- [x] 5.3 验证 `viewer.js list` 能正确列出拦截到的请求，`show` 能展示完整内容
- [x] 5.4 验证 `--redact-keys` 选项正确脱敏 API Key
