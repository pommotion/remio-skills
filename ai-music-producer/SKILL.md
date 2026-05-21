---
name: ai-music-producer
description: "AI 音乐全流程制作：从「我有个想法」到「成品歌+MV」的完整链路。6 Phase 覆盖选题→歌词→Prompt→生成→精修→视觉化。"
description_zh: "AI 音乐全流程制作——从灵感到成品歌的一站式工作流"
description_en: "End-to-end AI music production: from idea to finished song + MV in 6 phases"
version: 2.7.0
allowed-tools: read, write, search_notes, rag, create_note, update_note, web_search, web_fetch, bash, run_python
---

# AI Music Producer — AI 音乐全流程制作

从「我有个想法」到「成品歌 + 可选 MV」的完整制作链路。

## 适用场景

- "帮我做一首歌" / "我想做一首关于 XX 的歌"
- 用户有主题/情感但不知道怎么开始
- 批量生成多首歌曲 / 精修已有歌曲
- 用户说 "ai-music-producer" / "全流程做歌"

## 核心原则：全程留痕

**每首歌必须保留完整的创作过程。** 用户复盘时应能完整还原"为什么这样写、为什么选这个风格、改了什么、为什么改"。

## 生成工具

### 音乐生成

| 工具 | 方式 | 适用场景 |
|------|------|----------|
| **MiniMax Music 2.6**（`mmx music`） | 终端直接生成 mp3 | 已安装 mmx-cli（推荐） |
| **Suno (tuzi-api)** | API 自动调用（`tuzi-api` Skill） | 无 mmx 或用户指定 Suno |

### 封面生成

| 优先级 | 工具 | 方式 | 说明 |
|--------|------|------|------|
| ⭐ **默认** | **gcli2api**（gemini-3.1-flash-image） | `scripts/gcli-cover-gen.py` | 免费，NAS 本地，Antigravity 凭证池 |
| 回退 A | bozo-aigc（BizyAir GPT_IMAGE_2） | `bozo-aigc` Skill 文生图脚本 | gcli2api 不可用时 |
| 回退 B | mmx image | `mmx image generate` | bozo-aigc 也不可用时 |
| 可选 | Lovart GPT Image 2 | `lovart-api` Skill | 用户指定时 |

**判断逻辑**：
1. 优先使用 gcli2api（免费 6000 次额度，基于群晖 NAS Antigravity 凭证池，gemini-3.1-flash-image 模型）
2. gcli2api 连接失败（NAS 离线/凭证耗尽）→ 回退 bozo-aigc（需 `BIZYAIR_API_KEY`）
3. bozo-aigc 也不可用 → 回退 mmx image

**gcli2api 调用方式**：
```bash
python scripts/gcli-cover-gen.py --prompt "极简封面提示词" --output ~/Desktop/📂 音乐/歌名/cover_歌名.png --aspect 1:1
```
- 支持 `--aspect`：1:1（默认）、16:9、9:16、4:3、3:4、21:9
- 支持 `--model` 后缀自动拼接（如 gemini-3.1-flash-image-16x9）
- API 地址 `http://192.168.50.188:7861`，密钥 `violin`
- 每张约 90-120 秒，返回 1MB 左右 JPEG

## 与单点 skill 的关系

本 skill 是**编排层**：

| Phase | 调用 skill | 用途 |
|-------|-----------|------|
| Phase 2 | `scene2lyric` | 生成画面感歌词 |
| Phase 2 | `lyric-qa` | 歌词质量检测 |
| Phase 2 | `lyrics_generation` API | 默认歌词路径，API 草稿 + 精修 |
| Phase 3 | `music-prompt-templates` | 选择流派模板 |
| Phase 6 | `seedance-ad-studio`(aapp) | 可选，生成 MV |

## 关联参考文件

本 skill 采用三层渐进加载。SKILL.md 只包含决策逻辑和流程编排，详细内容按需读取：

| Phase | 参考文件 | 何时读取 |
|-------|---------|----------|
| Phase 2 | [hit-song-structures.md](./references/hit-song-structures.md) | 歌词创作时（爆款结构+洗脑度自检） |
| Phase 2 | [lyrics-generation-api.md](./references/lyrics-generation-api.md) | 使用歌词生成 API 时 |
| Phase 3 | [prompt-guide.md](./references/prompt-guide.md) | 构建 MiniMax/Suno Prompt 时 |
| Phase 4 | [mmx-known-issues.md](./references/mmx-known-issues.md) | mmx 生成前必读 |
| Phase 5 | [refinement-guide.md](./references/refinement-guide.md) | 精修评估/后期处理时 |
| Phase 5C | [monetization-guide.md](./references/monetization-guide.md) | 评估变现方向时 |
| Phase 7 | [publishing-guide.md](./references/publishing-guide.md) | 上架前必读 |
| Phase 8 | [archive-template.md](./references/archive-template.md) | 创建归档笔记时 |
| Phase 8 | [validate-archive.py](./scripts/validate-archive.py) | 归档前验证 |

