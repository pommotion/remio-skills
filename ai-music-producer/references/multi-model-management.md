# 多模型版本管理指南

> 目标：用 mmx / suno / listenhub 多平台做"对照实验"，自动选最优版本。

## 1. 平台矩阵

| 平台 | 调用方式 | 强项 | 弱项 |
|------|----------|------|------|
| **MiniMax Music 2.6**（mmx） | `mmx music` CLI | 中文友好、咬字准、动态好 | 配额限制（每 5h 滚动） |
| **Suno v4.5**（tuzi-api） | `tuzi-api` HTTP | 配器丰富、风格多样 | 中文吞字、长句不准 |
| **ListenHub** | `listenhub` skill | 多语言、情感细腻 | 速度慢、配额少 |

## 2. 文件命名规范

每个平台单独版本，互不覆盖：

```
~/Desktop/📂 音乐/六月之后/
  ├── 六月之后_lyrics.txt            # 歌词（共享）
  ├── 六月之后_lyrics_clean.txt      # 清洗后歌词
  │
  ├── 六月之后_mmx_v1.mp3            # mmx 中速
  ├── 六月之后_mmx_v2.mp3            # mmx 热血
  ├── 六月之后_mmx_v3.mp3            # mmx 抒情
  │
  ├── 六月之后_suno_v1.mp3           # Suno 风格 A
  ├── 六月之后_suno_v2.mp3           # Suno 风格 B
  │
  ├── 六月之后_listenhub_v1.mp3      # ListenHub 抒情
  │
  ├── cover_六月之后.png              # 共享封面
  ├── 六月之后_v1.lrc                # LRC（来自 v1，平台无关）
  ├── 六月之后_v2.lrc
  ├── 六月之后_v3.lrc
  │
  └── 六月之后_poster.png            # 海报
```

## 3. 平台 prompt 差异

### 3.1 mmx（MiniMax Music 2.6）

直接用 `--prompt` 参数：

```bash
mmx music generate \
  --prompt "Taiwanese Pop Rock, Mayday-style band sound, anthemic high school graduation ballad, 105 BPM, C major with 4536251 chord progression, rich 7th and 9th chords, intro soft clean electric guitar arpeggio with piano..." \
  --bpm 105 \
  --key "C major" \
  --genre "Pop Rock" \
  --mood "nostalgic, hopeful" \
  --lyrics-file 六月之后_lyrics_clean.txt \
  --output 六月之后_mmx_v1.mp3
```

参数：
- `--bpm`：默认 100
- `--key`：默认 "C major"
- `--mood`：多标签逗号分隔
- `--instruments`：乐器列表

### 3.2 Suno（tuzi-api）

Suno 用结构化 prompt：

```bash
tuzi-api call suno_generation '{
  "custom_mode": true,
  "prompt": "Style of Music: Taiwanese Pop Rock, Mayday-inspired, anthemic, emotional, 105 BPM, C major, electric guitar, acoustic guitar, piano, bass, drums, string section, warm male vocal, group vocals in chorus",
  "lyrics": "[Intro]\n\n[Verse 1]\n...",
  "title": "六月之后",
  "instrumental": false,
  "model": "V4_5",
  "wait_audio": true
}'
```

关键点：
- `prompt` = `Style of Music:` 开头
- `lyrics` = 含结构标记
- `model` = `V4_5`（最新）

### 3.3 ListenHub

```bash
listenhub call music-generate '{
  "lyrics": "...",
  "style": "Pop Rock, Mayday style, 105 BPM",
  "voice": "male-cn-1"
}'
```

## 4. 多平台对比实验

### 4.1 同步生成 + 对比评分

```python
from concurrent.futures import ThreadPoolExecutor

def gen_mmx(prompt, output): ...
def gen_suno(prompt, lyrics, output): ...
def gen_listenhub(prompt, output): ...

with ThreadPoolExecutor(max_workers=3) as ex:
    f1 = ex.submit(gen_mmx, mmx_prompt, "v1_mmx.mp3")
    f2 = ex.submit(gen_suno, suno_prompt, lyrics, "v1_suno.mp3")
    f3 = ex.submit(gen_listenhub, lh_prompt, "v1_listenhub.mp3")
    
    f1.result(); f2.result(); f3.result()

# 用 PIL/numpy 做音色对比（频谱、响度、动态范围）
# 用 ASR 做歌词保真度对比
```

### 4.2 评分维度

| 维度 | 测量方式 | 权重 |
|------|----------|------|
| **歌词保真度** | ASR 转写后字符匹配率 | 40% |
| **音色美感** | 频谱平滑度 + 谐波比 | 25% |
| **动态范围** | dB 极差 | 15% |
| **风格匹配度** | 与参考曲目（Mayday）相似度 | 20% |

### 4.3 自动选最优

```python
def pick_best(versions: list) -> dict:
    scored = []
    for v in versions:
        score = (
            v['lyrics_accuracy'] * 0.4 +
            v['tone_quality'] * 0.25 +
            v['dynamics'] * 0.15 +
            v['style_match'] * 0.20
        )
        scored.append({**v, 'score': score})
    return max(scored, key=lambda x: x['score'])
```

## 5. 与作品档案集成

作品档案的"## 四、当前选定版本"段落要扩展：

```markdown
## 四、当前选定版本

**多平台对比结果**：

| 平台 | 版本 | 时长 | 歌词保真度 | 音色 | 风格匹配 | 总分 |
|------|------|------|------------|------|----------|------|
| mmx | v1 | 3:12 | 95% | 88 | 92 | 91.0 |
| mmx | v2 | 3:18 | 70% | 90 | 88 | 80.4 |
| Suno | v1 | 3:25 | 85% | 85 | 80 | 83.0 |
| ListenHub | v1 | 3:08 | 90% | 92 | 75 | 86.0 |

**AI 推荐**：mmx v1（总分 91.0，结构最完整、最像 Mayday）
```

## 6. 配额管理

### 6.1 mmx 配额

```bash
mmx quota
# 输出：剩余 4% / 重置时间 4h23m
```

低于 20% 时**不要生成新歌**。

### 6.2 配额跟踪表

`~/Desktop/📂 音乐/_meta/quota.json`：

```json
{
  "mmx": {
    "limit": 1000,
    "used": 96,
    "last_check": "2026-06-02T23:30:00+08:00"
  },
  "suno": {
    "limit": 500,
    "used": 12
  }
}
```

### 6.3 自动 Fallback

```python
def generate_with_fallback(prompt, lyrics, output):
    providers = [
        ('mmx', gen_mmx),
        ('suno', gen_suno),
        ('listenhub', gen_listenhub),
    ]
    for name, fn in providers:
        quota = check_quota(name)
        if quota > 0.2:
            try:
                return fn(prompt, lyrics, output)
            except QuotaExhausted:
                continue
    raise AllProvidersExhausted()
```

## 7. 检查点

```
多平台对比完成：
  mmx: 3 版本（v1=91.0, v2=80.4, v3=78.2）
  suno: 2 版本（v1=83.0, v2=80.5）
  listenhub: 1 版本（v1=86.0）
AI 推荐版本：mmx v1（91.0）
待用户确认后进入 Phase 10 网站发布。
```

## 8. 实战经验

- **mmx v1 通常最优**：中文咬字 + 动态反差 + 4536251 进行
- **Suno 副歌更"燃"**：但长句吞字
- **ListenHub 适合抒情 Ballad**：88 BPM G major
- **不混用 prompt**：每个平台有自己偏好的 prompt 风格
- **配额 0% 时** 用之前生成的历史版本（不重复生成）
