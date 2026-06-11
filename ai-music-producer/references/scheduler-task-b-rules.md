# 调度器任务 B 规则集（海报+后处理）

> 本文件由任务 B prompt 引用，包含 BeatPrints 海报、歌词对齐、网站重建的具体命令。

---

## BeatPrints 海报生成

对每首歌：
1. **检查封面是否存在**：`~/Music/音乐项目/[歌名]/cover_*.{jpg,png}`，不存在则跳过海报。
2. **检查海报是否已存在**：`~/Music/音乐项目/[歌名]/[歌名]_poster.png`，**已存在则跳过**（除非 `--force`）。
3. 从 mp3 读取真实时长（mutagen）：
```python
from mutagen.mp3 import MP3
mp3_path = os.path.expanduser(f"~/Music/音乐项目/{song_name}/{song_name}_v1.mp3")
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
cover_path = os.path.expanduser(f"~/Music/音乐项目/{song_name}/{song_name}_cover.png")
output_dir = os.path.expanduser(f"~/Music/音乐项目/{song_name}")
python = "/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints/.venv/bin/python3.13"
script = "/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints/generate_poster.py"
result = subprocess.run([python, script, "--name", song_name, "--artist", "王同学", "--lyrics", lyrics_4lines, "--album", song_name, "--released", "2026", "--duration", duration, "--label", "AI Original", "--theme", "Dark", "--accent", "--cover-path", cover_path, "--output", output_dir], capture_output=True, text=True, timeout=60)
print(result.stdout[-1000:])
```

关键：`--duration` 必须是 mp3 真实时长，`--lyrics` 必须4行用 `\n` 拼接。

---

## 歌词对齐（ForcedAligner）

使用 **Qwen3-ForcedAligner-0.6B** 本地 GPU 服务，纯本地对齐，不依赖任何在线 API。

### 架构

- **主服务**: PC WSL2 (RTX 4070 Ti SUPER, 1.7GB VRAM)
- **Fallback**: M2 Mac mini (MLX/MPS, 16GB 统一内存)
- 音频 + 已知歌词 → 直接输出 LRC 时间戳，无需 ASR 识别

### 前置检查

```python
import subprocess, os, sys, requests

# 检查 PC 服务
PC_URL = "http://192.168.50.157:7777"
M2_URL = "http://192.168.50.243:7778"

backend = None
try:
    r = requests.get(f"{PC_URL}/api/health", timeout=3)
    if r.status_code == 200:
        backend = 'pc'
        print(f"✅ PC GPU: {r.json()['gpu']}")
except Exception:
    pass

if not backend:
    try:
        r = requests.get(f"{M2_URL}/api/health", timeout=3)
        if r.status_code == 200:
            backend = 'm2'
            print(f"✅ M2 MLX: {r.json()['device']}")
    except Exception:
        pass

if not backend:
    print("❌ 无可用 ForcedAligner 服务，跳过 LRC 对齐")
```

### 对齐命令

```python
import subprocess, os, sys
VAULT_DIR = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
PYTHON = sys.executable

# 增量对齐（自动检测 PC/M2，PC 优先）
subprocess.run([PYTHON, os.path.join(VAULT_DIR, "funasr_word_align.py")],
               capture_output=True, text=True, timeout=600, cwd=VAULT_DIR)
```

### 性能

| 指标 | 旧方案（DashScope ASR+DTW） | 新方案（ForcedAligner） |
|------|---------------------------|------------------------|
| 速度 | ~35s/首 | **~2-3s/首 (PC GPU)** / ~30s/首 (M2) |
| 准确率 | 后半首 Chorus 崩溃 | **全曲逐字精确** |
| 依赖 | DashScope API（付费） | 本地 GPU（免费） |

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
