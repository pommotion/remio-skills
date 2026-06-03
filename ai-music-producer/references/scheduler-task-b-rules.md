# 调度器任务 B 规则集（海报+后处理）

> 本文件由任务 B prompt 引用，包含 BeatPrints 海报、歌词对齐、网站重建的具体命令。

---

## BeatPrints 海报生成

对每首歌：
1. **检查封面是否存在**：`~/Desktop/📂 音乐/[歌名]/cover_*.{jpg,png}`，不存在则跳过海报。
2. **检查海报是否已存在**：`~/Desktop/📂 音乐/[歌名]/[歌名]_poster.png`，**已存在则跳过**（除非 `--force`）。
3. 从 mp3 读取真实时长（mutagen）：
```python
from mutagen.mp3 import MP3
mp3_path = os.path.expanduser(f"~/Desktop/📂 音乐/{song_name}/{song_name}_v1.mp3")
if os.path.exists(mp3_path):
    secs = int(MP3(mp3_path).info.length)
    duration = f"{secs//60}:{secs%60:02d}"
```
3. 从档案笔记提取歌词中最有画面感的 **4 行**，用 `\n` 拼接

逐首生成海报（run_python）：
```python
import subprocess, os
song_name = "歌名"  # 替换
lyrics_4lines = "第一行\n第二行\n第三行\n第四行"  # 替换
duration = "2:30"  # 真实时长
cover_path = os.path.expanduser(f"~/Desktop/📂 音乐/{song_name}/{song_name}_cover.png")
output_dir = os.path.expanduser(f"~/Desktop/📂 音乐/{song_name}")
python = "/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints/.venv/bin/python3.13"
script = "/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints/generate_poster.py"
result = subprocess.run([python, script, "--name", song_name, "--artist", "王同学", "--lyrics", lyrics_4lines, "--album", song_name, "--released", "2026", "--duration", duration, "--label", "AI Original", "--theme", "Dark", "--accent", "--cover-path", cover_path, "--output", output_dir], capture_output=True, text=True, timeout=60)
print(result.stdout[-1000:])
```

关键：`--duration` 必须是 mp3 真实时长，`--lyrics` 必须4行用 `\n` 拼接。

---

## 歌词对齐（ForcedAligner）

使用 **Qwen3-ForcedAligner-0.6B** 本地 GPU 服务，替代旧的 Whisper + FunASR + DTW 方案。

### 前置检查

```python
import subprocess, os, sys
VAULT_DIR = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
PYTHON = sys.executable

# 检查服务是否运行
import requests
try:
    # 优先尝试获取 tunnel URL
    result = subprocess.run(
        ["ssh", "pc", "journalctl -u cloudflared-asr --no-pager | grep -o 'https://[a-z0-9-]*\\.trycloudflare\\.com' | tail -1"],
        capture_output=True, text=True, timeout=10,
    )
    tunnel = result.stdout.strip()
    if tunnel:
        r = requests.get(f"{tunnel}/api/health", timeout=5, verify=False)
        health = r.json()
        ASR_URL = tunnel
    else:
        raise Exception("no tunnel")
except Exception:
    # fallback: 局域网
    try:
        r = requests.get("http://192.168.50.157:7777/api/health", timeout=3)
        health = r.json()
        ASR_URL = "http://192.168.50.157:7777"
    except Exception:
        health = None
        ASR_URL = None

if health:
    print(f"✅ ForcedAligner: {health['gpu']} ({health['vram_used_gb']}GB)")
else:
    print("❌ ForcedAligner 服务不可用，跳过 LRC 对齐")
```

### 对齐命令

```python
import subprocess, os, sys
VAULT_DIR = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
SCRIPT = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/remio/skills/ai-music-producer/scripts/lrc_align.py")
PYTHON = sys.executable

# 4a: 更新 songs.json
subprocess.run([PYTHON, os.path.join(VAULT_DIR, "build.py"), "extract"], capture_output=True, text=True, timeout=120, cwd=VAULT_DIR)

# 4b: ForcedAligner 歌词对齐（自动获取 tunnel URL，增量处理）
subprocess.run([PYTHON, SCRIPT, "--batch", "--rebuild"], capture_output=True, text=True, timeout=300, cwd=VAULT_DIR)
```

**注意**：`lrc_align.py --batch` 会自动获取 tunnel URL、增量跳过已对齐的歌曲、更新 `lrc_data.json`。

### 性能

| 指标 | 旧方案（Whisper+DTW） | 新方案（ForcedAligner） |
|------|----------------------|------------------------|
| 速度 | ~35s/首 | **~2-3s/首** |
| 准确率 | 后半首 Chorus 崩溃 | **全曲逐字精确** |
| 依赖 | DashScope API + Whisper | 本地 GPU（1.7GB VRAM） |

---

## Telegram 报告

用 run_node 发报告：
```javascript
const https = require('https');
const data = JSON.stringify({chat_id:'6428839227', text: report_text});
const req = https.request('https://api.telegram.org/bot8650394988:AAEXYZe4AZekKfE1xjVDpG0t1fjgglxjsdA/sendMessage', {method:'POST', headers:{'Content-Type':'application/json'}}, res => {});
req.write(data); req.end();
```

报告格式：
```
🎵 后处理报告 · {日期}

🖼️ 海报: 成功K / 失败L / 跳过M
📝 LRC对齐: K个版本 (ForcedAligner, ~2s/首)
🏗️ 网站已重建: 总歌曲数首 / 总LRC版本

明细:
✅ 歌名1: 海报+对齐(ForcedAligner 1.8s)
⏭️ 歌名2: 已有LRC
❌ 歌名3: 无封面(海报跳过)
```