**⚠️ 每次执行到对应 Phase 时，先读取参考文件再开始工作。**

---

## 工作流总览

```
Phase 1 选题定位 → [Checkpoint 1] →
Phase 2 歌词创作（选择路径 A/B/C → scene2lyric + lyric-qa）→ [Checkpoint 2] →
Phase 3 Prompt 构建（双平台）→ 读取 prompt-guide.md →
Phase 4 生成 & 选优（mmx 优先 / tuzi-api Suno 自动）→ 读取 mmx-known-issues.md →
Phase 5 精修后期 → 读取 refinement-guide.md →
  Phase 5C 变现判断 → 读取 monetization-guide.md
Phase 6 可选：MV 制作 →
Phase 7 上架资料 → 读取 publishing-guide.md →
Phase 8 归档 → 读取 archive-template.md + 运行 validate-archive.py
```

## Collection 自动管理

### 初始化

第一次运行时，搜索是否已有歌曲作品集 collection：
```
search_notes(query="AI 原创歌曲", item_type_filter=["collection"])
```
- 找到 → 使用该 collection ID
- 未找到 → `create_note` 创建 "🎵 AI 原创歌曲 · 作品集"

### 规则

1. **每首完成的歌曲笔记必须加入 collection**
2. **上传后用户发来的平台链接，更新到对应歌曲笔记**
3. **新建歌曲笔记后，更新 collection 索引笔记的歌曲总表**

---

## Phase 1: 选题定位

### 1.1 收集信息

| 信息 | 说明 | 必填 |
|------|------|------|
| **情感** | 核心情绪 | ✅ |
| **风格** | 音乐流派 | 默认：流行 |
| **主题** | 具体故事或画面 | 可选 |
| **用途** | 短视频BGM/广告歌/流媒体发布 | 默认：流媒体 |
| **目标平台** | 抖音/网易云/Spotify | 默认：多平台 |
| **目标工具** | Suno/Udio/豆包 | 默认：Suno |

### 1.2 参考分析（可选）

如果用户有参考歌曲，分析其 BPM/调式/结构/情绪曲线/Hook 特征。没有则基于情感和风格推荐 2-3 首。

### Checkpoint 1

```
选题确认：情感 / 风格 / 主题 / 用途 / 目标工具
参考歌曲：[歌名1] / [歌名2]
确认后进入歌词创作。需要调整吗？
```

---

## Phase 2: 歌词创作

### 2.0 歌词创作路径（优先级机制）

**默认走路径 A（API 草稿 + 精修）。** 仅当 API 返回错误（限额/不可用）时，自动回退到路径 B（全手写）。

| 路径 | 触发条件 | 流程 | 输出质量 |
|------|----------|------|----------|
| **A. API 草稿 + 精修（默认）** | 正常情况 | 歌词 API → `scene2lyric` 精修 → `lyric-qa` | 中高 |
| **B. 全手写（回退）** | API 报错 1002/1008/网络失败 | `scene2lyric` 从零写 → `lyric-qa` | 最高 |

**⚠️ 核心警告：不要使用 `mmx music generate --lyrics-optimizer`！**
- 它不会调用 MiniMax 独立歌词 API（不消耗 `lyrics_generation` 额度）
- 它让音乐模型自行发挥，几乎必定输出**英文**套路歌词
- 如果需要 AI 辅助写词，必须调用**独立的 `POST /v1/lyrics_generation` API**

### 2.0b 爆款歌词结构

**读取 [hit-song-structures.md](./references/hit-song-structures.md)** 获取 4 种洗脑结构（A+A+A+B 排比 / 三字连发 / 签名式 / 长句引子+排比）和题材偏好。

选一个结构填入 Hook，用 `scene2lyric` 反套路意象替换 XX。

**读取 [lyrics-generation-api.md](./references/lyrics-generation-api.md)** 获取完整 API 参数、调用示例和质量评估。

### 2.1 路径 A：API 草稿 + 精修（默认）

