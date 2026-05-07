## Why

CLI 工具（`viewer.js`）查看拦截日志需要记忆命令语法，且无法直观对比请求与响应、格式化展示 JSON 内容。提供一个本地 Web UI，让用户通过浏览器实时浏览、搜索和查看原始请求/响应内容，大幅降低使用门槛。

## What Changes

- 新增本地 Web 服务器，提供单页面应用（SPA）用于浏览日志
- 网页左侧显示请求列表，右侧显示选中请求的完整内容（请求头/体、响应头/体）
- 支持按关键词搜索请求，按日期切换日志
- JSON 内容语法高亮，流式响应展示重组后的完整文本
- Web 服务与现有 `proxy.js` 集成，代理运行时可同步开启 Web UI

## Capabilities

### New Capabilities

- `web-server`: 本地 HTTP 服务器，提供静态文件和读取 JSONL 日志的 REST API
- `request-list-ui`: 网页请求列表面板，支持分页、日期选择和关键词过滤
- `request-detail-ui`: 网页请求详情面板，展示完整请求/响应内容（JSON 语法高亮、流式响应文本）

### Modified Capabilities

<!-- No existing capabilities are being modified -->

## Impact

- **新文件**：`src/web-server.js`（Express/内置 http 服务）、`public/index.html`、`public/app.js`、`public/style.css`
- **修改**：`src/proxy.js` 可选集成 `--web` 标志启动 Web UI
- **依赖**：无需额外 npm 包（使用内置 `http` 模块 + 原生 JS），或可选引入轻量级依赖
- **端口**：Web UI 默认监听 `localhost:9998`，与代理端口（9999）分开
- **安全**：仅绑定 localhost，不对外暴露
