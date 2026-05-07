## ADDED Requirements

### Requirement: Date selector
页面 SHALL 提供日期选择器，用于切换要查看的日志日期。

#### Scenario: Initial load shows latest date
- **WHEN** 页面首次加载
- **THEN** 自动选中最新有日志的日期，并加载该日期的请求列表

#### Scenario: Switch date
- **WHEN** 用户从下拉列表选择另一个日期
- **THEN** 请求列表更新为所选日期的内容，详情面板清空

#### Scenario: No logs available
- **WHEN** `GET /api/dates` 返回空数组
- **THEN** 显示提示文字 "No logs found. Start the proxy to begin recording."

### Requirement: Request list display
页面 SHALL 在左侧面板展示当前日期的请求摘要列表。

#### Scenario: List renders request rows
- **WHEN** 日期的请求数据加载完成
- **THEN** 每行显示：时间（HH:mm:ss）、HTTP 方法（色块标识 POST/GET）、路径、状态码、耗时

#### Scenario: Streaming badge
- **WHEN** 某条请求的 `response_type` 为 `"stream"`
- **THEN** 该行显示 "stream" 徽标以区分流式响应

#### Scenario: Empty date
- **WHEN** 所选日期无请求记录
- **THEN** 列表区域显示 "No requests for this date."

### Requirement: Keyword filter
页面 SHALL 提供搜索框，实时过滤请求列表。

#### Scenario: Filter on input
- **WHEN** 用户在搜索框输入关键词
- **THEN** 列表仅显示请求体或响应内容中匹配的条目（通过 `/api/requests?q=` 重新请求）

#### Scenario: Clear filter
- **WHEN** 用户清空搜索框
- **THEN** 列表恢复显示全部请求

### Requirement: Request selection
用户 SHALL 能通过点击列表项选中请求，触发详情加载。

#### Scenario: Click to select
- **WHEN** 用户点击列表中的某一行
- **THEN** 该行高亮显示为选中状态，右侧详情面板加载该请求的完整内容

#### Scenario: Selected state persists on filter
- **WHEN** 用户在已选中某请求的情况下修改搜索词
- **THEN** 若选中项仍在过滤结果中，保持其高亮状态；否则清空详情面板
