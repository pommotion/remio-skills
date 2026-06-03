# LRC 歌词对齐 Phase 7（v3.1 双引擎）

> 目标：每首歌的每个版本都生成精确的 LRC 歌词时间轴，用于：
> - 音乐网站 (Music Vault) 同步显示
> - 短视频卡点剪辑
> - 用户在播放器里跟唱

## 1. 双引擎对齐架构

```
音频文件 (mp3) + 歌词文件 (txt)
        │
        ├─── FunASR WebSocket API ───→ 逐字时间戳（锚点）
        │                              ~12s/首, ~70% 文本准确率
        │
        ├─── Qwen3-ASR-Flash API ──→ 高准确率文本（纠错参考）
        │                              ~4s/首, ~90% 文本准确率
        │
        ▼
   DTW 编辑距离对齐
   (原歌词文本 + FunASR 时间戳 + Qwen3 辅助校验)
        │
        ▼
   LRC 数据 + lrc_data.json 索引
   (使用原始歌词文本，不是 ASR 文本)
```

### 为什么需要双引擎？

| 问题 | FunASR 单引擎 | 双引擎 |
|------|-------------|--------|
| 文本错误 | "地铁爆炸声"（应为"报站声"）| 原歌词替换 → "地铁报站声" ✅ |
| 时间戳缺失 | 某些字无时间戳 | Qwen3 辅助定位 |
| 漏词/多词 | 直接影响 LRC | DTW 对齐过滤 |

## 2. 工具调用

### 2.1 主脚本（双引擎）

```bash
# 增量对齐（推荐）
python <music-vault>/funasr_word_align.py --rebuild

# 指定歌曲
python <music-vault>/funasr_word_align.py --songs 发芽 你是一条河

# 全部重跑
python <music-vault>/funasr_word_align.py --force --rebuild

# 跳过 Qwen3 纠错（纯 FunASR）
python <music-vault>/funasr_word_align.py --no-qwen
```

### 2.2 备用脚本（Whisper based）

```bash
# 基于 Whisper fine.json 的对齐（不需要网络）
python <music-vault>/align_lyrics.py --rebuild
```

### 2.3 Skill 脚本（手动单首/批量）

```bash
# 单首歌
python <SKILL_ROOT>/scripts/lrc_align.py \
  --song "~/Desktop/📂 音乐/六月之后" \
  --version v1

# 批量
python <SKILL_ROOT>/scripts/lrc_align.py --batch \
  --music-dir "~/Desktop/📂 音乐" \
  --data-dir "<music-vault>/data"
```

## 3. 依赖与环境

| 项 | 要求 |
|---|---|
| Python | 3.8+（推荐 3.14 homebrew）|
| websockets | `pip install websockets` |
| ffmpeg | `/opt/homebrew/bin/ffmpeg` |
| DashScope API Key | 环境变量 `DASHSCOPE_API_KEY`（默认内嵌 fallback）|
| Qwen3-ASR-Flash | 共用同一 DashScope API Key，无需额外配置 |

## 4. DTW 对齐算法详解

### 4.1 三路数据

| 数据源 | 角色 | 用途 |
|--------|------|------|
| FunASR 逐字时间戳 | **锚点** | 提供每个字的时间位置 |
| Qwen3-ASR 文本 | **参考** | 辅助校验 FunASR 锚点（当 FunASR 匹配分数低时）|
| 原始歌词文本 | **最终文本** | 直接写入 LRC，不用 ASR 文本 |

### 4.2 匹配流程

1. FunASR → 展平为 `[(char, time_s), ...]` 时间轴
2. 去除标点符号和空白
3. 对每行歌词，取前 8 个字作为搜索锚点
4. 在 ASR 时间轴当前位置起，搜索 120 字窗口内的最佳匹配
5. 如果 FunASR 匹配分数 < 0.5，用 Qwen3 文本辅助定位
6. 匹配成功 → 取对应时间戳 + 原歌词文本写入 LRC
7. 匹配失败 → 用上一行时间 + 0.5s 作为 fallback

### 4.3 段落标记处理

`[Intro]` `[Verse 1]` `[Chorus]` 等标记：
- 不用模糊匹配
- 直接用当前 ASR 位置的时间戳
- 避免在音乐描述上浪费匹配算力

## 5. 输出格式

### 5.1 索引文件 lrc_data.json

```json
{
  "三十五岁以后__v3": [
    {"time": 12.52, "text": "地铁报站声淹没了耳机线"},
    {"time": 17.04, "text": "《温柔》前奏还在单曲循环"},
    ...
  ]
}
```

### 5.2 与 music-vault 集成

- `vault.py` 启动时读 `data/lrc_data.json`
- 按 `slug__version` 格式匹配
- 嵌入到网站播放器的 LRC 同步显示
- 对齐后自动 rebuild 网站

## 6. 质量验证

### 6.1 自检清单

- [ ] LRC 行数 ≥ 歌词原文 × 80%
- [ ] 时间戳递增（不允许倒退）
- [ ] 第一段在 60s 内
- [ ] fallback 行占比 < 15%

### 6.2 异常处理

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 整首歌无匹配 | 音频与歌词错配 | 重新核对 v1/v2/v3 配对 |
| 段落标记错位 | 段落时间被推后 | 检查歌词文件是否有空行 |
| 末尾歌词无时间 | FunASR 截断 | 调整最后一段的 fallback 逻辑 |
| Qwen3 API 超时 | 网络问题 | 自动 fallback 到纯 FunASR |
| FunASR 只返回部分 | WebSocket 超时 | 重试（定时任务环境不受 sandbox 限制）|

## 7. 定时任务集成

Task B（后处理）调用顺序：

```bash
# 4a: 更新 songs.json
python <music-vault>/build.py extract

# 4b: 双引擎歌词对齐（自动 rebuild）
python <music-vault>/funasr_word_align.py --rebuild
```

## 8. 检查点

```
LRC 完成：[歌名/v1: 行数] | [歌名/v2: 行数] | [歌名/v3: 行数]
双引擎: FunASR ✅ + Qwen3-ASR ✅
索引更新：data/lrc_data.json 共 [N] 个版本
耗时：总 [X] 分钟
fallback 率: [X]%
确认后进入 Phase 8 BeatPrints 海报。
```
