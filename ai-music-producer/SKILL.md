---
name: ai-music-producer
description: "AI 音乐全流程制作——从「我有个想法」到「成品歌 + 上架 + 网站发布」的一站式工作流。11 Phase 覆盖选题→歌词→Prompt→生成→精修→MV→LRC→海报→评分→发布→归档/调度。"
description_zh: "AI 音乐全流程制作——从灵感到成品歌 + 网站的一站式工作流"
description_en: "End-to-end AI music production: 11 phases from idea to finished song + LRC + poster + website publish + archive"
version: 3.0.0
allowed-tools: read, write, search_notes, rag, create_note, update_note, web_search, web_fetch, bash, run_python, aapp_call
---

# AI Music Producer — AI 音乐全流程制作 v3.0

从「我有个想法」到「成品歌 + 同步 LRC + BeatPrints 海报 + 4 维评分 + 网站发布 + 作品档案 + 定时调度」。

## 适用场景

- "帮我做一首歌" / "我想做一首关于 XX 的歌"
- 用户有主题/情感但不知道怎么开始
- 批量生成多首歌曲 / 精修已有歌曲
- "ai-music-producer" / "全流程做歌" / "11 Phase"

## 核心原则：全程留痕

**每首歌必须保留完整的创作过程。** 用户复盘时应能完整还原"为什么这样写、为什么选这个风格、改了什么、为什么改"。

## 11 Phase 总览

| Phase | 名称 | 产出 | 强制？ |
|-------|------|------|--------|
| **1** | 选题定位 | 情感/风格/主题/参考 | ⭐ 推荐 |
| **2** | 歌词创作 | 完整歌词 + 反陈词滥调 | ✅ |
| **3** | Prompt 构建 | MiniMax + Suno 双平台 | ✅ |
| **4** | 生成 & 选优 | mp3（多版本） | ✅ |
| **5** | 精修评估 & 后期 | 50 分精修诊断 | ⭐ 推荐 |
| **6** | 可选 MV 制作 | 视频配套 | 可选 |
| **7** | **LRC 歌词同步** | `.lrc` + `lrc_data.json` | ✅ |
| **8** | **BeatPrints 海报** | `歌名_poster.png`（2280×3480） | ✅ |
| **9** | **4 维质量评分** | 综合分 + 写回笔记 | ✅ |
| **10** | **网站发布** | `site/index.html` + 在线 | ✅ |
| **11** | **作品档案 + 调度** | 笔记 + collection + scheduler | ✅ |

## 生成工具

### 音乐生成

| 工具 | 方式 | 适用场景 |
|------|------|----------|
| **MiniMax Music 2.6**（`mmx music`）| 终端直接生成 mp3 | 已安装 mmx-cli（推荐） |
| **Suno (tuzi-api)** | API 自动调用 | 无 mmx 或用户指定 Suno |
| **ListenHub** | `listenhub` skill | 抒情 Ballad 备选 |

详见 [multi-model-management.md](./references/multi-model-management.md)。

### 封面生成

| 优先级 | 工具 | 方式 | 说明 |
|--------|------|------|------|
| ⭐ **默认** | **bizyair-skill**（GPT Image 2 via ModelZoo o2-t2i）| `cover_optimize.py` 自动 A/B + fallback | 始终异步，自带轮询；自动选最优；中文标题丝网印刷风格 |
| 第 2 | gcli2api（gemini-3.1-flash-image）| 同一脚本自动 fallback | bizyair 失败时自动切换 |
| 第 3 | mmx image | `mmx image generate` | 最后兜底 |
| 可选 | Lovart GPT Image 2 | `lovart-api` Skill | 用户指定时 |

详见 [cover-optimization.md](./references/cover-optimization.md)。

> ⚠️ **bozo-aigc 已废弃**：同步模式 + 无重试控制 → 超时重试导致重复提交（2026-06-02 2200 2800 积分根因）。`cover_optimize.py` 已统一用 bizyair-skill modelzoo-run（始终异步）。

---

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

