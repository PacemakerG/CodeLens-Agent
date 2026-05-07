## 1. Web Server（src/web-server.js）

- [x] 1.1 创建 `src/web-server.js`，实现基础 HTTP 服务器，监听 `localhost:9998`，支持 `--web-port` 参数
- [x] 1.2 实现静态文件服务：`GET /` → `public/index.html`，`GET /app.js` → `public/app.js`，`GET /style.css` → `public/style.css`，Content-Type 正确
- [x] 1.3 实现 `GET /api/dates`：扫描 `--log-dir` 目录，返回 `.jsonl` 文件对应的日期数组（降序）
- [x] 1.4 实现 `GET /api/requests?date=&q=`：读取指定日期的 JSONL 文件，返回摘要数组（`id`、`timestamp`、`method`、`path`、`status_code`、`duration_ms`、`response_type`），支持可选关键词过滤
- [x] 1.5 实现 `GET /api/requests/:id?date=`：在指定日期文件中精确匹配 ID，返回完整条目或 404
- [x] 1.6 实现端口冲突检测：端口被占用时打印错误并退出
- [x] 1.7 在 `src/proxy.js` 中添加 `--web` 和 `--web-port` 标志，启动时同进程内启动 Web 服务器
- [x] 1.8 在 `package.json` 中添加 `"web": "node src/web-server.js"` script

## 2. 前端页面骨架（public/index.html + public/style.css）

- [x] 2.1 创建 `public/index.html`：两栏布局，左侧为请求列表区，右侧为详情区，引入 `style.css` 和 `app.js`
- [x] 2.2 创建 `public/style.css`：实现两栏响应式布局、请求行样式（方法色块、选中高亮、stream 徽标）、标签页样式、JSON 高亮颜色变量（key/string/number/null 四色）

## 3. 前端逻辑（public/app.js）

- [x] 3.1 页面加载时调用 `/api/dates`，填充日期下拉框，自动选中最新日期并触发列表加载；无日志时显示提示文字
- [x] 3.2 实现 `loadRequestList(date, q)`：调用 `/api/requests?date=&q=`，渲染请求摘要行（时间、方法色块、路径、状态码、耗时、stream 徽标）
- [x] 3.3 实现搜索框 `input` 事件监听：用户输入后调用 `loadRequestList` 传入关键词，清空时重新加载全量列表
- [x] 3.4 实现日期下拉框 `change` 事件：切换日期时重新加载列表，清空详情面板
- [x] 3.5 实现行点击事件：调用 `/api/requests/:id?date=` 获取完整条目，高亮选中行
- [x] 3.6 实现详情面板渲染：顶部元信息（ID、时间戳、方法、路径、状态码、耗时），四个标签页（Request Headers / Request Body / Response Headers / Response），默认激活 Response 标签页
- [x] 3.7 实现 JSON 语法高亮函数：对合法 JSON 对象格式化缩进并用 `<span>` 标记 key/string/number/boolean/null，非 JSON 内容原样显示
- [x] 3.8 实现流式响应展示：Response 标签页默认显示 `response_assembled` 文本；提供 "Show raw chunks" 按钮，点击后展开 `stream_chunks` 数组（每个 chunk 分行）
- [x] 3.9 实现每个内容区域的 "Copy" 按钮：复制原始纯文本内容到剪贴板，按钮短暂显示 "Copied!"

## 4. Integration & Verification

- [x] 4.1 启动代理并让 Claude Code 发出几次请求，确认日志写入；然后运行 `node src/web-server.js` 并在浏览器打开 `http://localhost:9998`，验证请求列表正常显示
- [x] 4.2 验证点击列表项后详情面板正确显示请求头/体和响应内容（JSON 高亮生效）
- [x] 4.3 验证流式响应条目的 Response 标签页显示重组文本，"Show raw chunks" 可展开原始 chunks
- [x] 4.4 验证搜索框过滤功能和日期切换功能正常工作
- [x] 4.5 验证 `node src/proxy.js --web` 同时启动代理和 Web UI 两个端口
- [x] 4.6 更新 `README.md`，添加 Web UI 使用说明（启动命令、访问地址）
