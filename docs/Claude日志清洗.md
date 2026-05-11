# 目录结构与文件说明

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

# 先后关系处理

日志行号、时间戳、uuid父子关系都能用来决定先后顺序。**最准确的还是uuid-partentUuid关系。**

1. user、assistant、system、attachment类型的消息都有 uuid和parentUuid字段，可以据此重建层级关系。
2. ~~在展示成树形目录结构的时候需要注意，如果直接原样展示树形关系，会导致树很深。可行的方案是非根节点全部挂在根节点下，当做二级节点展示。~~
3. 当前规则：

  以用户真实消息作为 turn 的起点，后续所有条目归属该
  turn，直到下一条真实用户消息。

  具体判定：
  - 真实用户消息（turn 根节点）：type === 'user' 且 message.content
  是非空字符串
  - 子节点：不满足上述条件的所有其他条目（assistant、system、attachmen
  t、type=user 但 content 是数组的 tool_result
  消息等），都挂在最近一个真实用户消息下面
  - Preamble：第一条真实用户消息之前的条目，单独归为一个无根节点的平铺
   turn

# 日志类型

每行 JSON 的顶层 `type` 字段

| type | 说明 | 处理方式 |
|------|------|----------|
| `user` | 用户输入或工具执行结果回调 | ✅ 保留 |
| `assistant` | AI 回复（含文字和工具调用） | ✅ 保留 |
| `system` | 系统提示词 | ✅ 保留 |
| `permission-mode` | 权限模式设置，一般出现在日志首行 | ❌ 丢弃 |
| `file-history-snapshot` | 文件快照元数据 | ❌ 丢弃 |
| `attachment` | attachment.type 字段记录了类型，需要保留用于通过uuid串联顺序 |  ✅ 保留 |
| `queue-operation` | 当前正在处理其他任务，用户输入的消息会先入队列 | ❌ 丢弃 |


# 关联关系

1. 原始HTTP请求响应和日志的关联，✅（1）可以通过日志的 message.id 字段 和 HTTP请求关联起来。（2）**入口是assistant的消息**。
1. tool调用和结果的关联。assistant日志 message.content[].type==tool_use 时，message.content[].id 可以和 user message.content[].type==tool_result 的消息，通过message.content[].tool_use_id匹配上。✅
1. Main agent和subagent的日志关联。类型为agent的 tool_use 消息 找到 tool_result, 再找agent即可定位到。✅
2. skill作用域展示⚠️

