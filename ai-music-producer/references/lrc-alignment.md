# LRC 歌词对齐 Phase 7（v4.0 纯本地 ForcedAligner）

> 目标：每首歌的每个版本都生成精确的 LRC 歌词时间轴，用于：
> - 音乐网站 (Music Vault) 同步显示
> - 短视频卡点剪辑
> - 用户在播放器里跟唱

## 1. 架构

```
音频文件 (mp3) + 歌词文件 (txt)
        │
        ├─── PC GPU (Qwen3-ForcedAligner-0.6B, RTX 4070 Ti SUPER) ──→ 主服务
        │                                                              ~2-3s/首
        │
        └─── M2 Mac mini (Qwen3-ForcedAligner-0.6B, MLX/MPS) ────→ fallback
                                                                     ~30s/首
        │
        ▼
   LRC 时间轴（逐行精确对齐）
        │
        ▼
   lrc_data.json 索引
```

**核心原理**：ForcedAligner 不是「听出歌词」，而是「给定音频+已知歌词文本 → 找出每个字在音频中的时间位置」。因为我们已经有原始歌词（AI 生成时就写好了），不需要 ASR 识别，直接对齐即可。

## 2. 工具调用

```bash
# 增量对齐（推荐）
python <music-vault>/lrc_align.py

# 指定歌曲
python <music-vault>/lrc_align.py --songs 发芽 你是一条河

# 全部重跑
python <music-vault>/lrc_align.py --force
```

## 3. 依赖与环境

| 项 | 要求 |
|---|---|
| Python | 3.8+ |
| PC 服务 | WSL2, RTX 4070 Ti SUPER, 端口 7777 |
| M2 服务 | macOS, MLX/MPS, 端口 7778 |
| 网络 | 局域网（192.168.50.x） |

**不依赖任何在线 API**（无 DashScope、无小米 MiMo）。

## 4. 输出格式

### 4.1 索引文件 lrc_data.json

```json
{
  "三十五岁以后__v3": [
    {"time": 12.52, "text": "地铁报站声淹没了耳机线"},
    {"time": 17.04, "text": "《温柔》前奏还在单曲循环"},
    ...
  ]
}
```

### 4.2 与 music-vault 集成

- `vault.py` 启动时读 `data/lrc_data.json`
- 按 `slug__version` 格式匹配
- 嵌入到网站播放器的 LRC 同步显示
- 对齐后自动 rebuild 网站

## 5. 定时任务集成

Task B（后处理）调用顺序：

```bash
# 4a: 更新 songs.json
python <music-vault>/build.py extract

# 4b: ForcedAligner 歌词对齐（自动 rebuild）
python <music-vault>/lrc_align.py
```

## 6. 检查点

```
LRC 完成：[歌名/v1: 行数] | [歌名/v2: 行数] | [歌名/v3: 行数]
引擎: PC GPU ✅ / M2 MLX ✅
索引更新：data/lrc_data.json 共 [N] 个版本
耗时：总 [X] 分钟
确认后进入 Phase 8 BeatPrints 海报。
```