### 2.1 路径 A：API 草稿 + 精修（默认）

1. 调用 `POST /v1/lyrics_generation`（`mode: write_full_song`），传入主题、风格、标题
2. **如果 API 报错（1002 限流 / 1008 余额不足 / 网络失败）** → 自动跳转到路径 B
3. 拿到草稿后执行**强制精修流程**：
   - 用「反陈词滥调清单」逐行扫描，替换「梦想」「飞翔」「力量」等套话
   - 调用 `scene2lyric` 补充五感素材（API 草稿通常缺具象场景）
   - 检查 Hook 锋利度——API 倾向直白表达，需要加入反直觉的妙句

### 2.2 路径 B：全手写（API 不可用时的回退）

调用 `scene2lyric`：检索场景 → 提取五感 → 替换抽象词 → 组装结构化歌词

### 2.4 质量检测

**调用 `scripts/lyric_qa.py` 4 维检测**（D1 陈词滥调 / D2 画面感 / D3 Hook 强度 / D4 韵律一致性）。详见 [quality-scoring.md](./references/quality-scoring.md)。

### 2.5 迭代优化

综合评分 < 80 时按优先级修复最低维度，最多迭代 3 轮。

### 2.6 洗脑度自检

5 项中至少通过 3 项才能进入 Phase 3。

### Checkpoint 2

```
歌词完成，lyric-qa 综合评分：[X/100] [等级]
4 维：D1=[X] D2=[X] D3=[X] D4=[X]
洗脑度自检：[X/5] 通过
歌词正文：[完整歌词]
确认后进入 Prompt 构建。
```

---

## Phase 3: Prompt 构建（双平台）

**⛔ 核心原则：始终同时输出 MiniMax 和 Suno 两个版本的提示词。缺一不可。**

### 执行步骤

1. 调用 `music-prompt-templates` 根据风格匹配模板
2. **多维度组合法**：流派 + 情绪 + 年代 + 配器 + 场景（至少组合 3 维）
3. **选择和弦进行**
4. 记录风格决策日志
5. 按双平台格式组装完整提示词
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
| mmx 可达 **且** 用户未指定 Suno | A: mmx | MiniMax Music 2.6 |
| mmx 不可达 **或** 用户指定「Suno / suno」 | B: tuzi-api | Suno (chirp-v4) |

### 路径 A：mmx 终端生成

1. 读取 [mmx-known-issues.md](./references/mmx-known-issues.md)
2. 创建歌曲目录 + 写歌词文件
3. **强制歌词预处理**：运行 `lyrics-prep.py` 清洗歌词文件
4. 执行 mmx（通过 `bash -lc 'mmx music generate ...'`），输出到 `~/Desktop/📂 音乐/[歌名]/`
5. 每次消耗 1 次 music-2.6 配额（100 次/日），建议生成 3 版本

### 路径 B：Suno 自动生成（via tuzi-api）

调用 `tuzi-api` Skill 的 Suno 模块。

### 多平台对比实验

详见 [multi-model-management.md](./references/multi-model-management.md)。自动跑 3 平台 + 自动选最优。

### 自动精修循环

生成后自动执行六维诊断（含洗脑度）。达标线 42/60（A级）。
- **≥ 42** → 停止，提交用户审核
- **< 42** → 自动精修循环（最多 3 轮）

**核心原则：先保亮点，再修问题。每次最多修 2-3 个问题。**

### 自查触发器（Phase 4 生成前）

```
□ 歌词文件已写入
□ lyrics-prep.py 已运行，验证通过（0 括号、0 描述词）
□ 输出路径已确认（~/Desktop/📂 音乐/[歌名]/）
□ 路径选择已确认（mmx 或 tuzi-api Suno）
□ mmx 路径：配额充足
```

---

## Phase 5: 精修评估 & 后期

读取 [refinement-guide.md](./references/refinement-guide.md) 获取五维诊断表、人声三问、后期处理方案。

