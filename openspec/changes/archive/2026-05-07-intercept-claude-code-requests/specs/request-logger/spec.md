## ADDED Requirements

### Requirement: Structured request logging
系统 SHALL 将每个拦截到的请求以结构化 JSON 格式记录，包含完整的请求信息。

#### Scenario: Log entry structure for request
- **WHEN** 代理收到一个 HTTP 请求
- **THEN** 日志条目 SHALL 包含以下字段：
  - `id`：唯一请求 ID（UUID v4）
  - `timestamp`：ISO 8601 格式的请求时间
  - `method`：HTTP 方法
  - `path`：请求路径
  - `request_headers`：所有请求头的键值对
  - `request_body`：完整的请求体（JSON 对象，非字符串）

#### Scenario: Large request body handling
- **WHEN** 请求体超过 1MB
- **THEN** 系统仍然记录完整内容（不截断），但在日志条目中添加 `truncated: false` 标记

### Requirement: Structured response logging
系统 SHALL 将对应的响应内容记录到同一个日志条目中。

#### Scenario: Non-streaming response logging
- **WHEN** 收到非流式 JSON 响应
- **THEN** 日志条目 SHALL 追加以下字段：
  - `status_code`：HTTP 状态码
  - `response_headers`：响应头键值对
  - `response_body`：完整响应体（JSON 对象）
  - `duration_ms`：请求到响应的耗时（毫秒）

#### Scenario: Streaming response logging
- **WHEN** 收到 SSE 流式响应
- **THEN** 日志条目 SHALL 包含：
  - `response_type: "stream"`
  - `stream_chunks`：所有原始 SSE chunk 的数组
  - `response_assembled`：重组后的完整响应内容（合并所有 delta 后的文本）
  - `duration_ms`：从请求发出到流结束的总耗时

### Requirement: JSON Lines file storage
系统 SHALL 将日志条目写入本地 JSON Lines 文件，按日期组织。

#### Scenario: Daily log file creation
- **WHEN** 在某一天首次记录日志
- **THEN** 在日志目录下创建 `YYYY-MM-DD.jsonl` 文件

#### Scenario: Append-only writing
- **WHEN** 写入新的日志条目
- **THEN** 以追加方式写入文件，每条记录占一行，不覆盖历史记录

#### Scenario: Default log directory
- **WHEN** 用户未指定 `--log-dir` 参数
- **THEN** 日志写入 `./logs/` 目录（相对于代理脚本所在位置）

### Requirement: API key redaction option
系统 SHALL 提供可选的 API Key 脱敏功能。

#### Scenario: Key redaction enabled
- **WHEN** 代理以 `--redact-keys` 选项启动
- **THEN** 日志中 `x-api-key` 和 `authorization` 头的值被替换为 `***REDACTED***`

#### Scenario: Key redaction disabled (default)
- **WHEN** 代理未使用 `--redact-keys` 选项启动
- **THEN** 所有请求头（含 API Key）以原始值记录

### Requirement: Log retention management
系统 SHALL 提供日志清理功能以控制磁盘占用。

#### Scenario: Manual log cleanup
- **WHEN** 用户运行 `node proxy.js --cleanup --days 7`
- **THEN** 删除 7 天前的所有 `.jsonl` 日志文件，并打印删除文件列表
