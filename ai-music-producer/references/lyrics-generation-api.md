# MiniMax 歌词生成 API 参考

> 被 SKILL.md Phase 2 引用。使用 lyrics_generation API 时读取此文件。

---

## 重要区分

MiniMax 有**两种歌词生成方式**，效果完全不同：

| 方式 | 触发方式 | 额度类型 | 输出语言 | 质量 |
|------|----------|----------|----------|------|
| **独立歌词 API** | `POST /v1/lyrics_generation` | `lyrics_generation`（100次/日） | 中文 ✅ | 中等，可作草稿 |
| **CLI 内置优化器** | `mmx music generate --lyrics-optimizer` | `music-2.6`（共享音乐生成额度） | 英文 ❌ | 差，套路化 |

**⚠️ CLI 的 `--lyrics-optimizer` 不会调用独立歌词 API！** 它只是让音乐模型自行发挥，几乎必定输出英文歌词。

**正确用法：先调独立 API 出中文草稿 → 手工精修 → 再用 `--lyrics` 传入生成音乐。**

---

## 独立歌词生成 API

### 端点

```
POST https://api.minimaxi.com/v1/lyrics_generation
```

### 认证

```
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

API Key 从 `~/.mmx/config.json` 读取 `api_key` 字段。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | string | ✅ | `write_full_song`（生成完整歌词）或 `edit`（续写/修改） |
| `prompt` | string | 否 | 歌曲主题/风格描述，最长 2000 字符 |
| `lyrics` | string | 否 | 现有歌词，仅 `edit` 模式，最长 3500 字符 |
| `title` | string | 否 | 指定歌曲标题 |

### 响应格式

```json
{
  "song_title": "生成的歌名",
  "style_tags": "Pop, Upbeat, Female Vocals",
  "lyrics": "[Intro]\n...\n[Verse 1]\n...\n[Chorus]\n...",
  "base_resp": {
    "status_code": 0,
    "status_msg": "success"
  }
}
```

### 支持的结构标签

`[Intro]` `[Verse]` `[Pre-Chorus]` `[Chorus]` `[Post-Chorus]` `[Hook]` `[Drop]` `[Bridge]` `[Solo]` `[Build-up]` `[Instrumental]` `[Breakdown]` `[Break]` `[Interlude]` `[Outro]`

### 错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1002 | 限流 |
| 1004 | 鉴权失败 |
| 1008 | 余额不足 |
| 1026 | 敏感内容 |
| 2013 | 参数异常 |
| 2049 | 无效 API Key |

---

## 调用示例（Python）

```python
import json, os, urllib.request

# 读取 API Key
with open(os.path.expanduser("~/.mmx/config.json")) as f:
    api_key = json.load(f)["api_key"]

payload = {
    "mode": "write_full_song",
    "prompt": "Noir Jazz，慵懒讽刺，主题：拒绝进化的代价是永恒的童话",
    "title": "泥泞赞美诗"
}

req = urllib.request.Request(
    "https://api.minimaxi.com/v1/lyrics_generation",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    method="POST"
)

with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    lyrics = result["lyrics"]
    title = result["song_title"]
```

### 续写/修改模式

```python
payload = {
    "mode": "edit",
    "prompt": "继续往更深情的方向发展，Chorus 要更有画面感",
    "lyrics": "[Verse 1]\n海风轻轻吹\n\n[Chorus]\n永远在一起"
}
```

---

## 质量评估与局限性

### ✅ 优势
- 输出**中文歌词**（这是 CLI `--lyrics-optimizer` 做不到的）
- 能抓住 prompt 中的核心意象
- 结构完整（Intro → Verse → Chorus → Bridge → Outro）
- 可用于快速出 Demo / 灵感探索

### ❌ 局限
- 歌词偏「正」，缺少反直觉的妙句
- Chorus 重复过多，结构套路化
- 不会执行「反陈词滥调清单」——「梦想」「飞翔」「力量」等套话频出
- 无法融入用户的个人阅读/日记/思考洞察链

### 与手写歌词对比（实测 3 首）

| 维度 | 手写 | API 草稿 |
|------|------|----------|
| 意象独特性 | 冷咖啡是理想观众、深海祭奠 | 冷咖啡是我的观众（直译感） |
| Hook 锋利度 | 「拒绝进化的代价是永恒的童话」 | 「拒绝进化 拥抱这假象」（偏平） |
| 陈词滥调 | 严格执行反套路 | 「梦想」「飞翔」「力量」满天飞 |
| 效率 | 慢（构思+写+精修） | 快（30秒） |

---

## 推荐工作流

```
1. 独立 API 生成草稿（mode: write_full_song）
2. 用「反陈词滥调清单」逐行扫描替换
3. 用 scene2lyric 补充五感素材
4. 用 lyric-qa 四维检测
5. 确认最终版 → 进入 Phase 3 构建 Prompt
```

**草稿不是成品。** API 生成的歌词必须经过手写精修才能用于正式作品。
