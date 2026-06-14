# 定时调度指南 Phase 11

> 目标：把"每天做一首歌"从手动操作变成自动流水线。

> **⚠️ 架构变更（2026-06-14）**：原 11 阶段单体流水线已拆分为 **Task A → Task A' → Task B** 三阶段任务，每个阶段由独立 scheduler 触发、独立的 rules 文件约束。详见：
> - [scheduler-task-a-rules.md](./scheduler-task-a-rules.md) — 创作+归档（Phase 1-5, 11）
> - [scheduler-task-a2-rules.md](./scheduler-task-a2-rules.md) — 音频+封面（Phase 4-6）
> - [scheduler-task-b-rules.md](./scheduler-task-b-rules.md) — 海报+LRC+后处理（Phase 7-10）
>
> 本文件保留**总览/调度配置/失败处理/通知**等跨任务通用逻辑，**具体的执行步骤请查阅对应 task rules**。下文 3.1 / 3.2 节的 prompt 模板也对应拆分为三个独立任务。

## 1. 调度方式选择

| 方式 | 适用场景 | 推荐度 |
|------|----------|--------|
| **remio scheduler aapp** | 灵活的任务编排 + 失败重试 + 日志 | ⭐⭐⭐⭐⭐ |
| **macOS launchd** | 系统级后台任务 | ⭐⭐⭐ |
| **cron**（不推荐） | 简单定时 | ⭐⭐ |
| **手动触发** | 单次跑 | ⭐ |

**强烈推荐用 remio scheduler aapp**——它支持：
- 自然语言定义任务（"每天凌晨 2 点做一首歌"）
- 自动注入 nvm / API Key 等环境变量
- 失败重试 + 通知
- 任务日志查询
- 与 remio 知识库联动（结果直接写笔记）

## 2. remio scheduler aapp 配置

### 2.1 创建定时任务

通过 aapp 的 `create` 端点（参考 scheduler skill 文档）：

```python
aapp_call(
    aapp_id="scheduler",
    method="POST",
    path="/tasks",
    params={
        "name": "每天凌晨 2 点自动做一首歌",
        "schedule": "0 2 * * *",  # cron 表达式
        "prompt": """你是 ai-music-producer skill 主管。请执行完整 11 Phase 流程：
1. Phase 1 选题：从你最近的灵感笔记中选一个主题（10 分钟内），
   或随机从场景辞海选 1 个情绪+场景组合
2. Phase 2-5 歌词+生成+精修
3. Phase 7-9 LRC + 海报 + 4 维评分（综合 ≥70 才能归档）
4. Phase 10 网站发布
5. Phase 11 写作品档案 + 加入 🎵 AI 原创歌曲 · 作品集 Collection

完成后输出 [SCHEDULED_DONE] + 歌名 + noteId。""",
        "model": "sonnet",
        "timeout_minutes": 90,
        "notify_on_failure": True,
    }
)
```

### 2.2 任务字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | ✅ | 任务名（用于查询） |
| `schedule` | ✅ | cron 表达式 |
| `prompt` | ✅ | 任务执行指令（建议包含完整流程） |
| `model` | ❌ | LLM 模型（默认 sonnet） |
| `timeout_minutes` | ❌ | 超时（默认 60） |
| `notify_on_failure` | ❌ | 失败时通知（默认 false） |
| `notify_on_success` | ❌ | 成功时通知（默认 false） |
| `working_dir` | ❌ | 工作目录（默认 agent 根） |

### 2.3 常用 schedule 表达式

| 表达式 | 含义 |
|--------|------|
| `0 2 * * *` | 每天凌晨 2 点 |
| `0 */6 * * *` | 每 6 小时 |
| `0 2 * * 1` | 每周一凌晨 2 点 |
| `0 2 1 * *` | 每月 1 号凌晨 2 点 |
| `@daily` | 每天（remio 扩展） |
| `@weekly` | 每周（remio 扩展） |

## 3. 任务 prompt 模板

### 3.1 三阶段拆分版（推荐，2026-06-14 起）

新架构把原 11 阶段拆成 3 个独立 scheduler 任务，**上一阶段产出 pending_*.json，下一阶段从 pending 文件读取输入**。这样：
- 每个任务超时独立（Task A 90min，Task A' 60min，Task B 60min）
- 失败重试粒度更细（封面失败不会拖累归档）
- 配额耗尽/服务不可用时可以只跳过其中一个阶段