1. **读取 [lyrics-generation-api.md](./references/lyrics-generation-api.md)**
2. 调用 `POST /v1/lyrics_generation`（`mode: write_full_song`），传入主题、风格、标题
3. **如果 API 报错（1002 限流 / 1008 余额不足 / 网络失败）** → 自动跳转到路径 B
4. 拿到草稿后执行**强制精修流程**：
   - 用「反陈词滥调清单」逐行扫描，替换「梦想」「飞翔」「力量」等套话
   - 调用 `scene2lyric` 补充五感素材（API 草稿通常缺具象场景）
   - 检查 Hook 锋利度——API 倾向直白表达，需要加入反直觉的妙句
5. 精修后进入 2.4 质量检测

### 2.2 路径 B：全手写（API 不可用时的回退）

调用 `scene2lyric`：检索场景 → 提取五感 → 替换抽象词 → 组装结构化歌词 → 进入 2.4 质量检测

### 2.4 质量检测
调用 `lyric-qa` 四维检测：D1 陈词滥调 / D2 画面感 / D3 Hook 强度 / D4 韵律一致性

### 2.5 迭代优化
综合评分 < 80 时按优先级修复最低维度，最多迭代 3 轮。

### 2.6 洗脑度自检

**读取 [hit-song-structures.md](./references/hit-song-structures.md)** 第二部分「洗脑度自检清单」。

5 项中至少通过 3 项才能进入 Phase 3。不足 3 项 → 回到 2.1 补充。

### Checkpoint 2

```
歌词完成，lyric-qa 评分：[分数]
洗脑度自检：[X/5] 通过
使用的洗脑结构：[A+A+A+B / 三字连发 / 签名式 / 排比]
歌词正文：[完整歌词]
确认后进入 Prompt 构建。
```

---

## Phase 3: Prompt 构建（双平台）

**⛔ 核心原则：始终同时输出 MiniMax 和 Suno 两个版本的提示词。缺一不可。**

### 执行步骤

1. 调用 `music-prompt-templates` 根据风格匹配模板
2. **多维度组合法**：流派 + 情绪 + 年代 + 配器 + 场景（至少组合 3 维）
3. **选择和弦进行**（详见 [prompt-guide.md](./references/prompt-guide.md) 和弦速查表）
4. 记录风格决策日志（流派/BPM/调式/人声/乐器/和弦/避免项）
5. **读取 [prompt-guide.md](./references/prompt-guide.md)**，按双平台格式组装完整提示词
6. 输出参数说明表，用户确认后进入 Phase 4

### 自查触发器（Phase 3 输出前必须通过）

```
□ MiniMax Prompt 已生成（完整命令行）
□ Suno Prompt 已生成（Style of Music + Lyrics）
□ 歌词块中无括号注释（扫描通过）
□ 音乐描述已写入 --prompt / Style of Music（不在歌词中）
```
如未通过 → **禁止输出**，回到 Phase 3 补全。

---

## Phase 4: 生成 & 选优

### 4.0 路径选择

| 条件 | 路径 | 工具 |
|------|------|------|
| mmx 可达（`/opt/homebrew/bin/mmx` 存在）**且** 用户未指定 Suno | A: mmx | MiniMax Music 2.6 |
| mmx 不可达 **或** 用户指定「Suno / suno」 | B: tuzi-api | Suno (chirp-v4) |

> **触发词**：用户说「用 Suno」「suno 生成」「走 Suno」→ 强制走路径 B，无论 mmx 是否存在。

### 路径 A：mmx 终端生成

1. **读取 [mmx-known-issues.md](./references/mmx-known-issues.md)**（生成前必读）
2. 创建歌曲目录 + 写歌词文件
3. **⛔ 强制歌词预处理**：运行 `lyrics-prep.py` 清洗歌词文件（去除括号描述、替换黑名单词、拆分长句）。详见 [mmx-known-issues.md](./references/mmx-known-issues.md) 顶部「强制预处理」章节。
4. 执行 mmx（通过 `bash -lc 'mmx music generate ...'`），输出到 `~/Desktop/📂 音乐/[歌名]/`
5. 每次消耗 1 次 music-2.6 配额（100 次/日），建议生成 3 版本

### 路径 B：Suno 自动生成（via tuzi-api）

调用 `tuzi-api` Skill 的 Suno 模块，全程自动无需用户手动操作。

