# 番茄专项 Task T-A 规则集（创作归档）

> 本文件由番茄专项 Task T-A prompt 引用。
> 与现有 Task A 完全独立，面向番茄音乐平台，追求播放量最大化。

---

## 核心定位

番茄音乐的流量密码 = **接地气 × 情绪浓 × 旋律洗脑 × 下沉受众买单**。

与现有流水线（诗化意象）完全不同：番茄歌词要**直白口语、短句重复、情绪外放**。

---

## 五大曲风矩阵（固定轮换，每天各 1 首）

| # | 代号 | 风格描述 | BPM | 和弦公式 | 歌词方向 | 音色 |
|:---:|:---|:---|:---|:---|:---|:---|
| ① | `dance` | 广场舞 / DJ 舞曲 / 车载慢摇 | 120-130 | 6415 循环 | 极简重复，可纯音乐 | 女声 / 无人声 |
| ② | `viral_pop` | 抖音热歌 / 口水歌 / 欢快洗脑 | 100-120 | 4536251 | 短句三字重复，A+A+A+B | 夹子音女声 |
| ③ | `sad` | 失恋 / 孤独 / 情感共鸣 | 70-90 | 1645 | 直白情绪（想你/放不下/算了吧） | 气声女声 / 哭腔 |
| ④ | `guofeng` | 民族风 / 古诗词改编 / 中国风 | 80-100 | 大调卡农 | 古典意象（月/楼/风/雪/琴） | 戏腔 / 民族女声 |
| ⑤ | `hometown` | 乡愁 / 励志 / 朴实口语 | 90-110 | 卡农变体 | 地名+亲情（妈妈/老屋/村口） | 温暖男声 / 民谣女声 |

**每天必须产出 5 首，每种曲风各 1 首，不得遗漏。**

---

## ⛔ 歌名去重（强制执行，Phase 1 选题前必走）

### 去重策略：全历史 + 7 天双重

| 窗口 | 数据源 | 维度 |
|------|--------|------|
| **全历史** | 读 `tomato-vault/data/songs.json` 全量歌名 | 歌名 |
| **7 天** | `search_notes(query="🎵 番茄档案", time_filter={start:"<今天-7天>"})` | 歌名 |

### 执行步骤（必须按序）

1. 读取 `tomato-vault/data/songs.json`（不存在则跳过，视为首日）
2. 提取所有 `title` 字段，构建全量已用歌名集合
3. `search_notes(query="🎵 番茄档案", time_filter={start:"<今天-7天>"})` → 收 7 天内已用（二次确认）
4. 全量集合 ∪ 7 天集合 = **黑名单**
5. 为 5 种曲风各选 1 个歌名，全部与黑名单对比
6. **⛔ 重复的歌名必须重新命名**

### 任务头部输出（每次必须）

```
🍅 番茄专项去重报告：
全历史已用歌名 N 首；7天内已用 M 首
本次选择：
  ① 广场舞: [歌名]
  ② 洗脑情歌: [歌名]
  ③ 伤感情绪: [歌名]
  ④ 国风古风: [歌名]
  ⑤ 家乡励志: [歌名]
歌名去重：✅ 无重复 / ⚠️ X首重复已替换
```

---

## 歌词创作规则（番茄版，与现有流水线完全相反）

### ⛔ 路径选择（强制路径 B）

固定使用路径 B（全手写 DeepSeek），禁止 MiniMax 歌词 API。

### 各曲风歌词模板

#### ① 广场舞（dance）
```
[Intro] - 2-3行（节奏感强的短句，如"动起来 跟我跳"）
[Verse 1] - 6-8行（场景铺陈：广场/灯光/人群）
[Chorus] - 6-8行（核心洗脑Hook，三字/四字重复为主）
[Verse 2] - 6-8行
[Pre-Chorus] - 2-3行
[Chorus] - 6-8行（重复不变）
[Instrumental] - 标记纯器乐段落（DJ间奏）
[Verse 3] - 4-6行（新增：舞蹈动作描写/互动喊麦）
[Chorus] - 6-8行（Double Chorus：副歌唱两遍）
[Chorus] - 6-8行
[Outro] - 2-3行（渐弱）
总计：≥55行（⚠️ 广场舞节奏快，每行只值~2.8秒，必须多写才能撑够时长）
```