#### 3.1.1 Task A：创作+归档（每天凌晨 1 点）

```python
aapp_call(
    aapp_id="scheduler",
    method="POST",
    path="/tasks",
    params={
        "name": "AI 音乐 · 创作归档 Task A",
        "schedule": "0 1 * * *",
        "prompt": """你是 ai-music-producer skill 主管。

请严格按 scheduler-task-a-rules.md 执行 Task A 完整流程：
- 选题 + 五感素材（Phase 1）
- 歌词 + 双平台 prompt（Phase 2-3）
- 精修评分（Phase 5-6）
- 作品档案笔记（Phase 11）
- 更新 pending_audio.json（song_dir 指向 ~/Music/音乐项目/YYYY-MM-DD_歌名/）

最后输出 [SCHEDULED_DONE] 歌名 | noteId | 综合评分。""",
        "model": "sonnet",
        "timeout_minutes": 90,
        "notify_on_failure": True,
    }
)
```

#### 3.1.2 Task A'：音频+封面（每天凌晨 2 点）

```python
aapp_call(
    aapp_id="scheduler",
    method="POST",
    path="/tasks",
    params={
        "name": "AI 音乐 · 音频封面 Task A'",
        "schedule": "0 2 * * *",
        "prompt": """你是 ai-music-producer skill 主管。

请严格按 scheduler-task-a2-rules.md 执行 Task A' 完整流程：
- 读取 pending_audio.json 的 songs[]（如为空则跳过当天）
- 调用 mmx 生成 1-3 个版本
- 生成封面（bizyair → gcli2api → mmx fallback）
- 更新 pending_postprocess.json（指向同一个 song_dir）

最后输出 [SCHEDULED_DONE] 歌名 | 状态。""",
        "model": "sonnet",
        "timeout_minutes": 60,
        "notify_on_failure": True,
    }
)
```

#### 3.1.3 Task B：海报+LRC+发布（每天凌晨 3 点）

```python
aapp_call(
    aapp_id="scheduler",
    method="POST",
    path="/tasks",
    params={
        "name": "AI 音乐 · 后处理 Task B",
        "schedule": "0 3 * * *",
        "prompt": """你是 ai-music-producer skill 主管。

请严格按 scheduler-task-b-rules.md 执行 Task B 完整流程：
- 读取 pending_postprocess.json 的 songs[]（如为空则跳过当天）
- 生成 BeatPrints 海报（2280×3480）
- LRC 对齐（PC WSL2 GPU 优先，M2 MLX fallback）
- 4 维质量评分
- 运行 vault.py build 重新发布

最后输出 [SCHEDULED_DONE] 歌名 | 综合评分。""",
        "model": "sonnet",
        "timeout_minutes": 60,
        "notify_on_failure": True,
    }
)
```

#### 3.1.4 旧版单体 prompt（仅供历史参考，新部署请用 3.1.1-3.1.3）

<details>
<summary>点击展开：原 11 阶段单体 prompt（已废弃）</summary>

```
你是 ai-music-producer skill 主管。请执行完整 11 Phase 流程：
1. Phase 1 选题 + 五感素材
2. Phase 2-3 歌词 + 双平台 prompt
3. Phase 4 音频（music-2.6 mmx）
4. Phase 5-6 精修 + 封面
5. Phase 7 LRC（lrc_align.py）
6. Phase 8 BeatPrints 海报
7. Phase 9 4 维评分
8. Phase 10 网站发布（vault.py build）
9. Phase 11 归档
```

> **为什么不推荐单体**：超时失控、单点失败、配额耗尽拖垮整条线、agent context 撑爆。详见 3.1.1-3.1.3 的拆分版本。
</details>

### 3.2 快速版（仅歌词+生成）

适合：配额紧张时 / 心情不好想偷懒时。三个任务的 prompt 中将质量阈值从 70 调到 65，跳过某些可选 phase：

#### Task A（快速）
- 选题跳过 Phase 1 五感素材表，直接从最近笔记中选主题
- 综合评分阈值 ≥65（默认 70）
- 其余不变

#### Task A'（快速）
- 只生成 v1 一个版本（默认跑 v1/v2/v3 三个）
- 仍需生成封面（封面是网站展示必需）

