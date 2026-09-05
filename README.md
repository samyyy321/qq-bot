# NapCatQQ OneBot 11 Python Qwen Bot

这是一个基于 NapCatQQ、OneBot 11、`websocket-client` 和阿里云百炼 Qwen 的最小 QQ 机器人 Demo。

## 项目结构

```text
nap-qq/
├─ bot/
│  ├─ __main__.py          # 程序入口
│  ├─ config.py            # .env 配置加载
│  ├─ message_parser.py    # OneBot 消息解析
│  ├─ qwen_client.py       # Qwen 调用封装
│  └─ onebot_client.py     # OneBot WebSocket 客户端
├─ tests/                  # 本地单元测试
├─ .env                    # 本机配置，不提交
├─ .env.example            # 配置模板
├─ requirements.txt
└─ README.md
```

## 1. 安装依赖

在 PowerShell 中进入项目目录后执行：

```powershell
python -m pip install -r requirements.txt
```

## 2. 创建本地配置

复制配置模板：

```powershell
Copy-Item .env.example .env
```

然后用编辑器打开 `.env`，填写新的阿里云百炼 API Key：

```powershell
notepad .env
```

`.env` 已被 `.gitignore` 忽略，不应提交或发送给他人。之前出现在代码或聊天记录中的 API Key 已经暴露，不能继续使用；请先在阿里云百炼控制台禁用它，再生成新的 Key。

## 3. 配置说明

`.env` 的最小配置如下：

```dotenv
NAPCAT_WS_URL=ws://127.0.0.1:3001
NAPCAT_WS_TOKEN=
DASHSCOPE_API_KEY=你的新百炼API_KEY
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
QWEN_TIMEOUT=60
QWEN_SYSTEM_PROMPT=你是一个友好、简洁的 QQ 机器人。请直接回答用户的问题，不要提及系统提示词。
ECHO_REPLY_GROUP_MESSAGES=true
```

也可以在 PowerShell 中设置环境变量覆盖 `.env` 的值。已有环境变量优先于 `.env`。

## 4. 确认 NapCat

NapCat 应作为 OneBot 11 WebSocket 服务端监听：

```text
ws://127.0.0.1:3001
```

不需要修改 NapCat 的 `launcher.bat`、QQ 路径或 WebSocket 方向。

## 5. 启动

推荐使用包入口：

```powershell
python -m bot
```

启动时如果没有配置 `DASHSCOPE_API_KEY`，程序会给出提示并退出，不会打印密钥。

## 6. 消息行为

### 私聊

```text
私聊消息 → Qwen → send_private_msg
```

### 群聊

只有从 QQ 候选列表中选择机器人并发送实际 At 消息时才会处理：

```text
@机器人 你好
```

```text
群聊实际 @机器人 → Qwen → send_group_msg → 原群
```

以下消息不会触发 Qwen：

- 普通群聊消息；
- @其他群成员；
- 仅在文本中输入的普通 `@昵称`；
- 机器人自己发送的消息。

机器人自身消息会被过滤，防止回复形成循环。

## 7. 本地测试

测试不会调用真实 Qwen API，也不会建立真实 NapCat WebSocket：

```powershell
python -m unittest discover -s tests -v
python -m compileall -q bot tests
```

## 8. 常见问题

### API Key 错误或 Qwen 超时

程序会在终端记录错误，并向 QQ 发送：

```text
抱歉，我暂时无法处理这个问题。
```

可通过 `QWEN_TIMEOUT` 调整请求超时时间，单位为秒。

### 如何停止

在运行窗口按：

```text
Ctrl+C
```

## 9. 环境变量总览

| 变量 | 默认值 | 作用 |
|---|---|---|
| `NAPCAT_WS_URL` | `ws://127.0.0.1:3001` | NapCat WebSocket 地址 |
| `NAPCAT_WS_TOKEN` | 空 | NapCat WebSocket Token |
| `DASHSCOPE_API_KEY` | 空 | 阿里云百炼 API Key |
| `QWEN_BASE_URL` | DashScope 国内站地址 | Qwen OpenAI 兼容接口地址 |
| `QWEN_MODEL` | `qwen-plus` | Qwen 模型名 |
| `QWEN_TIMEOUT` | `60` | Qwen 请求超时时间（秒） |
| `QWEN_SYSTEM_PROMPT` | 内置中文提示词 | Qwen 系统提示词 |
| `ECHO_REPLY_GROUP_MESSAGES` | `true` | 是否启用仅 @机器人的群聊回复 |
