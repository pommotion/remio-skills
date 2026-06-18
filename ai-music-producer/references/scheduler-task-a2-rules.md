# 调度器任务 A' 规则集（音频+封面）

> 本文件由任务 A' prompt 引用，包含 mmx CLI 用法、封面生成脚本调用方式、Telegram 通知。

---

## mmx CLI 音频生成

- mmx路径：`~/Library/Application Support/remio/Users/SharedData/runtime/npm-global/bin/mmx`
- Node路径：`~/.nvm/versions/node/v22.18.0/bin`（必须加入PATH）
- 命令：`mmx music generate --prompt "风格描述" --lyrics-file 歌词.txt --model music-2.6 --out 输出.mp3`

单首失败不阻塞，超时600s。输出目录：`~/Music/音乐项目/YYYY-MM-DD_歌名/歌名_v1.mp3`

⛔ **路径铁律**：
- 音乐目录完整路径是 `~/Music/音乐项目/`。创建目录时必须用完整路径。
- ⛔ 目录名必须带日期前缀：`YYYY-MM-DD_歌名`（从 pending_audio.json 的 `songs[].song_dir` 读取，不要自行拼接）
- ⛔ 目录内文件仍用纯歌名命名：`歌名_v1.mp3`、`歌名_lyrics.txt`

### ⚡ 并行生成流程（ThreadPoolExecutor max_workers=3）

> **根因修复（2026-06-18）**：串行 3 首 × 3-5min = 9-15min，叠加封面、队列操作，总逼近 30min RPC 上限。
> mmx CLI 每个进程是独立 HTTP API 客户端，API 侧无并发限制 → 3 首同时跑，总耗时 ≈ 最慢的一首 ≈ 3-5min。

```python
import subprocess, os, json
from concurrent.futures import ThreadPoolExecutor, as_completed

MUSIC_DIR = os.path.expanduser("~/Music/音乐项目")
MMX = os.path.expanduser("~/Library/Application Support/remio/Users/SharedData/runtime/npm-global/bin/mmx")
MMX_ENV = os.environ.copy()
MMX_ENV["PATH"] = os.path.expanduser("~/.nvm/versions/node/v22.18.0/bin") + ":" + MMX_ENV["PATH"]

AGENT = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent")
with open(os.path.join(AGENT, "music-vault/data/pending_audio.json")) as f:
    data = json.load(f)

# ---- 准备阶段（串行，快）----
tasks = []
for song in data["songs"]:
    song_dir = os.path.expanduser(song["song_dir"])
    os.makedirs(song_dir, exist_ok=True)
    lyrics_path = os.path.join(song_dir, f"{song['title']}_lyrics.txt")
    with open(lyrics_path, "w") as f:
        f.write(song["lyrics"])
    out_path = os.path.join(song_dir, f"{song['title']}_v1.mp3")
    if os.path.exists(out_path):
        print(f"⏭️ {song['title']} 已存在，跳过")
        continue
    tasks.append(song)

# ---- 单首生成函数（供并行调用）----
def generate_one_song(song):
    song_dir = os.path.expanduser(song["song_dir"])
    lyrics_path = os.path.join(song_dir, f"{song['title']}_lyrics.txt")
    out_path = os.path.join(song_dir, f"{song['title']}_v1.mp3")
    title = song['title']
    
    result = subprocess.run([
        MMX, "music", "generate",
        "--prompt", song["mmx_prompt"],
        "--lyrics-file", lyrics_path,
        "--model", "music-2.6",
        "--out", out_path
    ], capture_output=True, text=True, timeout=600, env=MMX_ENV)
    
    if result.returncode != 0:
        print(f"❌ {title} mmx 失败: {result.stderr[:200]}")
        return (title, False)
    
    ok = os.path.exists(out_path)
    print(f"{'✅' if ok else '❌'} {title} 完成")
    return (title, ok)

# ---- ⚡ 并行生成 ----
print(f"\n🎵 并行生成 {len(tasks)} 首音频 (max_workers=3)...")
with ThreadPoolExecutor(max_workers=3) as pool:
    futures = {pool.submit(generate_one_song, song): song for song in tasks}
    for future in as_completed(futures):
        title, success = future.result()
        status = "✅" if success else "❌"
        print(f"{status} {title} 完成")
```

---

## 封面生成（⛔ 必须调用 regenerate_covers.py）

**⛔ 绝对禁止**自行写 BizyAir API 调用、自行构造封面 prompt、使用 gcli2api/mmx image。

### 封面风格规范（v4 五段式通感场景）
脚本自动读取歌词文件，提取物件/动作写进 prompt。风格：英文电影摄影场景描述，暗色调电影质感，极简构图一个核心视觉主体，歌名中文文字自然融入场景元素。

**禁止**出现 "album cover"、"design" 等设计指令词。

### 唯一正确做法
```python
import subprocess, os
VAULT = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
PYTHON = "/opt/homebrew/bin/python3"
songs = ["歌名1", "歌名2"]  # ← 替换
cmd = [PYTHON, os.path.join(VAULT, "regenerate_covers.py"), "--run", "--songs"] + songs
result = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True, timeout=1800)
print(result.stdout[-2000:])
```

封面规格：bizyair-skill (GPT Image 2 via ModelZoo o2-t2i)，1:1 2048×2048。

⛔ 封面脚本传入的 `--songs` 参数用**纯歌名**（不含日期前缀），脚本内部会自动匹配目录。

---

## Telegram 通知

```javascript
const https = require('https');
const data = JSON.stringify({chat_id:'6428839227', text: report_text});
const req = https.request('https://api.telegram.org/bot8650394988:AAEXYZe4AZekKfE1xjVDpG0t1fjgglxjsdA/sendMessage', {method:'POST', headers:{'Content-Type':'application/json'}}, res => {});
req.write(data); req.end();
```
