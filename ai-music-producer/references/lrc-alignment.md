# LRC 歌词对齐 Phase 7

> 目标：每首歌的每个版本都生成精确的 LRC 歌词时间轴，用于：
> - 音乐网站 (Music Vault) 同步显示
> - 短视频卡点剪辑
> - 用户在播放器里跟唱

## 1. 核心流程

```
音频文件 (mp3) + 歌词文件 (txt)
        │
        ▼
   FunASR WebSocket API
   (DashScope fun-asr-realtime)
        │
        ▼
   逐字时间戳 + 句子级时间戳
        │
        ▼
   滑动窗口模糊匹配对齐
        │
        ▼
   LRC 文件 + lrc_data.json 索引
```

## 2. 工具调用

### 2.1 单首歌（v1 版本）

```bash
python <SKILL_ROOT>/scripts/lrc_align.py \
  --song "~/Desktop/📂 音乐/六月之后" \
  --version v1
```

输出：
- `~/Desktop/📂 音乐/六月之后/六月之后_v1.lrc`
- `data/lrc_data.json` 索引更新（key: 六月之后__v1）

### 2.2 单首歌所有版本

```bash
python <SKILL_ROOT>/scripts/lrc_align.py \
  --song "~/Desktop/📂 音乐/六月之后" \
  --all-versions
```

### 2.3 批量处理

```bash
python <SKILL_ROOT>/scripts/lrc_align.py \
  --batch \
  --music-dir "~/Desktop/📂 音乐" \
  --data-dir "<SKILL_ROOT>/data"
```

跳过已存在的 `.lrc` 文件（增量模式）。`--force` 重新生成。

### 2.4 强制重新生成

```bash
python <SKILL_ROOT>/scripts/lrc_align.py --song "~/Desktop/📂 音乐/六月之后" --version v1 --force
```

## 3. 依赖与环境

| 项 | 要求 |
|---|---|
| Python | 3.8+ |
| websockets | `pip install websockets` |
| ffmpeg | macOS 自带或 `/opt/homebrew/bin/ffmpeg` |
| DashScope API Key | 环境变量 `DASHSCOPE_API_KEY`（默认内嵌 fallback） |

```bash
export DASHSCOPE_API_KEY="sk-xxx"
```

## 4. 歌词文件优先级

脚本按以下优先级查找歌词文件：

1. `{歌名}_lyrics_clean.txt`（推荐，来自 lyrics-prep.py 清洗后）
2. `{歌名}_lyrics.txt`
3. 任意 `*lyrics*.txt`
4. 任意 `*.txt`

## 5. 输出格式

### 5.1 单歌 LRC 文件

```lrc
[ti:六月之后]
[ar:Violin]
[al:AI 原创歌曲 · 作品集]
[by:FunASR + lrc_align.py (12.3s)]
[00:00.00][Intro]
[00:00.00]
[00:10.20]黑板上 倒计时的墨水
[00:14.50]还没干 就被擦掉重来
...
```

### 5.2 索引文件 lrc_data.json

```json
{
  "六月之后__v1": [
    {"time": 0.0, "text": "[Intro]"},
    {"time": 0.0, "text": ""},
    {"time": 10.2, "text": "黑板上 倒计时的墨水"},
    ...
  ],
  "六月之后__v2": [...],
  ...
}
```

## 6. 对齐算法

### 6.1 字级时间戳

FunASR 返回每句 + 每字的时间戳：
```json
{
  "text": "黑板上 倒计时的墨水",
  "begin_time": 10200,  // ms
  "end_time": 14500,
  "words": [
    {"text": "黑", "begin_time": 10200, "end_time": 10300},
    {"text": "板", "begin_time": 10300, "end_time": 10500},
    ...
  ]
}
```

### 6.2 模糊匹配

1. 展平为 `[(char, time_s), ...]` 时间轴
2. 去除标点符号和空白
3. 对每行歌词，在 ASR 文本中从当前位置起找最长公共子串
4. 找到的位置对应的时间戳即为该行起始时间
5. 找不到则用上一行时间（保证 LRC 完整）

### 6.3 段落标记处理

`[Intro]` `[Verse 1]` `[Chorus]` 等标记：
- 不用模糊匹配
- 直接用当前 ASR 位置的时间戳
- 避免在音乐描述上浪费匹配算力

## 7. 质量验证

### 7.1 自检清单

- [ ] LRC 文件存在（`{歌名}_{版本}.lrc`）
- [ ] LRC 文件第一行是 `[ti:歌名]`
- [ ] 行数 ≥ 歌词原文行数 × 80%
- [ ] 时间戳递增（不允许倒退）
- [ ] 时间戳从 0 开始，第一段在 60s 内

### 7.2 异常处理

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 整首歌无匹配 | 音频与歌词错配 | 重新核对 v1/v2/v3 配对 |
| 段落标记错位 | 段落时间被推后 | 检查歌词文件是否有空行 |
| 末尾歌词无时间 | FunASR 截断 | 调整最后一段的 fallback 逻辑 |
| 段间时间跳变 | 段落匹配错位 | 用 `--force` 重新生成 |

## 8. 与 music-vault 集成

LRC 索引文件可被 music-vault 直接读取：
- `vault.py` 启动时会读 `data/lrc_data.json`
- 按 `slug__version` 格式匹配
- 嵌入到网站播放器的 LRC 同步显示

`lrc_align.py --data-dir` 默认输出到 skill 的 `data/` 目录，**实际应指向 music-vault 的 `data/`** 才能被 vault.py 识别：

```bash
python <SKILL_ROOT>/scripts/lrc_align.py \
  --batch \
  --data-dir "/Users/wanglingwei/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault/data"
```

## 9. 检查点

```
LRC 完成：[歌名/v1: 行数] | [歌名/v2: 行数]
索引更新：data/lrc_data.json 共 [N] 个版本
耗时：总 [X] 分钟
未对齐行：[0/总]
确认后进入 BeatPrints 海报生成。
```