1. **读取 [tuzi-api SKILL.md](../tuzi-api/SKILL.md)** 的 Suno 模块代码模板
2. 创建歌曲目录
3. 调用 `POST /suno/submit/music`，传入 Phase 3 的 Suno prompt 参数：
   ```python
   {"prompt": "<歌词>", "tags": "<Style of Music>", "mv": "chirp-v4", "title": "<歌名>"}
   ```
4. 获取 task_id，轮询 `GET /suno/fetch/{task_id}` 等待完成
5. Suno 返回 **2 个版本**（数组），下载全部音频到 `~/Desktop/📂 音乐/[歌名]/`
   - 文件命名：`[歌名]_suno_v1_[调性]_[BPM]bpm.mp3`
   - 关键字段：`data.data[N].audio_url` / `.metadata.key` / `.metadata.avg_bpm` / `.duration`
   - **⚠️ MUSIC 任务 `data.data` 是数组（非 dict），与 LYRICS 不同**
6. 输出两版本对比表（调性 / BPM / 时长），提交用户选优

### 自动精修循环（mmx 路径专属）

生成后自动执行六维诊断（含洗脑度）。达标线 42/60（A级）。

- **≥ 42** → 停止，提交用户审核
- **< 42** → 自动精修循环（最多 3 轮）

**核心原则：先保亮点，再修问题。每次最多修 2-3 个问题。**

**读取 [refinement-guide.md](./references/refinement-guide.md)** 获取完整精修流程、诊断表和禁忌清单。

### 自查触发器（Phase 4 生成前）

```
□ 歌词文件已写入
□ ⛔ lyrics-prep.py 已运行，验证通过（0 括号、0 描述词）
□ 输出路径已确认（~/Desktop/📂 音乐/[歌名]/）
□ 路径选择已确认（mmx 或 tuzi-api Suno）
□ mmx 路径：配额充足
□ Suno 路径：TUZI_API_KEY 环境变量已设置
```

---

## Phase 5: 精修评估 & 后期

**读取 [refinement-guide.md](./references/refinement-guide.md)** 获取五维诊断表、人声三问、后期处理方案。

Phase 5 分为：
- **5A 精修评估**：五维打分 + 视频适配 + 人声三问
- **5B 后期处理**：mmx Cover / 重新生成 / RVC 修音 / 母带处理
- **5C 变现判断**：**读取 [monetization-guide.md](./references/monetization-guide.md)**，评估 8 种变现方式适配度

---

## Phase 6: 可选 — MV 制作

如果用户用途涉及视频，建议制作配套 MV：
1. BGM：Phase 4-5 完成的音乐
2. 分镜板：gcli2api gemini-3.1-flash-image 生成（**默认**），不可用时回退 bozo-aigc / Lovart / mmx image
3. 视频：Seedance 2.0 逐镜生成
4. 剪辑：合并 BGM + 视频

---

## Phase 7: 作品资产上架（强制执行）

**⛔ 心态校准：不是「上传作业」，是「作品资产上架」。**

### 核心红线（不需要读 reference 也要记住）
- 版权来源记录每首必存
- 歌词-音频对照必做
- AI 生成声明如实填写
- 封面无版权风险

### 执行步骤
1. **读取 [publishing-guide.md](./references/publishing-guide.md)**
2. 按 7.1-7.12 逐步执行（版权记录 → 音频质检 → 歌词对照 → 信息填写 → 简介标签 → AI 声明 → 封面 → 资料包输出）
3. 执行 7.10 上传前总检清单，确认 11 项全部通过

---

## Phase 8: 归档（强制执行）

### ⛔ 8.0 归档前强制 Checklist（缺一不可）

**在 `create_note` / `update_note` 之前，运行验证脚本并逐项确认：**

```bash
python <SKILL_ROOT>/scripts/validate-archive.py --lyrics "[歌词]" --note "[笔记内容]"
```

7 项 Checklist：

| # | 必需内容 | 如果缺失 |
|---|---------|----------|
| 1 | **情感锚点**（一句话） | 从核心洞察中提炼 |
| 2 | **场景五感素材表**（≥ 2 行） | 回溯歌词中具体场景补写 |
| 3 | **歌词反陈词滥调清单** | 列出替换了哪些抽象词 |
| 4 | **Hook 设计思路** | 从副歌提炼核心句并说明机制 |
| 5 | **MiniMax Prompt + Suno Prompt** | **缺任何一条都不允许归档** |
| 6 | **音乐描述设定**（括号注释已迁移） | 检查歌词块 `(...)` 残留 |
| 7 | **歌词块纯净**（零括号） | 正则扫描不得有匹配 |

