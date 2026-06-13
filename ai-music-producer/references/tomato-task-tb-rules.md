# 番茄专项 Task T-B 规则集（海报+后处理+网站重建）

> 本文件由番茄专项 Task T-B prompt 引用。
> 与现有 Task B 流程基本一致，仅数据源和输出目标不同。

---

## 数据源

读取 `tomato-vault/data/tomato_postprocess.json`（Task T-A' 的产出）。
⚠️ **唯一数据源**。

---

## BeatPrints 海报生成

对每首歌：
1. 检查封面是否存在：`~/Music/番茄音乐/YYYY-MM-DD_歌名/cover_*.{jpg,png}`
2. 检查海报是否已存在：`~/Music/番茄音乐/YYYY-MM-DD_歌名/[歌名]_poster.png`，已存在则跳过
3. 从 mp3 读取真实时长
4. 从歌词提取最有画面感的 4 行

```python
import subprocess, os, json

VAULT_TOMATO = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/tomato-vault")
PYTHON_BEAT = "/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints/.venv/bin/python3.13"
SCRIPT_BEAT = "/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints/generate_poster.py"

with open(os.path.join(VAULT_TOMATO, "data/tomato_postprocess.json")) as f:
    data = json.load(f)

for song in data["songs"]:
    song_dir = song["song_dir"]
    title = song["title"]
    mp3_path = os.path.join(song_dir, f"{title}_v1.mp3")
    
    # 检查封面
    covers = [f for f in os.listdir(song_dir) if f.startswith("cover_") and f.endswith((".jpg", ".png"))]
    if not covers:
        print(f"⏭️ {title}: 无封面，跳过海报")
        continue
    
    # 检查海报是否已存在
    poster_path = os.path.join(song_dir, f"{title}_poster.png")
    if os.path.exists(poster_path):
        print(f"⏭️ {title}: 海报已存在")
        continue
    
    # 读时长
    from mutagen.mp3 import MP3
    secs = int(MP3(mp3_path).info.length)
    duration = f"{secs//60}:{secs%60:02d}"
    
    # 提取4行歌词
    lines = [l for l in song["lyrics"].split("\n") if l.strip() and not l.startswith("[")]
    lyrics_4 = "\n".join(lines[:4])
    
    cover_path = os.path.join(song_dir, covers[0])
    
    result = subprocess.run([
        PYTHON_BEAT, SCRIPT_BEAT,
        "--name", title, "--artist", "王同学",
        "--lyrics", lyrics_4, "--album", title,
        "--released", "2026", "--duration", duration,
        "--label", "🍅 番茄专项", "--theme", "Dark",
        "--accent", "--cover-path", cover_path,
        "--output", song_dir
    ], capture_output=True, text=True, timeout=60)
    print(f"{'✅' if os.path.exists(poster_path) else '❌'} 海报: {title}")
```

---

## 歌词对齐（ForcedAligner）

⚠️ **独立内联脚本，不复用 music-vault 的 `funasr_word_align.py`**（该脚本绑定 music-vault 的 songs.json 路径，且不支持 TOMATO_MODE）。
⚠️ **API 参数名是 `lyrics_text` 不是 `lyrics`**（2026-06-13 踩坑修复）。

### 完整对齐流程

