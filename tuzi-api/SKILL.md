---
name: tuzi-api
description: "兔子 API 统一调用工具——对话、生图、音乐生成的底层 Skill，被其他 Skill 编排调用或独立使用。"
description_zh: "兔子 API 统一调用：对话 / 生图 / Suno 音乐生成"
description_en: "Tuzi API unified client for chat, image generation, and Suno music. Designed as a lower-level tool skill."
version: 1.0.0
allowed-tools: run_python, bash
metadata: {"clawdbot":{"emoji":"🐰","requires":{"env":["TUZI_API_KEY"]}}}
---

# Tuzi API — 兔子统一调用 Skill

对接兔子 API（`api.tu-zi.com`）的底层工具 Skill。提供三大能力模块：

| 模块 | Base Path | 用途 |
|------|-----------|------|
| Chat | `/v1/chat/completions` | 对话问答、指令执行 |
| Image | `/v1/images/generations` | 文本生图 |
| Suno | `/suno/submit/*`, `/suno/fetch/*` | 歌词生成、歌曲生成、任务查询 |

## 认证

**环境变量**：`TUZI_API_KEY`（值为 `sk-xxx`）

> ⚠️ **安全**：API Key 仅从环境变量读取，绝不硬编码。首次使用时通过 `run_python` 写入 shell profile。

**首次设置**（仅当 `$TUZI_API_KEY` 为空时执行）：
```python
import os
key = os.environ.get("TUZI_API_KEY", "")
if not key:
    # 将 key 写入 ~/.zshrc（或 ~/.bashrc）
    # 然后 export 使当前会话生效
    ...
```

## 通用调用模式

所有请求通过 `run_python` + `urllib` 发起（绕过 bash 弹窗），统一模板：

```python
import urllib.request, json, os

BASE = "https://api.tu-zi.com"
KEY  = os.environ["TUZI_API_KEY"]

def tuzi(method, path, body=None):
    url = f"{BASE}{path}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KEY}"
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())
```

---

## 模块 1：Chat（对话）

**POST** `/v1/chat/completions`

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | ✅ | 模型名，如 `gpt-4o`, `gpt-5`, `claude-sonnet-4-20250514` |
| messages | array | ✅ | 对话消息数组 |
| temperature | float | ❌ | 0-2，默认 0.7 |
| stream | bool | ❌ | 流式输出，默认 false |
| max_tokens | int | ❌ | 最大生成 token 数 |

### 调用模板

```python
result = tuzi("POST", "/v1/chat/completions", {
    "model": "gpt-4o",
    "messages": [
        {"role": "system", "content": "你是一个音乐制作人"},
        {"role": "user", "content": "帮我写一段关于城市的歌词"}
    ],
    "temperature": 0.8,
    "stream": False
})
print(result["data"]["choices"][0]["message"]["content"])
```

### 被其他 Skill 调用时的约定

- 调用方 Skill 负责组装 `messages`，本 Skill 只做 HTTP 转发
- 返回原始 JSON，由调用方解析
- 如需流式，调用方应设置 `"stream": True` 并自行处理 SSE

---

## 模块 2：Image（生图）

**POST** `/v1/images/generations`

### 支持模型

| 模型 | 能力 | 特点 |
|------|------|------|
| `gpt-image-2` | 文生图 + 图生图 | GPT Image 2，高质量，支持 `image` 参数做图生图 |
| `gemini-3.1-flash-image-preview` | 文生图 | nano-banana-2，速度快，适合快速迭代 |

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | ✅ | 模型名，见上表 |
| prompt | string | ✅ | 图像描述 |
| image | string | ❌ | 参考图片 URL（图生图，仅 gpt-image-2） |
| size | string | ❌ | 如 `1024x1024`, `1536x1024`, `1024x1536`，默认 `1024x1024` |
| n | int | ❌ | 生成数量，默认 1 |

### 文生图

```python
result = tuzi("POST", "/v1/images/generations", {
    "model": "gpt-image-2",
    "prompt": "一只戴蓝色围巾的兔子，卡通风格，高清",
    "size": "1024x1024",
    "n": 1
})
images = result["data"]["images"]
for img in images:
    print(img["url"])
```

### 图生图（仅 gpt-image-2）

```python
result = tuzi("POST", "/v1/images/generations", {
    "model": "gpt-image-2",
    "prompt": "图中角色站起来指挥交响乐团",
    "image": "https://example.com/source.png",
    "size": "1024x1024",
    "n": 1
})
```

