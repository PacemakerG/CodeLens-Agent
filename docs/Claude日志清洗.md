# Claude日志目录结构与文件说明

```
~/.claude/projects/
└── <project-slug>/                        # 项目目录，由工作路径转义而来（/ → -）
    ├── <sessionId>.jsonl                  # main agent 对话日志
    ├── <sessionId>/                       # 同名目录，存放该 session 的 subagent 数据
    │   └── subagents/
    │       ├── agent-<agentId>.jsonl      # subagent 对话日志（isSidechain: true）
    │       └── agent-<agentId>.meta.json  # subagent 元信息
    └── ...
```

**agentId 与文件名的对应关系**：subagent 文件名格式为 `agent-<agentId>.jsonl`，agentId 即去掉 `agent-` 前缀后的字符串。

# 日志类型

每行 JSON 的顶层 `type` 字段

| type                    | 说明　　　　　　　　　　　　　　　　　　　　　　　　　　　　 |
| -------------------------| --------------------------------------------------------------|
| `user`                  | 用户输入或工具执行结果回调　　　　　　　　　　　　　　　　　 |
| `assistant`             | AI 回复（含文字和工具调用）　　　　　　　　　　　　　　　　　|
| `system`                | 系统提示词　　　　　　　　　　　　　　　　　　　　　　　　　 |
| `attachment`            | attachment.type 字段记录了类型，需要保留用于通过uuid串联顺序 |
| `permission-mode`       | 权限模式设置，一般出现在日志首行　　　　　　　　　　　　　　 |
| `file-history-snapshot` | 文件快照元数据　　　　　　　　　　　　　　　　　　　　　　　 |
| `queue-operation`       | 当前正在处理其他任务，用户输入的消息会先入队列　　　　　　　 |
| `last-prompt`           | 用于在 /resume 会话列表　　　　　　　　　　　　　　　　　　　|

**user消息**

message.content字段一定有，可能是文本，可能是数组。
为数组时，实际测试下来长度为1，数组对象有两种, type为tool_result和text.
message.content[0].type==='text'时：

```json
{"type": "text",
  "text": "text goes here. 也可能是数字"}
```

message.content[0].type==='text'时，message.content[0].content可以是str或者列表.

```json
{"type": "tool_result",
  "tool_use_id": "toolu_bdrk_01FFDhpUtNSWSyYTmD2ZNymK",
  "content": "Launching skill: finishing-a-development-branch"}
```

```json
[{"type": "text",
   "text": "massive messages."},
  {"type": "text",
   "text": "agentId: ab49d5098e41cad37 (use SendMessage with to: \"ab49d5098e41cad37\" to continue this agent)\n<usage>total_tokens: 141696\ntool_uses: 51\nduration_ms: 322780</usage>"}]
```

**assistant消息**

实际测试的message.content都是list，长度为1。**通过message.id可以关联到同一个LLM请求。**
message.content[0].type为text或者tool_use。
message.content[0].type===tool_use的时候，有id（即tool_id）、type、name、input四个字段。
可以使用message.content[0].name处理不同的工具调用。不同工具调用的input字段内容不一样。


# 顺序识别与切分

日志行号、时间戳、uuid父子关系都能用来决定先后顺序。
目前user、assistant、system、attachment类型的消息都有 uuid和parentUuid字段，可以据此重建层级关系。

1. 首先以行号排序
2. 没有parentUuid和uuid的日志，按行号向前追溯，直到能找到有parentUuid和uuid的记录，或者找不到。(type为user、assistant、system、attachment的日志采有parentUuid和uuid)
3. 用parentUuid和uuid串联先后关系并排序。
4. 以用户真实消息作为 turn 的起点，后续所有条目归属该turn，直到下一条真实用户消息。真实用户消息（turn 根节点）：type === 'user' 且 message.content 是非空字符串。

# 关联关系

1. 原始HTTP请求响应和日志的关联:可以通过assistant日志的 message.id 字段 和 HTTP请求关联起来。但多条日志有可能关联到同一个原始请求、原始请求有可能关联不到日志，一种情况是请求小模型获取title，还有一种是compact
2. **tool调用和结果的关联**。assistant日志 message.content[].type=='tool_use' 时，message.content[].id 可以和 user message.content[].type==tool_result 的消息，通过message.content[].tool_use_id匹配上。
3. Main session和subagent的日志关联。assistant消息，类型为agent的 tool_use 消息 找到 user的tool_result消息, 再找agent即可定位到。
4. skill打标
   1. 打标。assistant 的 tool_use消息，且name=='Agent'。
   2. ❓❓❓卸载需要看http请求/上下文是否被实际压缩

