## ADDED Requirements

### Requirement: Proxy server startup
代理服务器 SHALL 在指定本地端口启动，并接受来自 Claude Code 的 HTTP 请求。

#### Scenario: Default startup
- **WHEN** 用户运行 `node proxy.js` 不带参数
- **THEN** 代理在 `localhost:9999` 启动，并打印启动日志（端口号、日志目录路径）

#### Scenario: Custom port startup
- **WHEN** 用户运行 `node proxy.js --port 8888`
- **THEN** 代理在 `localhost:8888` 启动

#### Scenario: Port conflict
- **WHEN** 指定端口已被占用
- **THEN** 代理打印明确错误信息并退出，不静默失败

### Requirement: Transparent request forwarding
代理 SHALL 将所有收到的 HTTP 请求原样转发至 `https://api.anthropic.com`，保留所有请求头和请求体。

#### Scenario: Standard API request forwarding
- **WHEN** Claude Code 发送 POST 请求到代理的 `/v1/messages`
- **THEN** 代理将请求（含完整 headers 和 body）转发至 `https://api.anthropic.com/v1/messages`
- **THEN** 将响应原样返回给 Claude Code，状态码和响应头保持不变

#### Scenario: Path and method preservation
- **WHEN** 收到任意 HTTP 方法（GET/POST/DELETE 等）和路径的请求
- **THEN** 代理保留原始 HTTP 方法和路径进行转发

### Requirement: Streaming response passthrough
代理 SHALL 支持 SSE（Server-Sent Events）流式响应的透明透传，不引入额外延迟。

#### Scenario: SSE stream forwarding
- **WHEN** Anthropic API 返回 `Content-Type: text/event-stream` 的流式响应
- **THEN** 代理实时将每个 SSE chunk 转发给 Claude Code
- **THEN** 客户端与真实 API 之间的首字节时间（TTFB）增加不超过 50ms

#### Scenario: Stream completion
- **WHEN** SSE 流正常结束（收到 `[DONE]` 事件）
- **THEN** 代理正确关闭流并触发日志写入

### Requirement: Error handling and resilience
代理 SHALL 在上游 API 不可达或返回错误时，将错误信息透明传递给客户端。

#### Scenario: Upstream API error
- **WHEN** Anthropic API 返回 4xx 或 5xx 响应
- **THEN** 代理将原始错误响应（含状态码和响应体）转发给 Claude Code，不进行修改

#### Scenario: Network failure
- **WHEN** 无法连接到 `api.anthropic.com`
- **THEN** 代理返回 502 Bad Gateway 响应，并记录错误日志
