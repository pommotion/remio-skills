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

## 封面生成

⛔ **封面已移至任务 B。** A' 只负责音频生成，不生成封面。

### ⚡ 异步封面提交（A' 阶段）

> **2026-06-30 BizyAir 停服迁移**：封面生成从 BizyAir 切换到 ListenHub (provider=openai → GPT Image 2)，
> Lovart (generate_image_gpt_image_2) 作为 fallback。由 image_provider.py 统一调度。
> submit_one 现在是同步生成（保存到临时目录），fetch_one 从临时目录复制。API 不变。
> BizyAir 恢复后改回异步模式（见 regenerate_covers.py 注释保留的原始代码）。

音频生成完后，追加执行封面提交：

```python
import subprocess, os, sys
VAULT = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
PYTHON = sys.executable
# 提交封面任务（异步，< 5s/首），写入 pending_covers.json
result = subprocess.run(
    [PYTHON, os.path.join(VAULT, "regenerate_covers.py"), "--submit"],
    cwd=VAULT, capture_output=True, text=True, timeout=120)
print(result.stdout[-2000:])
if result.returncode != 0:
    print(f"⚠️ 封面提交失败: {result.stderr[-500:]}")
    # 不阻塞——B 阶段会发现 pending_covers.json 不存在，回退到同步模式
```

⛔ **封面提交铁律**：
- 提交失败不阻塞音频结果，在报告中标记即可
- B 阶段会发现 pending_covers.json 不存在，回退到同步模式
- BizyAir 失败（429 限额/停服/超时）→ 记录失败，**禁止用其他工具补图**
- ListenHub/Lovart 失败同理 → 记录失败，不补图

---

## Telegram 通知

```javascript
const https = require('https');
const data = JSON.stringify({chat_id:'6428839227', text: report_text});
const req = https.request('https://api.telegram.org/bot8650394988:AAEXYZe4AZekKfE1xjVDpG0t1fjgglxjsdA/sendMessage', {method:'POST', headers:{'Content-Type':'application/json'}}, res => {});
req.write(data); req.end();
```
