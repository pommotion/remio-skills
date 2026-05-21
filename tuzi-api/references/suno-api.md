# Suno API 详细规范

兔子 API 封装的 Suno 接口文档。本文件供需要了解完整字段细节的场景按需加载。

## Base URL

`https://api.tu-zi.com`

## 认证

```
Authorization: Bearer <TUZI_API_KEY>
Content-Type: application/json
```

> **注意**：Wiki 示例中部分代码用 `sk-**` 直接传（无 Bearer 前缀），但总览文档明确要求 `Bearer` 前缀。为兼容性，本 Skill 统一使用 `Bearer` 前缀。

---

## 1. 生成歌词

**POST** `/suno/submit/lyrics`

### 请求

```json
{
  "prompt": "歌颂可爱的兔子API服务商"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | ✅ | 歌词主题描述 |

### 响应（已验证）

```json
{
  "code": "success",
  "data": "<task_id>"
}
```

外层 `data` 直接是 task_id 字符串。歌词内容需通过 fetch 接口查询获取。

---

## 2. 生成歌曲

**POST** `/suno/submit/music`

### 请求

```json
{
  "prompt": "[Verse]\nWalking down the streets\nBeneath the city lights\n...",
  "tags": "emotional punk",
  "mv": "chirp-v4",
  "title": "City Lights"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | ✅ | 歌词文本。支持 Suno 结构标签：`[Verse]`, `[Chorus]`, `[Bridge]`, `[Outro]` 等。**为空时可由系统自动生成歌词**（需配合 `gpt_description_prompt` 参数） |
| tags | string | ✅ | 风格标签，逗号分隔。如 `"emotional punk"`, `"chinese ambient, cinematic"`, `"indie folk, acoustic"` |
| mv | string | ✅ | 模型版本。已知值：`chirp-v4`（推荐） |
| title | string | ✅ | 歌曲标题 |

### Prompt 歌词结构示例

```
[Verse]
第一段歌词...

[Chorus]
副歌部分...

[Verse 2]
第二段歌词...

[Bridge]
桥段...

[Outro]
尾声...
```

### 响应（已验证）

```json
{
  "code": "success",
  "data": "<task_id>"
}
```

同 lyrics，外层 `data` 是 task_id 字符串。

---

## 3. 查询任务

**GET** `/suno/fetch/{task_id}`

### 请求

无需请求体，在 URL path 中传入 `task_id`。

### 响应（已验证 — Lyrics 任务）

```json
{
  "code": "success",
  "data": {
    "task_id": "...",
    "action": "LYRICS",
    "status": "SUBMITTED",
    "submit_time": 1779112646,
    "start_time": 1779112646,
    "finish_time": 1779112655,
    "progress": "100%",
    "data": {
      "data": {
        "tags": ["pop, upbeat, Mandarin Chinese"],
        "text": "[Verse]\n...歌词内容...",
        "title": "失眠代码",
        "status": "complete",
        "error_message": ""
      },
      "action": "LYRICS",
      "status": "SUCCESS",
      ...
    }
    # ⚠️ MUSIC 任务时 data.data 是数组而非对象：
    # "data": [
    #   {"id": "...", "audio_url": "...", "duration": 181.96, "metadata": {"key": "B_major", "avg_bpm": 85}, ...},
    #   {"id": "...", "audio_url": "...", "duration": 174.36, "metadata": {"key": "Db_major", "avg_bpm": 126}, ...}
    # ]
  }
}
```

### 关键字段路径

| 路径 | 说明 |
|------|------|
| `data.status` | 外层状态：`SUBMITTED` → `SUCCESS` |
| `data.data` | **LYRICS**: 对象；**MUSIC**: 数组（含 2 首歌） |
| `data.data.data.text` | 歌词文本（仅 LYRICS） |
| `data.data.data.title` | 歌曲标题（仅 LYRICS） |
| `data.data[N].audio_url` | 音频 MP3 URL（仅 MUSIC） |
| `data.data[N].image_url` | 封面图 URL（仅 MUSIC） |
| `data.data[N].media_urls` | 多格式音频（m4a + mp3）（仅 MUSIC） |
| `data.data[N].duration` | 时长（秒）（仅 MUSIC） |
| `data.data[N].metadata.key` | 调性，如 `B_major`（仅 MUSIC） |
| `data.data[N].metadata.avg_bpm` | 平均 BPM（仅 MUSIC） |
| `data.data[N].status` | `complete` 表示完成 |

### 轮询策略

- 间隔：10 秒
- 最大等待：300 秒（5 分钟）
- 停止条件：`data.status == "SUCCESS"` 或 `data.data.status == "complete`"

---

## 与 mmx-cli 的对比

| 维度 | mmx-cli | 兔子 Suno API |
|------|---------|---------------|
| 安装 | 需安装 CLI | 无需，纯 API |
| 模型 | MiniMax Music | Suno（多个版本） |
| 调用方式 | `mmx music` 终端命令 | HTTP POST |
| 异步 | 本地等待 | 提交任务 + 轮询 |
| 歌词生成 | 不支持 | 支持（`/suno/submit/lyrics`） |
| 适用场景 | 已有 mmx 环境 | 无 mmx 或需要 Suno 特有风格 |

---

## 在 ai-music-producer 中的集成点

ai-music-producer Phase 4（生成 & 选优）应增加判断：

```
if which mmx:
    使用 mmx music 路径（现有逻辑）
else:
    使用 tuzi-api Suno 路径：
    1. 组装 prompt/tags/mv/title
    2. 调用 tuzi("POST", "/suno/submit/music", ...)
    3. 获取 task_id
    4. 调用 wait_for_suno(task_id)
    5. 下载音频到 ~/Desktop/📂 音乐/[歌名]/
    6. 返回结果给 Phase 5
```