Phase 5 分为：
- **5A 精修评估**：五维打分 + 视频适配 + 人声三问
- **5B 后期处理**：mmx Cover / 重新生成 / RVC 修音 / 母带处理
- **5C 变现判断**：评估 8 种变现方式适配度

---

## Phase 6: 可选 — MV 制作

如果用户用途涉及视频：
1. BGM：Phase 4-5 完成的音乐
2. 分镜板：bizyair-skill GPT Image 2 生成
3. 视频：Seedance 2.0 逐镜生成
4. 剪辑：合并 BGM + 视频

详见 [seedance-ad-studio skill]。

---

## Phase 7: LRC 歌词同步 ✅ 强制

**目的**：为每个版本生成精确 LRC 时间轴，用于网站同步显示 + 短视频卡点 + 用户跟唱。

### 工具

```bash
# 单首歌（v1 版本）
python <SKILL_ROOT>/scripts/lrc_align.py \
  --song "~/Desktop/📂 音乐/六月之后" \
  --version v1

# 全部版本
python <SKILL_ROOT>/scripts/lrc_align.py \
  --song "~/Desktop/📂 音乐/六月之后" \
  --all-versions

# 批量（增量）
python <SKILL_ROOT>/scripts/lrc_align.py --batch \
  --music-dir "~/Desktop/📂 音乐" \
  --data-dir "<music-vault>/data"

# 强制重新生成
python <SKILL_ROOT>/scripts/lrc_align.py \
  --song "~/Desktop/📂 音乐/六月之后" \
  --version v1 --force
```

### 工作流

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

### 依赖

- `pip install websockets`
- 环境变量 `DASHSCOPE_API_KEY`（默认内嵌 fallback）
- ffmpeg（macOS 自带）

### 输出

- `~/Desktop/📂 音乐/六月之后/六月之后_v1.lrc`（标准 LRC 格式）
- `data/lrc_data.json`（增量更新，key = `歌名__v1`）

### 质量验证

- [ ] LRC 文件存在
- [ ] 行数 ≥ 歌词原文 × 80%
- [ ] 时间戳递增
- [ ] 第一段在 60s 内

### 与 music-vault 集成

lrc_data.json 可被 vault.py 直接读取并嵌入网站播放器。

### Checkpoint 7

```
LRC 完成：[歌名/v1: 行数] | [歌名/v2: 行数] | [歌名/v3: 行数]
索引更新：data/lrc_data.json 共 [N] 个版本
耗时：总 [X] 分钟
确认后进入 Phase 8 BeatPrints 海报。
```

详见 [lrc-alignment.md](./references/lrc-alignment.md)。

---

## Phase 8: BeatPrints 海报 ✅ 强制

**目的**：从封面生成 9:16 竖版海报（2280×3480），用于短视频封面、社交媒体推广、音乐网站展示。

### 工具

```bash
# 单首歌
python <SKILL_ROOT>/scripts/beatprint_gen.py \
  --cover "~/Desktop/📂 音乐/六月之后/cover_六月之后.png" \
  --title "六月之后" \
  --genre "Pop Rock" \
  --emotion "倔强" \
  --duration 192

# 批量
python <SKILL_ROOT>/scripts/beatprint_gen.py \
  --from-vault "<music-vault 路径>" \
  --music-dir "~/Desktop/📂 音乐"

# 强制重新生成
python <SKILL_ROOT>/scripts/beatprint_gen.py --from-vault <path> --force
```

### 设计规范

- **顶部**（0-280px）：纯色留白
- **封面**（280-2300px）：1920×1920 居中 + 10px 白边 + 圆角
- **渐变**（2880-3480px）：黑色 200α→0α
- **标题**（2960-3120px）：120pt 加粗 + 阴影
- **信息**（3120-3180px）：48pt 常规

### 输出

`{歌名}_poster.png`（与 cover 同目录，2280×3480，约 800-1500KB）

### 与 music-vault 集成

海报路径会写入 songs.json，vault 网站自动展示。

### Checkpoint 8

```
BeatPrints 完成：[歌名] → 2280×3480, [KB]
批量模式：生成 N 张，跳过 M 张
确认后进入 Phase 9 4 维质量评分。
```