输出「✅ Checklist 确认：7/7 通过」或「❌ 缺失：[N]. [项目名]」。

### 8.1 创建归档笔记

1. **读取 [archive-template.md](./references/archive-template.md)** 获取完整笔记模板
2. 用 `create_note` 创建，标题：`🎵 [歌名] · 作品档案`
3. 采用「共用元数据 + 并列版本」结构，新增版本追加，**绝不覆盖旧版本**
4. `add_note_to_collection` 加入 collection
5. 更新 collection 索引笔记的歌曲总表

### 8.2 新增版本时

1. `read_note` 读取全文
2. 在版本历史末尾追加新版本段落
3. 更新选定版本 + 复盘表
4. **全量写入**（`update_note` 是覆盖写入，必须先读后拼）

### 自查触发器（Phase 8 归档前）

```
□ 8.0 Checklist 7/7 通过
□ 笔记标题格式正确：🎵 [歌名] · 作品档案
□ 歌词块纯净（零括号、零舞台指令）
□ 双平台 Prompt 已写入风格参数区域
□ 音乐描述已单独存入 1.6 区域
```
如未通过 → **禁止写入笔记**。

### 自查触发器（update_note 修改已有笔记时）

```
□ 已先 read_note 读取全文
□ 已将新内容与旧内容拼接（非覆盖）
□ 验证关键区域未丢失（版本历史、歌词正文、Prompt）
```

---

## 文件管理规范

所有音乐和封面文件统一存放在 `~/Desktop/📂 音乐/[歌名]/`：
- 音频：`[歌名]_v1.mp3`、`[歌名]_v2.mp3`（按版本并存，不覆盖）
- 封面：`cover_[歌名].png`
- 歌词：`[歌名]_lyrics.txt`
- 命名用歌名，不用 song1/song2 代号

---

## ⛔ 变更同步规则（全程留痕执行）

**任何对歌曲状态的变更，必须立即同步到对应的作品档案笔记。** 这是硬性规则，不是建议。

### 必须同步的变更类型

| 变更操作 | 必须更新档案的哪些区域 |
|----------|--------------------------|
| 生成新版本音频 | 版本历史（追加）+ 选定版本 + 文件大小 |
| 生成/更换封面 | 封面图（路径+分辨率+Prompt+工具+日期）+ 版权来源记录 |
| 修改歌词 | 歌词正文（替换）+ 版本历史（追加修改记录） |
| 修改 Prompt | 风格参数决策（更新）+ 版本历史（追加） |
| 精修诊断 | 版本历史（追加诊断评分）|
| 上架准备 | 上架资料区（版权+标签+简介+声明） |
| 平台上架 | 平台链接区（更新链接+状态） |
| 封面放大/格式转换 | 封面图（更新分辨率+大小） |

### 执行流程（每次变更后）

```
1. read_note 获取当前档案全文
2. 定位变更区域，拼接新内容（绝不覆盖旧内容）
3. update_note 全量写入
4. 如影响 collection 索引，同步更新索引笔记
```

### 自查触发器（每次变更后必须通过）

```
□ read_note 已读取当前全文
□ 新内容已拼接到正确位置（版本历史=追加，其他=替换对应段落）
□ 旧内容未丢失（版本历史、歌词、Prompt 完整）
□ 封面变更已记录：路径 + 分辨率 + Prompt + 工具 + 日期
□ 版权来源记录已更新
```

---

## 质量规则

1. **Phase 8 归档是强制步骤**——每首歌完成后必须保存笔记 + 加入 collection
2. **始终输出双平台提示词**——MiniMax + Suno，缺一不可
3. **全程留痕**——每个决策都记录在笔记中
4. **歌词块中绝不能放括号注释**——音乐描述写在 `--prompt` 和 `Style of Music` 中，存入 1.6 区域
5. **不替用户做审美决策**——版本选择、精修方向由用户决定
6. **所有建议必须可操作**——不说"可以更好"，说"把 L3 的'心痛'换成'手心冰凉'"
7. **mmx 配额意识**——生成前告知用户剩余配额

## 快捷模式

用户说"快速做一首歌"时：跳过 Phase 1 和 Checkpoint，用默认参数直接从 Phase 2 开始。
- **仍然输出双平台提示词**
- **仍然执行 Phase 8 归档**
- 不执行 lyric-qa 检测

批量生成时：每首歌独立走 Phase 2-8，全部完成后更新 collection 索引。
