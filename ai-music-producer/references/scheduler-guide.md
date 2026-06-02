# 定时调度指南 Phase 11

> 目标：把"每天做一首歌"从手动操作变成自动流水线。

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

### 3.1 完整流程版（推荐）

```
你是 ai-music-producer skill 主管。请执行完整 11 Phase 流程：

1. Phase 1 选题（10 分钟内）
   - 优先从你最近的灵感笔记（@[灵感]）中选 1 个主题
   - 或从场景辞海（@[场景辞海]）随机选 1 个"情绪+场景"组合
   - 选题要写 1.1 灵感来源 + 1.2 五感素材表

2. Phase 2-3 歌词 + Prompt 构建
   - 用 2026 ai-music-producer skill 完整工作流
   - 反陈词滥调（用 lyric-qa skill D1 检测）
   - 输出双平台 prompt（MiniMax + Suno）

3. Phase 4 音频生成
   - 用 music-2.6（mmx CLI）
   - 3 个版本（中速/热血/抒情）
   - 检查配额（>20% 才会全跑）

4. Phase 5-6 精修 + 视觉化
   - 3 版 ASR 转写检查
   - 50 分精修评分
   - 封面生成（bizyair-skill → gcli2api fallback）

5. Phase 7 LRC 同步
   - python scripts/lrc_align.py --song ... --all-versions

6. Phase 8 BeatPrints 海报
   - python scripts/beatprint_gen.py --cover ... --title ... --genre ... --emotion ... --duration ...

7. Phase 9 4 维质量评分
   - python scripts/lyric_qa.py --lyrics ... --note-id <新建noteId>
   - 综合分 ≥70 才能进入下一步

8. Phase 10 网站发布
   - python scripts/site_publish.py --build

9. Phase 11 归档
   - 创建作品档案笔记（7 大段模板）
   - 加入 🎵 AI 原创歌曲 · 作品集 collection
   - 更新 collection 索引

输出格式：
[SCHEDULED_DONE] 歌名 | noteId | 综合评分 | 状态
```

### 3.2 快速版（仅歌词+生成）

```
你是 ai-music-producer skill 主管。执行"快速做一首歌"模式：

1. 跳过 Phase 1 + Checkpoint
2. Phase 2 歌词（用默认主题：从你最近的笔记中选）
3. Phase 3 Prompt
4. Phase 4 音频（1 个版本即可，不跑 3 版）
5. Phase 7-9 LRC + 海报 + 评分（综合 ≥65 即可）
6. Phase 11 归档

[SCHEDULED_DONE] 歌名 | noteId
```

适合：配额紧张时 / 心情不好想偷懒时。

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
| FunASR 失败 | 标记"未对齐"，下次手工补 |
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

music-vault 已有自己的批量处理脚本（`v5_regen.py` 等），但它们是手动触发的。**推荐**：

- **ai-music-producer 调度**：新歌创作（每天 1 首）
- **music-vault 调度**：批量重生成封面 / 海报 / 评分（每周日）

```python
# 周日凌晨 3 点批量重生成
aapp_call(
    aapp_id="scheduler",
    method="POST",
    path="/tasks",
    params={
        "name": "music-vault 周末批量维护",
        "schedule": "0 3 * * 0",
        "prompt": "运行 v5_regen_all.py + beatprint_gen.py --from-vault + site_publish.py --build"
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