详见 [beatprint.md](./references/beatprint.md)。

---

## Phase 9: 4 维质量评分 ✅ 强制

**目的**：用 lyric_qa.py 自动跑 D1-D4 四维检测，输出综合评分，写入作品档案的「## 三、质量检测」段落。

### 工具

```bash
# 单首歌
python <SKILL_ROOT>/scripts/lyric_qa.py \
  --lyrics "~/Desktop/📂 音乐/六月之后/六月之后_lyrics.txt"

# 写回作品档案
python <SKILL_ROOT>/scripts/lyric_qa.py \
  --lyrics "~/Desktop/📂 音乐/六月之后/六月之后_lyrics.txt" \
  --note-id mpwo2judryqgjit4ghn

# 批量
python <SKILL_ROOT>/scripts/lyric_qa.py --batch --music-dir "~/Desktop/📂 音乐"
```

### 4 维度

| 维度 | 权重 | 检测什么 |
|------|------|----------|
| **D1. 陈词滥调扫描** | 25% | 关键词清单（7 类） |
| **D2. 画面感评分** | 35% | 画面行占比 + 五感覆盖 |
| **D3. Hook 强度** | 25% | 长度 + 重复 + 记忆点 + 开头 |
| **D4. 韵律一致性** | 15% | 主韵脚 + 节奏均匀度 |

### 质量门径

| 综合分 | 处理 |
|--------|------|
| ≥ 85 | 🟢 优秀——可直接发布 |
| 70-84 | 🟡 良好——小修小补 |
| 50-69 | 🟠 需改进——优先修 D1/D2 |
| < 50 | 🔴 重写——重做歌词 |

### 写回流程

1. 跑 4 维检测
2. 读 remio 笔记
3. 定位插入点（优先级："## 三、质量检测" > "## 三、版本历史" > "## 二、 之后"）
4. 拼接 + update_note 写回

### Checkpoint 9

```
质量检测完成：[歌名] 综合 [X]/100 [等级]
  D1: [X] | D2: [X] | D3: [X] | D4: [X]
笔记已写回：[noteId]
确认后进入 Phase 10 网站发布。
```

详见 [quality-scoring.md](./references/quality-scoring.md)。

---

## Phase 10: 网站发布 ✅ 强制

**目的**：调用 music-vault 重建 site/index.html，把新歌推到在线网站。

### 工具

```bash
# 完整发布（扫描 + 重建 + 启动服务）
python <SKILL_ROOT>/scripts/site_publish.py --build

# 只扫描新歌
python <SKILL_ROOT>/scripts/site_publish.py --scan-only

# 只重建网站
python <SKILL_ROOT>/scripts/site_publish.py --rebuild

# 自定义 vault 路径
python <SKILL_ROOT>/scripts/site_publish.py --vault-dir /custom/path
```

### 流程

```
1. 扫描 ~/Desktop/📂 音乐/ → data/songs.json
2. 提取封面、歌词、封面色调
3. 重建 site/index.html（杂志风深色主题）
4. （可选）启动 HTTP 服务（端口 8892）
5. songs.json 字段更新（cover/poster/lrc/qualityReport）
```

### 数据同步

site_publish.py 会自动同步：
- `songs.json` 的 `cover` / `poster` / `lyrics_file` 字段
- `lrc_data.json` 的 LRC 同步数据
- `archives.json` 的 qualityReport 提取

### 访问方式

- 在线：http://localhost:8892/
- 文件：`music-vault/site/index.html`

### Checkpoint 10

```
网站发布完成：
  扫描：✅ N 首歌
  构建：✅ site/index.html ([X] KB)
  服务：http://localhost:8892/（运行中）
songs.json 已更新。
确认后进入 Phase 11 作品档案 + 调度。
```

---

## Phase 11: 作品档案 + 调度 ✅ 强制

### 11.1 作品资产上架

**⛔ 心态校准：不是「上传作业」，是「作品资产上架」。**

