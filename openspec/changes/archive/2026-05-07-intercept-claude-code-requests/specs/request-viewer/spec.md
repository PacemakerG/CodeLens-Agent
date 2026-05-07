## ADDED Requirements

### Requirement: List recorded requests
系统 SHALL 提供命令列出已记录的请求摘要，支持按日期筛选。

#### Scenario: List today's requests
- **WHEN** 用户运行 `node viewer.js list`
- **THEN** 输出今天所有请求的摘要列表，每行包含：请求 ID（前8位）、时间戳、HTTP 方法、路径、状态码、耗时

#### Scenario: List requests by date
- **WHEN** 用户运行 `node viewer.js list --date 2024-01-15`
- **THEN** 输出指定日期的请求摘要列表

#### Scenario: Empty log
- **WHEN** 指定日期没有日志文件或文件为空
- **THEN** 输出 `No requests found for [date]`，退出码为 0

### Requirement: View full request detail
系统 SHALL 支持通过请求 ID 查看单个请求的完整内容。

#### Scenario: View full request and response
- **WHEN** 用户运行 `node viewer.js show <request-id>`
- **THEN** 以格式化 JSON 输出该请求的完整日志条目（包含请求头、请求体、响应头、响应体）

#### Scenario: Request ID prefix matching
- **WHEN** 用户提供请求 ID 的前缀（至少4位）
- **THEN** 系统匹配第一个以该前缀开头的请求并显示
- **THEN** 如果前缀匹配多个请求，显示所有匹配的请求 ID 列表要求用户指定

#### Scenario: Request not found
- **WHEN** 提供的 ID 在所有日志中不存在
- **THEN** 输出 `Request [id] not found`，退出码为 1

### Requirement: Extract assembled response content
系统 SHALL 提供快速提取重组后响应文本的命令，方便快速查阅 AI 回复内容。

#### Scenario: Extract response text
- **WHEN** 用户运行 `node viewer.js response <request-id>`
- **THEN** 仅输出 `response_assembled` 字段的文本内容（纯文本，无 JSON 包装）

#### Scenario: Extract from non-streaming response
- **WHEN** 目标请求是非流式响应
- **THEN** 输出 `response_body.content` 中的文本内容

### Requirement: Search log content
系统 SHALL 支持在日志内容中搜索关键词。

#### Scenario: Full-text search
- **WHEN** 用户运行 `node viewer.js search "关键词"`
- **THEN** 输出所有请求/响应中包含该关键词的日志条目摘要（默认搜索最近7天）

#### Scenario: Scoped search
- **WHEN** 用户运行 `node viewer.js search "关键词" --in request`
- **THEN** 仅搜索请求体内容；`--in response` 仅搜索响应内容
