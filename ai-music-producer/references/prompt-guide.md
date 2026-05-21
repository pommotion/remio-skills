# MiniMax + Suno 双平台 Prompt 写法指南

> 被 SKILL.md Phase 3 引用。执行 Phase 3 时读取此文件。

---

## 一、和弦进行速查

> 数据来源：番茄音乐爆款手册 + 华语流行金曲统计分析

| 进行 | 感觉 | 代表作品 | 适用场景 |
|------|------|----------|----------|
| **4536251** | 华语流行最高频 | 说好幸福呢、修炼爱情、青花瓷 | **默认推荐**，几乎所有流行歌 |
| 大调卡农 (15634145) | 正、稳 | 稻香、枫、说好不哭 | 抒情慢歌、温暖治愈 |
| 小调卡农 (6-4-1-5 等变体) | 怀旧伤感 | 夜曲、错位时空 | 伤感情歌、回忆杀 |
| **6415** | 经典流行 | 晴天、七里香、白月光与朱砂痣 | 年轻热歌、活力流行 |
| 1645 | 民谣风 | 成都、好久不见 | 都市民谣、叙事感 |
| 456 | 日系纯音乐感 | 所念皆星河 | 轻音乐、氛围感 |

### 和弦色彩技巧
- **多用 7 和弦、9 和弦**，少用三和弦 → 增加色彩和层次
- 三和弦太「干净」，加 7th/9th 让听感更丰富
- 在 `--prompt` 中写法：`rich jazz chords, dominant 7th, major 9th`
- Suno 中写法：在 Style of Music 加入 `jazz harmony, extended chords`

### 三连音 = 节奏洗脑利器
- 大面积用：「爱情来的太快就像龙卷风」
- 衔接用：「半城烟沙，随风而下」
- 在 `--prompt` 中加 `triplet feel` 或 `shuffle rhythm`

---

## 二、流派 Prompt 速查表

> 基于 AI 音乐生成场景整理，每个条目含核心特征 + 可直接使用的 Prompt。

### 2.1 主力品类（番茄平台验证）

| 品类 | 核心特征 | Prompt 模板 |
|------|----------|-------------|
| **年轻热歌** | 洗脑旋律 + 年轻音色 + 简单副歌 | `Mandarin Pop, catchy melody, young female vocal, bright, upbeat, 120 BPM, radio-friendly` |
| **旋律说唱** | Verse 半说半唱 + Hook 全旋律 | `Melodic Rap, R&B influenced, half-sung verse, melodic chorus, smooth male vocal, 95 BPM` |
| **电子音乐** | 合成器 + 数字音效 + Drop 抓耳 | `Synth Pop, electronic beats, drops, dynamic, 128 BPM, danceable` |
| **潮流摇滚** | 活力 + 电吉他 + 年轻感 | `Alternative Rock, energetic, electric guitar riffs, youthful vocal, 135 BPM` |
| **国风古风** | 中国乐器 + 古风歌词 | `C-Pop, traditional Chinese instruments, guzheng, erhu, poetic lyrics, 80 BPM, elegant` |
| **经典摇滚** | 厚重 + 经典和弦进行 | `Classic Rock, distorted guitar, powerful drums, raspy vocal, strong chorus, 125 BPM` |

### 2.2 常用流派 Prompt（按字母）

| 流派 | Prompt |
|------|--------|
| 原声/不插电 | `Acoustic guitar, soft piano, intimate vocals, warm tone, stripped-down` |
| 氛围 | `Ethereal pads, slow evolving, no drums, atmospheric, meditative, cinematic` |
| 另类摇滚 | `Distorted guitar, raw vocals, 90s vibe, experimental, garage rock` |
| 蓝调 | `Delta blues, electric guitar, harmonica, soulful vocals, 12-bar blues, gritty` |
| 波萨诺瓦 | `Bossa nova, acoustic guitar, soft percussion, laid-back, warm Brazilian vibe` |
| 舒缓嘻哈 | `Chillhop, lo-fi beats, jazz piano samples, mellow, coffee shop vibe, 85 BPM` |
| 舒缓波 | `Chillwave, 80s synths, reverb, dreamy, nostalgic, hazy summer` |
| 电影配乐 | `Cinematic orchestral, epic, emotional, string section, brass, building dynamics` |
| 经典流行 | `Classic pop, 80s production, catchy melody, synth bass, strong chorus` |
| 香颂 | `French chanson, romantic, accordion, soft vocals, Parisian cafe vibe` |
| 乡村 | `Country pop, acoustic guitar, fiddle, storytelling, warm male vocal, 110 BPM` |
| 迪斯科 | `1970s disco, funky bass, string section, falsetto vocals, 120 BPM` |
| 后摇 | `Post-rock, building dynamics, delay guitar, instrumental, atmospheric, epic climax` |
| 灵魂乐 | `Neo-soul, warm Rhodes piano, groovy bass, smooth vocal, R&B influenced` |
| 合成波 | `Synthwave, retro 80s, neon, driving bass, arpeggiator, night drive` |

