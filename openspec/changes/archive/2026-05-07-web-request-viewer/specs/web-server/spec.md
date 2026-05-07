## ADDED Requirements

### Requirement: Web server startup
Web 服务器 SHALL 在本地端口启动，提供静态文件和 REST API，仅绑定 localhost。

#### Scenario: Standalone startup
- **WHEN** 用户运行 `node src/web-server.js`
- **THEN** 服务器在 `localhost:9998` 启动并打印访问地址

#### Scenario: Custom port
- **WHEN** 用户运行 `node src/web-server.js --web-port 8080`
- **THEN** 服务器在 `localhost:8080` 启动

#### Scenario: Integrated startup via proxy
- **WHEN** 用户运行 `node src/proxy.js --web`
- **THEN** 代理（默认 9999）和 Web UI（默认 9998）在同一进程内同时启动

#### Scenario: Port conflict
- **WHEN** 指定 Web 端口已被占用
- **THEN** 打印明确错误信息并退出

### Requirement: Static file serving
服务器 SHALL 将 `public/` 目录下的文件作为静态资源提供。

#### Scenario: Serve index page
- **WHEN** 浏览器请求 `GET /`
- **THEN** 返回 `public/index.html`，Content-Type 为 `text/html`

#### Scenario: Serve JS and CSS assets
- **WHEN** 浏览器请求 `GET /app.js` 或 `GET /style.css`
- **THEN** 返回对应文件，Content-Type 正确（`application/javascript` / `text/css`）

### Requirement: API — list available dates
`GET /api/dates` SHALL 返回所有有日志记录的日期列表。

#### Scenario: Dates present
- **WHEN** `logs/` 目录下存在 `.jsonl` 文件
- **THEN** 返回 JSON 数组，格式 `["2024-01-15", "2024-01-14", ...]`，按日期降序排列

#### Scenario: No logs
- **WHEN** `logs/` 目录为空或不存在
- **THEN** 返回空数组 `[]`，HTTP 200

### Requirement: API — list requests
`GET /api/requests?date=YYYY-MM-DD&q=keyword` SHALL 返回指定日期的请求摘要列表。

#### Scenario: List all requests for a date
- **WHEN** 请求 `GET /api/requests?date=2024-01-15`
- **THEN** 返回 JSON 数组，每项包含 `id`、`timestamp`、`method`、`path`、`status_code`、`duration_ms`、`response_type`

#### Scenario: Filter by keyword
- **WHEN** 请求 `GET /api/requests?date=2024-01-15&q=hello`
- **THEN** 仅返回请求体或响应内容中包含 "hello"（大小写不敏感）的条目摘要

#### Scenario: Date not found
- **WHEN** 指定日期无日志文件
- **THEN** 返回空数组 `[]`，HTTP 200

### Requirement: API — get request detail
`GET /api/requests/:id` SHALL 返回单条请求的完整日志条目。

#### Scenario: Entry found
- **WHEN** 请求 `GET /api/requests/uuid-here?date=2024-01-15`
- **THEN** 返回完整 JSON 对象（含 `request_headers`、`request_body`、`response_headers`、`response_body` 或 `response_assembled`）

#### Scenario: Entry not found
- **WHEN** 指定 ID 在该日期文件中不存在
- **THEN** 返回 HTTP 404，body 为 `{"error": "Not found"}`
