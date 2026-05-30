# 调度器任务 A 规则集（创作归档）

> 本文件由任务 A prompt 引用，包含流派池、结构模板、歌词规则、质检标准。
> prompt 只保留骨架逻辑，详细规则全部在此文件中。

---

## 流派多样性池（20种，7天去重）

1. 城市暗潮 Urban Darkwave  2. 氛围电子 Ambient Electronic  3. 后摇 Post-Rock
4. 数学摇滚 Math Rock  5. 迷幻民谣 Psychedelic Folk  6. 新古典 Neo-Classical
7. 合成器波 Synthwave  8. 梦幻流行 Dream Pop  9. 垃圾摇滚 Grunge
10. 爵士嘻哈 Jazz Hip-Hop  11. 世界融合 World Fusion  12. 极简主义 Minimalism
13. 前卫电子 Avant-Garde Electronic  14. 灵魂乐 Neo-Soul  15. 巴萨诺瓦 Bossa Nova
16. 工业电子 Industrial Electronic  17. 氛围说唱 Ambient Rap  18. 后朋克 Post-Punk
19. 实验民谣 Experimental Folk  20. 氛围后摇 Ambient Post-Rock

## 结构多样性（不套同一模板）

- A型（叙事）：V1→V2→PC→C→Inst→V3→PC→C→Bridge→Solo→C→Outro
- B型（递进）：V1→PC→C→V2→PC→C→Bridge→V3→C→C→Outro
- C型（漫游）：Intro→V1→V2→C→Break→V3→V4→C→Bridge→Inst→C→Outro
- D型（简约）：V1→C→V2→C→Bridge→C→Outro+大量间奏

## 歌词创作规则

### MiniMax 歌词 API（第一环）
调用 `POST https://api.minimaxi.com/v1/lyrics_generation`（mode: write_full_song）。
API Key 从 `~/.mmx/config.json` 读取 `api_key` 字段。

参数：`mode: "write_full_song"`, `title`: 歌名, `style_tags`: 从流派池选取, `prompt`: 结构模板（≤2000字）：

```
请创作一首完整的歌词，严格遵循以下结构和行数要求：
[Intro] - 2-3行氛围铺陈
[Verse 1] - 6-8行叙事
[Pre-Chorus] - 2-3行情绪过渡
[Chorus] - 4-6行核心 Hook
[Verse 2] - 6-8行深化
[Pre-Chorus] - 2-3行
[Chorus] - 4-6行（递进变化）
[Instrumental] - 标记纯器乐段落
[Verse 3] - 6-8行新视角
[Chorus] - 4-6行（第三次变化）
[Bridge] - 4-6行转折
[Solo] - 标记纯器乐段落
[Chorus] - 4-6行终版
[Outro] - 3-4行收束
总计纯歌词行数要求：≥60行（不含结构标签行）
每个段落之间留 1 行空行。
歌词风格：用画面和意象说话，禁止直白表达情感。
```

API 报错时回退纯手写（同样遵循结构模板和 60+ 行要求）。

### 诗化审核（第二环）
MiniMax 返回后，作为「词境审核师」重写整首歌词。规则：

**【词境之场】**：场有双力——根力向情感扎根，流力向旋律流淌。不直说只暗示，说出三分留七分。宁可短句不可长句，宁可空白不可填满，宁可跳跃不可平铺。

**【抽象之梯下沉】**：每句歌词在梯子底部——用物件/场景/动作说话。禁止「想念」「孤独」「快乐」「悲伤」「爱」「迷茫」等情感词。

**【诗歌四要素】**：
1. 行顿：每4行必有≤3字短句/省略号/空行（换气口）
2. 酌字：每行≤10字，不用虚词
3. 跳跃：允许意象非线性跳跃
4. 留白：不说透，让听众续写

**【五感选材】**：优先视觉+听觉意象，偶尔通感跳跃，但每个意象只取一个切面，不堆叠。

**【Chorus递进】**：每次副歌改1-2行（提出→加深→升华）。禁止说理句。

### lyric-qa 质检（第三环）
调用 `lyric-qa` skill 四维度检测。画面感<7分或陈词滥调>3处则回炉（最多2轮）。通过后调用 `music-prompt-templates` skill 输出双平台提示词。

### 歌词格式铁律
- 只允许 `[Tag]` + 纯歌词，禁止括号描述词
- 禁止发音黑名单：画框、缝补、依归、干涸、禁止项、避让

---

## 时长铁律（目标 3:00-4:00）
- 纯歌词≥55行，目标60-75行（不含 `[Tag]` 行）
- 实测：25-30行≈1:30❌，55行≈2:30及格，60-70行≈3:00-3:30✅
- 至少2个纯器乐段落（`[Instrumental]`/`[Solo]`）
- **⛔ 完成后必须数行数，N<55立即补充，N<50判定失败**
- **⛔ 每首必须输出**：`✅ 歌词行数检查：纯歌词 N 行（目标 ≥55），预估时长 X:XX`
- **⛔ 绝对禁止<50行**

---

## 作品档案笔记模板

每首歌独立创建 `🎵 [歌名] · 作品档案`，包含：
- 构思灵感来源
- style_tags 及选派理由
- 诗化审核前后对比（MiniMax 原始 → 重写版）
- lyric-qa 报告
- 歌词正文
- 结构理由
- MiniMax / Suno 提示词

每创建笔记后**立即**调用 `remio_syscall(action="add_note_to_collection")` 加入 `mp8hk00v8ibo61feheg`。

---

## 产出校验（任务结束前必须执行）
1. 调用 `search_notes` 搜索今天创建的 `作品档案`（`time_filter` 设置今天，`limit: 5`）
2. 确认今天有 ≥1 个新作品档案
3. 如果 0 个 → 输出 `❌ TASK VALIDATION FAILED: 0 songs created today`（这会让调度器标记该次运行为异常）
4. 报告格式：`创作成功N首/失败M首/补集修复K首`