### 下载图片到本地

```python
import urllib.request, os

def download_image(url, save_path):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    urllib.request.urlretrieve(url, save_path)
    return save_path
```

---

## 模块 3：Suno（音乐）

详细规范见 [./references/suno-api.md](./references/suno-api.md)。

### 3a. 生成歌词

**POST** `/suno/submit/lyrics`

```python
result = tuzi("POST", "/suno/submit/lyrics", {
    "prompt": "歌颂可爱的兔子"
})
# 响应: {"code": "success", "data": "<task_id>"}
task_id = result["data"]  # 注意：外层 data 直接是 task_id 字符串
```

歌词内容需通过 3c 的 fetch 接口轮询获取。

### 3b. 生成歌曲

**POST** `/suno/submit/music`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | ✅ | 歌词文本（含结构标签如 `[Verse]`）；为空则自动生成 |
| tags | string | ✅ | 风格标签，如 `emotional punk` |
| mv | string | ✅ | 模型版本，如 `chirp-v4` |
| title | string | ✅ | 歌曲标题 |

```python
result = tuzi("POST", "/suno/submit/music", {
    "prompt": "[Verse]\nWalking down the streets\nBeneath the city lights",
    "tags": "emotional punk",
    "mv": "chirp-v4",
    "title": "City Lights"
})
# 响应格式同 lyrics: {"code": "success", "data": "<task_id>"}
task_id = result["data"]
print(f"Task ID: {task_id}")
```

### 3c. 轮询任务状态

**GET** `/suno/fetch/{task_id}`

```python
import time

def wait_for_suno(task_id, interval=10, max_wait=300):
    """轮询直到任务完成，返回最终结果
    
    响应结构（已验证）：
    {
      "code": "success",
      "data": {
        "task_id": "...",
        "action": "LYRICS" | "MUSIC",
        "status": "SUBMITTED" | "SUCCESS",
        "data": {
          "status": "complete",
          "text": "歌词文本",          # LYRICS 时
          "title": "歌曲标题",
          "tags": ["pop, upbeat"],
          "audio_url": "...",       # MUSIC 时
          "video_url": "...",       # MUSIC 时
          ...
        }
      }
    }
    """
    elapsed = 0
    while elapsed < max_wait:
        result = tuzi("GET", f"/suno/fetch/{task_id}")
        inner = result.get("data", {}).get("data", {})
        # LYRICS: inner 是 dict；MUSIC: inner 是 list（2首歌）
        if isinstance(inner, list):
            inner_status = inner[0].get("status", "") if inner else ""
        else:
            inner_status = inner.get("status", "")
        outer_status = result.get("data", {}).get("status", "")
        if inner_status == "complete" or outer_status == "SUCCESS":
            return result
        print(f"[{elapsed}s] 状态: {outer_status}，继续等待...")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"Suno 任务 {task_id} 超时（{max_wait}s）")
```

### 3d. 下载音频到本地

```python
import urllib.request, os

def download_audio(url, save_path):
    """下载 Suno 生成的音频文件"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as r:
        with open(save_path, "wb") as f:
            f.write(r.read())
    return save_path
```

---

## 被 ai-music-producer 调用的接口约定

当 `ai-music-producer` 等 Skill 需要使用 Suno 生成时：

1. **检测**：`which mmx` → 如果不存在，提示 agent 使用本 Skill 的 Suno 路径
2. **调用方式**：编排 Skill 组装 `prompt/tags/mv/title`，通过 `run_python` 调用本 Skill 的模板代码
3. **返回值**：包含 `task_id`、音频 URL、歌词文本的 dict
4. **轮询**：编排 Skill 调用 `wait_for_suno()` 等待完成

---

## 错误处理

| 场景 | 处理 |
|------|------|
| `TUZI_API_KEY` 未设置 | 提示用户设置环境变量，并引导首次设置流程 |
| HTTP 4xx | 解析 `code` 和 `message`，向用户报告具体错误 |
| HTTP 5xx | 重试 1 次后报告 |
| Suno 任务超时 | 建议检查任务状态或重试 |
| 网络超时 | 增大 `timeout` 参数重试 1 次 |

---

## 独立使用示例

用户可直接说：
- "用兔子 API 聊天" → 使用 Chat 模块
- "用兔子 API 生成一张图" → 使用 Image 模块
- "用 Suno 生成一首歌" → 使用 Suno 模块
- "查一下 Suno 任务状态" → 使用 Fetch 模块