#### ② 洗脑情歌（viral_pop）
```
[Intro] - 2-3行
[Verse 1] - 6-8行（日常生活场景）
[Pre-Chorus] - 2-3行
[Chorus] - 6-8行（A+A+A+B排比结构！三句相同/相似+一句转折）
[Verse 2] - 6-8行
[Pre-Chorus] - 2-3行
[Chorus] - 6-8行
[Bridge] - 4-6行
[Chorus] - 6-8行（Double Chorus）
[Chorus] - 6-8行
[Outro] - 2-3行
总计：≥55行
```

#### ③ 伤感情绪（sad）
```
[Intro] - 2-3行（雨/夜/空房间意象）
[Verse 1] - 6-8行（直白叙事：分手场景/独处时刻）
[Pre-Chorus] - 2-3行
[Chorus] - 4-6行（核心情绪爆发：想你/放不下/算了吧）
[Verse 2] - 6-8行（回忆对比）
[Pre-Chorus] - 2-3行
[Chorus] - 4-6行
[Bridge] - 4-6行（转折：接受/放下）
[Chorus] - 4-6行
[Outro] - 3-4行
总计：≥50行
```

#### ④ 国风古风（guofeng）
```
[Intro] - 2-3行（古典意象铺陈）
[Verse 1] - 6-8行（月/楼/风/雪/琴意象）
[Pre-Chorus] - 2-3行
[Chorus] - 4-6行（化用古诗或仿古句式）
[Verse 2] - 6-8行
[Pre-Chorus] - 2-3行
[Chorus] - 4-6行
[Instrumental] - 标记器乐段落（古筝/笛子）
[Bridge] - 4-6行
[Chorus] - 4-6行
[Outro] - 3-4行
总计：≥50行
```

#### ⑤ 家乡励志（hometown）
```
[Intro] - 2-3行（村口/老屋/炊烟）
[Verse 1] - 6-8行（童年记忆/妈妈/老屋）
[Pre-Chorus] - 2-3行
[Chorus] - 6-8行（乡愁核心：回家/想念/奋斗）
[Verse 2] - 6-8行（离开家乡/城市打拼）
[Pre-Chorus] - 2-3行
[Chorus] - 6-8行
[Bridge] - 4-6行（励志转折：一定要出人头地）
[Chorus] - 6-8行
[Outro] - 3-4行
总计：≥55行
```

### 番茄歌词审核规则（反转版）

**⛔ 禁止使用现有流水线的诗化审核规则。番茄歌词走以下规则：**

1. **直白表达**：✅ 鼓励「想你」「放不下」「我爱你」「心好痛」等直白情感词
2. **口语化**：用大白话说事，像跟朋友聊天一样
3. **短句重复**：副歌核心用三字/四字重复（滴答滴 / 会不会 / 想你啦）
4. **排比洗脑**：副歌 A+A+A+B 结构——三句相似 + 一句转折
5. **线性叙事**：好懂，不需要跳跃，时间线清晰
6. **不追求留白**：该说透就说透，番茄用户要的是即时共鸣
7. **国风例外**：国风古风可以用古典意象和仿古句式

### 歌词格式铁律
- 只允许 `[Tag]` + 纯歌词，禁止括号描述词
- 禁止发音黑名单：画框、缝补、依归、干涸、禁止项、避让

---

## 时长要求（番茄用户完播率优先）

> ⚠️ **核心规律**：mmx music-2.6 的时长 ≈ 歌词行数 × ~3秒/行。歌词行数是时长的首要决定因素，mmx_prompt 里的 "full length 3-4 minutes" 只是建议，实际以歌词量为准。
>
> 实测数据（2026-06-14 首跑）：蹦跶蹦 40行→1:54、要不要 48行→2:08、想家了 62行→2:53、还爱你 62行→3:32、长相思 61行→4:03