#### Task B（快速）
- 仍跑完整 LRC + 海报 + 评分
- 评分阈值与 Task A 一致

输出仍按三阶段格式：`[SCHEDULED_DONE] 歌名 | noteId`。

## 4. 任务监控

### 4.1 查看任务列表

```python
aapp_call(
    aapp_id="scheduler",
    method="GET",
    path="/tasks",
    params={"status": "active"}  # 可选：active/paused/all
)
```

### 4.2 查看任务历史

```python
aapp_call(
    aapp_id="scheduler",
    method="GET",
    path="/tasks/<id>/history",
    params={"limit": 30}
)
```

### 4.3 暂停 / 恢复 / 删除

```python
# 暂停
aapp_call(aapp_id="scheduler", method="POST", path="/tasks/<id>/pause", params={})

# 恢复
aapp_call(aapp_id="scheduler", method="POST", path="/tasks/<id>/resume", params={})

# 删除
aapp_call(aapp_id="scheduler", method="DELETE", path="/tasks/<id>", params={})
```

## 5. 失败处理

### 5.1 常见失败原因

| 原因 | 解决方案 |
|------|----------|
| GLM API 限额 | 自动 fallback DeepSeek v4 pro |
| 配额耗尽 | 跳过当天 |
| ForcedAligner 不可用 | 标记"未对齐"，下次手工补 |
| remio 笔记 API 异常 | 重试 3 次后跳过 |
| music-vault 服务端口占用 | 自动检测 `check_serve_running` |

### 5.2 重试策略

prompt 中应明确：

```
失败重试规则：
- API 调用失败：等 30s 重试，最多 3 次
- 配额问题：标记 [QUOTA_EXHAUSTED] 后跳过当天
- 整体超时：超过 90 分钟自动终止
- 网络问题：等 60s 重试 2 次
```

## 6. 通知配置

### 6.1 微信通知（通过 message-gateway aapp）

prompt 末尾追加：

```
完成后通过 message-gateway aapp 发送微信通知：
aapp_call(
    aapp_id="message-gateway",
    method="POST",
    path="/send",
    params={"to": "violin", "text": "🎵 [SCHEDULED_DONE] 歌名"}
)
```

### 6.2 失败通知

`notify_on_failure=True` 触发后，scheduler aapp 会自动调用 message-gateway。

## 7. 与其他定时任务的关系

**推荐架构**：

- **ai-music-producer 三阶段调度**（Task A / A' / B）：新歌创作（每天 1 首）
- **music-vault 批量维护**（每周日）：批量重生成封面 / 海报 / 评分

> **历史说明**：早期的 `v5_regen.py` / `v5_regen_all.py` 已被 `regenerate_covers.py` + `lrc_align.py` + `vault.py build` 取代。如果发现老脚本引用，请删除。

```python
# 周日凌晨 3 点批量重生成（修复型）
aapp_call(
    aapp_id="scheduler",
    method="POST",
    path="/tasks",
    params={
        "name": "music-vault 周末批量维护",
        "schedule": "0 3 * * 0",
        "prompt": """执行以下批处理：
1. python build.py extract  # 重建 songs.json
2. python regenerate_covers.py --all  # 重生成所有封面（可选：--songs 指定）
3. python lrc_align.py --force  # 重新对齐所有 LRC
4. python vault.py build  # 重建网站
5. python vault.py serve --restart  # 重启静态服务器
报告：扫描 N 首歌 / 修复 M 个封面 / 补齐 K 个 LRC"""
    }
)
```

## 8. 检查点

```
调度任务创建：
- 任务名：[...]
- schedule：[cron 表达式]
- 预计首次运行：[YYYY-MM-DD HH:MM]
- 通知：失败时 ✅ / 成功时 ❌
- 工作目录：[agent 根]
```

## 9. 实战经验

从 MEMORY 提取：
- **GLM 限额**：用 GLM Coding Plan base URL `https://open.bigmodel.cn/api/coding/paas/v4/`，不要用标准 API
- **深夜偶发限额**：06:03 GLM 不可用时手动补跑
- **Failback 链**：bizyair → gcli2api → mmx（bizyair 高峰期会 error 1011）
- **更新后重跑**：每次大改 skill 后建议手动跑一次完整流程
