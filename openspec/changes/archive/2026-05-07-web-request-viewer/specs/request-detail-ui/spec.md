## ADDED Requirements

### Requirement: Detail panel layout
详情面板 SHALL 以标签页方式组织请求和响应内容。

#### Scenario: Panel tabs
- **WHEN** 用户选中一个请求
- **THEN** 详情面板显示四个标签页：Request Headers、Request Body、Response Headers、Response（响应内容）

#### Scenario: Default active tab
- **WHEN** 详情面板首次加载
- **THEN** 默认激活 "Response" 标签页（最常用）

#### Scenario: Empty state
- **WHEN** 未选中任何请求
- **THEN** 详情面板显示占位提示 "Select a request to view details"

### Requirement: JSON syntax highlighting
系统 SHALL 对 JSON 格式的请求体和响应体进行语法高亮渲染。

#### Scenario: Highlight JSON object
- **WHEN** 内容为合法 JSON 对象或数组
- **THEN** 以不同颜色区分 key（蓝色）、string 值（绿色）、number/boolean/null（橙色），并缩进格式化

#### Scenario: Non-JSON content fallback
- **WHEN** 内容不是合法 JSON（如纯文本）
- **THEN** 以等宽字体原样显示，不报错

### Requirement: Streaming response display
系统 SHALL 对流式响应提供专属展示方式。

#### Scenario: Show assembled text
- **WHEN** 请求的 `response_type` 为 `"stream"`
- **THEN** Response 标签页默认展示 `response_assembled`（重组后的完整文本）

#### Scenario: Toggle raw chunks
- **WHEN** 用户点击 "Show raw chunks" 按钮
- **THEN** 展开显示 `stream_chunks` 数组中的原始 SSE 数据，每个 chunk 分行显示

### Requirement: Copy to clipboard
系统 SHALL 提供一键复制功能，方便用户复制内容。

#### Scenario: Copy button per section
- **WHEN** 用户点击某个内容区域的 "Copy" 按钮
- **THEN** 该区域的原始内容（未高亮的纯文本 JSON）被复制到剪贴板，按钮短暂显示 "Copied!"

### Requirement: Request metadata header
详情面板顶部 SHALL 显示请求的关键元信息。

#### Scenario: Metadata display
- **WHEN** 详情面板加载完成
- **THEN** 顶部显示：完整请求 ID、时间戳、HTTP 方法、路径、状态码、耗时（ms）