#### 核心红线
- 版权来源记录每首必存
- 歌词-音频对照必做
- AI 生成声明如实填写
- 封面无版权风险

#### 执行步骤
1. 读取 [publishing-guide.md](./references/publishing-guide.md)
2. 按 7.1-7.12 逐步执行（版权记录 → 音频质检 → 歌词对照 → 信息填写 → 简介标签 → AI 声明 → 封面 → 资料包输出）
3. 执行 7.10 上传前总检清单

### 11.2 归档

#### 11.2.0 归档前强制 Checklist

| # | 必需内容 | 如果缺失 |
|---|---------|----------|
| 1 | **情感锚点** | 从核心洞察中提炼 |
| 2 | **场景五感素材表**（≥ 2 行）| 回溯歌词中具体场景补写 |
| 3 | **歌词反陈词滥调清单** | 列出替换了哪些抽象词 |
| 4 | **Hook 设计思路** | 从副歌提炼核心句并说明机制 |
| 5 | **MiniMax Prompt + Suno Prompt** | 缺任何一条都不允许归档 |
| 6 | **音乐描述设定** | 检查歌词块 `(...)` 残留 |
| 7 | **歌词块纯净**（零括号）| 正则扫描不得有匹配 |
| **8** | **LRC 同步完成** | Phase 7 检查点 |
| **9** | **BeatPrints 海报完成** | Phase 8 检查点 |
| **10** | **4 维质量评分**（综合 ≥ 70）| Phase 9 检查点 |
| **11** | **网站发布完成** | Phase 10 检查点 |

#### 11.2.1 创建归档笔记

1. 读取 [archive-template.md](./references/archive-template.md)
2. `create_note` 创建：`🎵 [歌名] · 作品档案`
3. `add_note_to_collection` 加入 🎵 AI 原创歌曲 · 作品集
4. 更新 collection 索引笔记的歌曲总表（追加新行）

#### 11.2.2 新增版本时

1. `read_note` 读取全文
2. 在版本历史末尾追加新版本段落
3. 更新选定版本 + 复盘表
4. **全量写入**（先读后拼，绝不覆盖）

### 11.3 定时调度（可选）

把"每天做一首歌"变成自动流水线。

```python
aapp_call(
    aapp_id="scheduler",
    method="POST",
    path="/tasks",
    params={
        "name": "每天凌晨 2 点自动做一首歌",
        "schedule": "0 2 * * *",
        "prompt": """你是 ai-music-producer skill 主管。请执行完整 11 Phase 流程：
1. Phase 1 选题：从灵感笔记或场景辞海选 1 个主题
2. Phase 2-3 歌词 + Prompt 构建
3. Phase 4 音频生成（mmx 3 版本）
4. Phase 5 精修 + Phase 6 可选 MV
5. Phase 7-10 LRC + 海报 + 评分 + 网站发布
6. Phase 11.1-11.2 作品档案 + collection 索引更新

综合评分 ≥70 才能归档。""",
        "model": "sonnet",
        "timeout_minutes": 90,
        "notify_on_failure": True,
    }
)
```

详见 [scheduler-guide.md](./references/scheduler-guide.md)。

### Checkpoint 11

```
归档完成：
  笔记已创建：[noteId] 🎵 [歌名] · 作品档案
  collection 已加入：🎵 AI 原创歌曲 · 作品集
  索引已更新：第 [N] 首
  综合评分：[X]/100 [等级]
  调度（可选）：已创建 / 未创建
[SCHEDULED_DONE] 歌名 | noteId
```

---

## 文件管理规范

所有音乐和封面文件统一存放在 `~/Desktop/📂 音乐/[歌名]/`：

