# 调度器任务 B 规则集（海报+后处理）

> 本文件由任务 B prompt 引用，包含 BeatPrints 海报、Whisper 转写、歌词对齐、网站重建的具体命令。

---

## BeatPrints 海报生成

对每首歌：
1. 检查 `~/Desktop/📂 音乐/[歌名]/[歌名]_cover.png` 是否存在。不存在则跳过。
2. 从 mp3 读取真实时长（mutagen）：
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
result = subprocess.run([python, script, "--name", song_name, "--artist", "violin", "--lyrics", lyrics_4lines, "--album", song_name, "--released", "2026", "--duration", duration, "--label", "AI Original", "--theme", "Dark", "--cover-path", cover_path, "--output", output_dir], capture_output=True, text=True, timeout=60)
print(result.stdout[-1000:])
```

关键：`--duration` 必须是 mp3 真实时长，`--lyrics` 必须4行用 `\n` 拼接。

---

## Whisper 转写

对每首有 MP3 的歌，检查是否已有 `.fine.json`，没有则转写：

```python
import subprocess, os, glob
WHISPER_CLI = "/Applications/Memo.app/Contents/Resources/addon/whisper/bin/1.8.4/whisper-cli"
MODEL = os.path.expanduser("~/Library/Application Support/Memo/models/ggml-large-v3-turbo.bin")
MUSIC_DIR = os.path.expanduser("~/Desktop/📂 音乐")
songs = ["歌名1", "歌名2"]  # 替换

for song in songs:
    song_dir = os.path.join(MUSIC_DIR, song)
    mp3s = sorted(glob.glob(os.path.join(song_dir, "*.mp3")))
    for mp3 in mp3s:
        base = os.path.splitext(os.path.basename(mp3))[0]
        fine_path = os.path.join(song_dir, f"{base}.fine.json")
        if os.path.exists(fine_path):
            continue
        result = subprocess.run([WHISPER_CLI, "-m", MODEL, "-l", "zh", "-f", mp3, "--output-json-full", "-of", os.path.join(song_dir, base), "-ml", "20", "--split-on-word"], capture_output=True, text=True, timeout=120)
        raw_json = os.path.join(song_dir, f"{base}.json")
        if os.path.exists(raw_json) and not os.path.exists(fine_path):
            os.rename(raw_json, fine_path)
```

每首约8-12秒。

---

## 歌词对齐 + Rebuild 网站

```python
import subprocess, os, sys
VAULT_DIR = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
PYTHON = sys.executable

# 4a: 更新 songs.json
subprocess.run([PYTHON, os.path.join(VAULT_DIR, "build.py"), "extract"], capture_output=True, text=True, timeout=120, cwd=VAULT_DIR)

# 4b: 歌词对齐（增量）
subprocess.run([PYTHON, os.path.join(VAULT_DIR, "align_lyrics.py")], capture_output=True, text=True, timeout=120, cwd=VAULT_DIR)

# 4c: rebuild 网站
subprocess.run([PYTHON, os.path.join(VAULT_DIR, "vault.py"), "build"], capture_output=True, text=True, timeout=120, cwd=VAULT_DIR)
```

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
🎤 Whisper: 转写N首
📝 LRC对齐: K个版本
🏗️ 网站已重建: 总歌曲数首 / 总LRC版本

明细:
✅ 歌名1: 海报+转写+对齐
⏭️ 歌名2: 已有LRC
❌ 歌名3: 无封面(海报跳过)
```