```python
import base64, json, os, re, time, requests, subprocess
from pathlib import Path

VAULT_DIR = Path.home() / "Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/tomato-vault"

# ForcedAligner URL — 优先 SSH tunnel (本地 9777)，回退直连
ASR_URLS = [
    "http://127.0.0.1:9777",       # SSH tunnel → PC:7777
    "http://192.168.50.157:7777",  # PC 直连
    "http://192.168.50.243:7778",  # M2 fallback
]

def find_asr():
    for url in ASR_URLS:
        try:
            r = requests.get(f"{url}/api/health", timeout=3)
            if r.status_code == 200:
                return url
        except:
            pass
    return None

# 如果没有 tunnel，先建立
if not find_asr():
    subprocess.run(["ssh", "-o", "ConnectTimeout=3", "-f", "-N",
                    "-L", "9777:localhost:7777", "pc"],
                   capture_output=True, timeout=10)
    time.sleep(1)

asr_url = find_asr()
if not asr_url:
    print("❌ 无可用 ForcedAligner 服务，跳过 LRC 对齐")
else:
    def forced_align(server_url, mp3_path, lyrics_text, label=""):
        try:
            with open(mp3_path, 'rb') as f:
                audio_b64 = base64.b64encode(f.read()).decode()
            payload = json.dumps({
                "audio_base64": audio_b64,
                "lyrics_text": lyrics_text,  # ⚠️ 不是 lyrics！
                "language": "Chinese"
            }).encode()
            resp = requests.post(
                f"{server_url}/api/align/lrc",
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=300
            )
            result = resp.json()
            lrc_text = result.get("lrc", "")
            entries = []
            for line in lrc_text.strip().split("\n"):
                m = re.match(r'\[(\d+):(\d+\.\d+)\](.+)', line)
                if m:
                    entries.append({
                        "time": int(m.group(1)) * 60 + float(m.group(2)),
                        "text": m.group(3).strip()
                    })
            return entries
        except Exception as e:
            print(f"   ⚠️ {label} 错误: {e}")
            return []

    with open(VAULT_DIR / "data/tomato_postprocess.json") as f:
        data = json.load(f)

    lrc_data = {}
    for song in data["songs"]:
        title = song["title"]
        song_dir = song["song_dir"]
        mp3_path = song["mp3_path"]

        clean_lines = [l.strip() for l in song["lyrics"].split("\n") if l.strip() and not l.strip().startswith("[")]
        clean_lyrics = "\n".join(clean_lines)

        lrc_path = os.path.join(song_dir, f"{title}.lrc")
        if os.path.exists(lrc_path):
            print(f"⏭️ {title}: LRC 已存在")
            continue

        entries = forced_align(asr_url, mp3_path, clean_lyrics, title)
        if entries:
            with open(lrc_path, "w", encoding="utf-8") as f:
                for entry in entries:
                    mins = int(entry["time"] // 60)
                    secs = entry["time"] % 60
                    f.write(f"[{mins:02d}:{secs:05.2f}]{entry['text']}\n")
            print(f"   ✅ {title}: {len(entries)} 行")
            lrc_data[title] = entries
        else:
            print(f"   ❌ {title}: 对齐失败")

    # 更新 lrc_data.json
    lrc_out = VAULT_DIR / "data/lrc_data.json"
    existing = {}
    if lrc_out.exists():
        with open(lrc_out, encoding='utf-8') as f:
            existing = json.load(f)
    for title, entries in lrc_data.items():
        existing[title] = entries
    with open(lrc_out, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
```

---

## 网站重建

```python
import subprocess, os, sys
VAULT_DIR = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/tomato-vault")
PYTHON = sys.executable
result = subprocess.run([PYTHON, os.path.join(VAULT_DIR, "vault.py"), "build"],
                       capture_output=True, text=True, timeout=120, cwd=VAULT_DIR)
print(result.stdout[-2000:])
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
🍅 番茄专项后处理报告 · {日期}

🖼️ 海报: 成功K / 失败L / 跳过M
📝 LRC对齐: K首 (ForcedAligner)
🏗️ 网站已重建

明细:
✅ ① 广场舞「歌名」: 海报+对齐(2.1s)
✅ ② 洗脑情歌「歌名」: 海报+对齐(1.8s)
✅ ③ 伤感情绪「歌名」: 海报+对齐(2.3s)
✅ ④ 国风古风「歌名」: 海报+对齐(1.9s)
✅ ⑤ 家乡励志「歌名」: 海报+对齐(2.0s)
```