### 2.3 高级组合示例（多维度组合法）

```
咖啡馆背景：Lo-fi Chillhop + jazz piano + vinyl crackle + soft rain, 90 BPM
史诗预告片：Cinematic Orchestral + Choir + Epic percussion + dramatic strings, 140 BPM
80年代迪斯科：1970s Disco + funky bass + string section + falsetto vocals, 120 BPM
公路旅行：Classic Rock + Americana + harmonica + upbeat rhythm, 125 BPM
深夜电台：R&B + slow jam + warm electric piano + smooth male vocal, 80 BPM
雨天生闷：Dream Pop + reverb-heavy guitar + ethereal female vocal + lo-fi drums, 95 BPM
```

---

## 三、MiniMax Music 2.6 命令格式

```bash
mmx music generate \
  --prompt "[风格描述 + 编曲指令 + 和弦提示 + Intro 音乐描述]" \
  --lyrics-file [歌名]_lyrics.txt \
  --vocals "[人声描述 + clear consonant enunciation on every syllable]" \
  --genre "[流派]" \
  --mood "[情绪]" \
  --instruments "[乐器列表]" \
  --bpm [BPM] \
  --key "[调式]" \
  --use-case "[用途]" \
  --structure "Intro-Verse1-Verse2-PreChorus-Chorus-Verse3-PreChorus-Chorus-Bridge-Chorus-Outro" \
  --avoid "[要避免的元素]" \
  --model music-2.6 \
  --out [歌名].mp3
```

### 参数详解

| 参数 | 说明 | 示例 |
|------|------|------|
| `--prompt` | 风格描述 + 编曲指令 + 和弦提示。**音乐描述写在这里** | `"Indie Folk, warm acoustic guitar, gentle piano fills, 4536251 chord progression, rich 7th chords"` |
| `--lyrics-file` | 歌词文件路径。只有纯歌词 + `[Tag]` | `[歌名]_lyrics.txt` |
| `--vocals` | 人声描述。**必须加咬字指令** | `"warm male vocal, clear consonant enunciation on every syllable"` |
| `--genre` | 流派 | `"Indie Folk"` |
| `--mood` | 情绪 | `"nostalgic, hopeful"` |
| `--instruments` | 乐器列表 | `"acoustic guitar, piano, cello, light percussion"` |
| `--bpm` | 速度 | `85` |
| `--key` | 调式 | `"C major"` |
| `--structure` | 歌曲结构。**必须加**，防止 AI 跳过段落 | `"Intro-Verse1-Chorus-Verse2-Chorus-Bridge-Chorus-Outro"` |
| `--avoid` | 要避免的元素 | `"electronic drums, auto-tune, screaming"` |

### 人声音色偏好（番茄平台验证）

| 性别 | 偏好 | Prompt 写法 |
|------|------|-------------|
| 女 | 夹子音、细嗓、空气感、情绪充沛 | `breathy female vocal, airhead tone, emotional, delicate` |
| 男 | 短视频向、温暖、年轻 | `warm male vocal, youthful tone, smooth, clear diction` |

### 演唱技巧注入

```
--vocals 中可加：
- breathy, airhead tone → 气声
- slight cry in voice → 哭腔
- ghost note, soft delivery → 弱处理
- spoken word intro → 半说半唱（旋律说唱品类）
```

### 混音参数建议