```
六月之后/
  ├── 六月之后_lyrics.txt            # 原始歌词
  ├── 六月之后_lyrics_clean.txt      # 清洗后（lyrics-prep.py）
  │
  ├── 六月之后_mmx_v1.mp3            # mmx 中速
  ├── 六月之后_mmx_v2.mp3            # mmx 热血
  ├── 六月之后_mmx_v3.mp3            # mmx 抒情
  │
  ├── 六月之后_v1.lrc                # LRC v1（mmx）
  ├── 六月之后_v2.lrc                # LRC v2
  ├── 六月之后_v3.lrc                # LRC v3
  │
  ├── cover_六月之后.png              # 封面
  ├── 六月之后_poster.png            # BeatPrints 海报（2280×3480）
  │
  ├── cover_prompt.txt               # 封面 prompt
  └── prompts.txt                    # 风格参数决策记录
```

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
| **生成 LRC** | **质量检测区** + **LRC 文件路径** |
| **生成海报** | **封面图区** + **海报文件路径** |
| **网站发布** | **平台链接区**（本地 URL）|
| 上架准备 | 上架资料区（版权+标签+简介+声明） |
| 平台上架 | 平台链接区（更新链接+状态） |

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

1. **Phase 11 归档是强制步骤**——每首歌完成后必须保存笔记 + 加入 collection
2. **始终输出双平台提示词**——MiniMax + Suno，缺一不可
3. **全程留痕**——每个决策都记录在笔记中
4. **歌词块中绝不能放括号注释**——音乐描述写在 `--prompt` 和 `Style of Music` 中
5. **不替用户做审美决策**——版本选择、精修方向由用户决定
6. **所有建议必须可操作**——不说"可以更好"，说"把 L3 的'心痛'换成'手心冰凉'"
7. **mmx 配额意识**——生成前告知用户剩余配额
8. **Phase 7-10 强制执行**——LRC/海报/评分/网站是质量门径，不是可选项
9. **综合评分 ≥ 70 才能归档**——低于则需要重做歌词
10. **失败重试链**：bizyair → gcli2api → mmx（封面）/ mmx → suno → listenhub（音频）

## 快捷模式

用户说"快速做一首歌"时：跳过 Phase 1 + Checkpoint 1+6（MV），用默认参数从 Phase 2 开始。
- **仍然输出双平台提示词**
- **仍然执行 Phase 7-11**（LRC/海报/评分/网站/归档）
- 不强制 lyric-qa 综合 ≥ 80（≥ 65 即可）

批量生成时：每首歌独立走 Phase 2-11，全部完成后更新 collection 索引。

## 故障排除

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| FunASR 转写为空 | websockets 未装 / 配额 | `pip install websockets` / 检查 `DASHSCOPE_API_KEY` |
| 海报字体降级 | macOS 字体找不到 | 调整 `FONT_PATHS` 优先级 |
| lyric-qa pypinyin 警告 | 未装 | `pip install pypinyin`（D4 精度降级）|
| site_publish 卡住 | vault.py 端口 8892 占用 | `lsof -i :8892` 查杀 |
| cover_optimize 反复 fallback | bizyair 限额 | 等 5h 滚动后重跑 |
| emoji 路径 EPERM | bash 沙盒限制 | 写到 `/tmp` 再 `mv` 到目标 |
| LRC 末尾歌词无时间 | FunASR 截断 | 调整最后一段 fallback 逻辑 |

## 参考文档

| 文档 | 内容 |
|------|------|
| [lrc-alignment.md](./references/lrc-alignment.md) | LRC 歌词对齐详细说明 |
| [beatprint.md](./references/beatprint.md) | BeatPrints 海报详细说明 |
| [quality-scoring.md](./references/quality-scoring.md) | 4 维质量评分详细说明 |
| [multi-model-management.md](./references/multi-model-management.md) | 多平台音频管理 |
| [scheduler-guide.md](./references/scheduler-guide.md) | 定时调度详细说明 |
| [publishing-guide.md](./references/publishing-guide.md) | 作品资产上架指南 |
| [hit-song-structures.md](./references/hit-song-structures.md) | 4 种爆款歌词结构 |
| [mmx-known-issues.md](./references/mmx-known-issues.md) | mmx 常见问题 |
| [prompt-guide.md](./references/prompt-guide.md) | 双平台 prompt 速查 |
| [archive-template.md](./references/archive-template.md) | 作品档案模板 |