| 曲风 | 目标时长 | 歌词行数下限 | 秒/行参考 |
|:---|:---|:---|:---|
| ① 广场舞 | 2:45-3:15 | **≥55行** | ~2.8 |
| ② 洗脑情歌 | 2:45-3:15 | **≥55行** | ~2.7 |
| ③ 伤感情绪 | 3:00-3:30 | ≥50行 | ~3.4 |
| ④ 国风古风 | 3:00-3:30 | ≥50行 | ~4.0 |
| ⑤ 家乡励志 | 3:00-3:30 | **≥55行** | ~2.8 |

**⛔ 完成后每首必须输出**：`✅ 歌词行数检查：[曲风] 纯歌词 N 行，预估时长 X:XX`（行数不达标必须补写，禁止跳过）

---

## 双平台提示词生成

通过质检后，调用 `music-prompt-templates` skill 输出：
- **mmx 提示词**（music-2.6 模型）：包含风格描述、BPM、和弦、音色
- **Suno 提示词**：同样参数，适配 Suno 格式

### mmx 提示词风格模板

#### ① 广场舞
```
style: high energy Chinese square dance, DJ remix, four-on-the-floor beat, 128 BPM, female vocal chops, catchy synth melody, bass drop, full length song 3-4 minutes, extended instrumental breaks, long intro and outro
```
#### ② 洗脑情歌
```
style: catchy Chinese pop, viral earworm, upbeat tempo 115 BPM, sweet female vocal (夹子音), 4536251 chord progression, repetitive hook, full length song 3-4 minutes, extended chorus repeats, bridge section
```
#### ③ 伤感情绪
```
style: emotional Chinese ballad, melancholy, slow tempo 80 BPM, breathy female vocal, piano and strings, crying tone, 1645 progression, full length song 3-4 minutes, long instrumental intro, extended outro
```
#### ④ 国风古风
```
style: Chinese traditional style pop, guzheng and dizi, operatic female vocal (戏腔), poetic lyrics, 90 BPM, canon chord progression, elegant and atmospheric, full length song 3-4 minutes, extended guzheng solo, long intro
```
#### ⑤ 家乡励志
```
style: Chinese folk pop, warm male vocal, acoustic guitar, 100 BPM, nostalgic and uplifting, countryside imagery, canon variation progression, full length song 3-4 minutes, extended instrumental sections, bridge
```

---

## 作品档案笔记模板

每首歌独立创建 `🎵 [歌名] · 番茄档案`，包含：
- 曲风代号 + 风格描述
- 和弦公式 + BPM
- 歌词正文
- mmx / Suno 提示词
- 创作思路（为什么选这个主题）

每创建笔记后**立即**加入 Collection「🍅 番茄专项」（首次运行时创建）。

---

## 数据交接（Phase 结束时必须执行）

### 写入 `tomato_audio.json`

```json
{
  "date": "2026-06-14",
  "songs": [
    {
      "title": "歌名",
      "genre_code": "dance",
      "genre_label": "广场舞",
      "song_dir": "/Users/wanglingwei/Music/番茄音乐/2026-06-14_歌名",
      "slug": "歌名_2026-06-14",
      "date": "2026-06-14",
      "chord": "6415",
      "bpm": 128,
      "lyrics": "[完整歌词]",
      "mmx_prompt": "mmx风格描述...",
      "suno_prompt": "suno风格描述..."
    }
    // ... 共 5 首
  ]
}
```

⚠️ **目录格式**：`~/Music/番茄音乐/YYYY-MM-DD_歌名/`（日期前缀防止覆盖）
⚠️ **slug 格式**：`歌名_YYYY-MM-DD`（唯一标识）

写入路径：`tomato-vault/data/tomato_audio.json`

---

## 产出校验（任务结束前必须执行）

1. 确认 5 首歌词全部完成
2. 确认 `tomato_audio.json` 已写入且包含 5 首歌
3. 确认 5 个 `🎵 [歌名] · 番茄档案` 笔记已创建
4. 如果 < 5 首 → 输出 `❌ TASK VALIDATION FAILED: 仅创作 N/5 首`
5. 报告格式：`🍅 番茄专项创作完成：5/5（广场舞✅ 洗脑情歌✅ 伤感✅ 国风✅ 家乡✅）`