```
--prompt 中可加：
- warm reverb, delay on vocals → 混响+延迟
- +3dB loudness for streaming → 面向流媒体响度提升
- lo-fi vinyl crackle → 复古质感
```

### 歌词文件写法

```txt
[Intro]

[Verse 1]
凌晨三点的便利店
冷柜嗡嗡地响
我买了一罐过期的咖啡
坐在窗边看街灯

[Pre-Chorus]
有些话来不及说
就像有些路来不及走

[Chorus]
你有没有这样的时刻
站在人群里却觉得空

[Bridge]
如果时间能倒流

[Chorus]
你有没有这样的时刻
站在人群里却觉得空

[Outro]
那就这样吧
```

**⚠️ 关键规则**：
- 歌词文件中只有 `[Tag]` 标签和纯歌词文本
- **绝不能放括号注释**：`(温暖的Rhodes电钢琴)` 会被 mmx 当歌词唱出来
- 音乐描述只写在 `--prompt` 参数中

---

## 四、Suno Prompt 格式

```
Style of Music: [风格，BPM，核心乐器，人声类型，情绪，和弦提示]

Lyrics:

[Intro]

[Verse 1]
[歌词...]

[Pre-Chorus]
[歌词...]

[Chorus]
[歌词...]

[Bridge]
[歌词...]

[Chorus]
[歌词...]

[Outro]
[歌词...]
```

### Style of Music 写法示例

| 流派 | Style of Music 示例 |
|------|---------------------|
| 都市民谣 | `Indie Folk, acoustic guitar, warm male vocal, 80 BPM, nostalgic, gentle piano, 1645 progression` |
| Dream Pop | `Dream Pop, reverb-heavy guitar, ethereal female vocal, 95 BPM, melancholic, atmospheric, dreamy` |
| Pop Jazz | `Pop Jazz, brushed drums, warm piano, smooth male vocal, 110 BPM, late-night cafe vibe` |
| 华语流行 | `Mandarin Pop, piano-driven, clear female vocal, 90 BPM, emotional ballad, 4536251` |
| 电子氛围 | `Ambient Electronic, synth pads, minimal beats, 70 BPM, cinematic, dreamy` |

### Suno 高级技巧

**歌曲结构标签**：
```
[Intro] [Verse] [Chorus] [Bridge] [Rap] [Outro] [End]
[Pre-Chorus] [Interlude] [Instrumental] [Break]
```

**二重奏（和声）技巧**：
句尾括号重复指定词，Suno 自动生成和声：
```
岁月的痕迹 随风悄然飘散 （悄然飘散）
梦想的方向 淡淡的微笑 （淡淡的微笑）
```

**漏字解决**：
用同音同声字替换 Suno 不认识的字。

**超过 2 分钟**：
- 用 `Continue From This Song` 续杯
- 每次续最长 1 分钟
- 最后用 `Get Whole Song` 无缝拼接（额外 5 积分）

---

## 五、双平台对照

| 项 | MiniMax | Suno |
|----|---------|------|
| 音乐描述放哪 | `--prompt` | `Style of Music` 行 |
| 歌词放哪 | `--lyrics-file` 文件 | `Lyrics:` 下方 |
| 结构标签 | 同 Suno | `[Intro]` `[Verse 1]` 等 |
| 人声控制 | `--vocals`（加咬字指令） | 写在 Style of Music 中 |
| 流派 | `--genre` | Style of Music 第一部分 |
| BPM | `--bpm` 数字 | Style of Music 中写数字 |
| 乐器 | `--instruments` | Style of Music 中列出 |
| 和弦 | `--prompt` 中写 | Style of Music 中写 |
| 和声 | `--prompt` 中描述 | 歌词中用 `()重复词` |

---

## 六、参数说明表（输出给用户确认时使用）

| 参数 | 值 | 理由 |
|------|-----|------|
| --prompt | [值] | [理由] |
| --vocals | [值] | [理由] |
| --bpm | [值] | [理由] |
| --key | [值] | [理由] |
| --instruments | [值] | [理由] |
| --structure | [值] | [理由] |
| --avoid | [值] | [理由] |
| 和弦进行 | [值] | [理由] |
| 洗脑结构 | [值] | [理由] |
