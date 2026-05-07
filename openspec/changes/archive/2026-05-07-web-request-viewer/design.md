## Context

项目已有 `src/proxy.js`（拦截代理）、`src/logger.js`（JSONL 日志记录）和 `src/viewer.js`（CLI 查看器）。日志以 `logs/YYYY-MM-DD.jsonl` 格式存储，每行一条 JSON 记录，包含请求/响应的完整内容。

本次新增一个本地 Web UI，通过浏览器可视化浏览这些日志，无需记忆 CLI 命令。

## Goals / Non-Goals

**Goals:**
- 提供本地 HTTP 服务器，暴露读取日志的 REST API
- 单页面 Web 应用：左侧请求列表 + 右侧详情面板（主从布局）
- 请求列表支持按日期切换、关键词过滤
- 详情面板展示请求头/体、响应头/体，JSON 内容格式化显示
- 零依赖前端（原生 HTML/CSS/JS），无需构建工具

**Non-Goals:**
- 实时推送（WebSocket/SSE）——刷新页面或手动轮询即可
- 用户认证/权限控制（仅限 localhost）
- 修改或删除日志的操作
- 移动端适配

## Decisions

### 决策 1：Web 服务器实现 — Express vs 内置 http 模块

**选择：内置 `http` 模块**

- 零额外依赖，与现有 `proxy.js` 风格一致
- API 路由简单（仅 3 个端点），不需要框架
- 静态文件服务用 `fs.readFileSync` + `Content-Type` 映射即可

**放弃：Express**

对于仅有 3 个 API 路由 + 静态文件的场景，引入 Express 是过度设计。

### 决策 2：前端架构 — SPA 框架 vs 原生 JS

**选择：原生 HTML + CSS + JavaScript（无框架）**

- 无需构建步骤（Webpack/Vite），直接 `public/` 目录托管
- 数据量小（按日查看），DOM 操作无性能瓶颈
- 维护简单，不引入 React/Vue 的升级负担

**放弃：React/Vue**

工具性质的 UI，功能固定，原生 JS 足以胜任。

### 决策 3：JSON 高亮渲染 — 第三方库 vs 自实现

**选择：内联自实现（正则替换）**

- 无网络请求依赖（完全离线可用）
- 高亮逻辑仅需区分 string/number/boolean/null/key，20 行 JS 可实现
- 样式通过 CSS 变量控制，易于调整

**放弃：highlight.js / Prism.js**

需要额外加载脚本文件，且对 JSON 渲染是大炮打蚊子。

### 决策 4：API 设计

三个端点：
- `GET /api/dates` — 返回所有有日志的日期列表（降序）
- `GET /api/requests?date=YYYY-MM-DD&q=keyword` — 返回指定日期的请求摘要列表，支持可选关键词过滤
- `GET /api/requests/:id?date=YYYY-MM-DD` — 返回指定 ID 的完整日志条目

ID 查找在指定日期文件内精确匹配，不跨日期搜索（前端已知日期上下文）。

### 决策 5：与 proxy.js 的集成方式

**选择：`--web` 标志，在同一进程内启动 Web 服务器**

`node src/proxy.js --web` 同时启动代理（9999）和 Web UI（9998）。Web 服务器读取同一 `--log-dir`，无需进程间通信。

也可单独运行：`node src/web-server.js --log-dir ./logs`。

## Risks / Trade-offs

- **大日志文件加载慢** → API 返回摘要列表（不含完整 body），详情按需加载；单日超过 1000 条时前端分页显示
- **并发写入冲突** → Web 服务器只读，不存在写入冲突
- **端口占用** → `--web-port` 参数可自定义，默认 9998；启动时检测端口冲突

## Open Questions

- 是否需要自动刷新（轮询最新请求）？初期手动刷新，后续可选。
- 详情面板是否展示原始 SSE chunks？默认只展示重组后的文本，但可折叠展开原始 chunks。
