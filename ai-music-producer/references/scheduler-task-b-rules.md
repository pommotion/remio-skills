# 调度器任务 B 规则集（海报+后处理）

> 本文件由任务 B prompt 引用，包含 BeatPrints 海报、歌词对齐、网站重建的具体命令。

---

## 封面生成（⛔ 海报前置依赖，必须调用 regenerate_covers.py）

> **2026-06-30 BizyAir 停服迁移**：封面生成从 BizyAir 切换到 ListenHub (provider=openai → GPT Image 2)，
> Lovart (generate_image_gpt_image_2) 作为 fallback。由 image_provider.py 统一调度。
> submit 现在是同步生成（保存到临时目录），fetch 从临时目录复制。调用方式不变。
> BizyAir 恢复后改回（见 regenerate_covers.py 注释保留的原始代码）。

**⛔ 绝对禁止**自行写 API 调用、自行构造封面 prompt、使用 gcli2api/mmx image。

### 封面风格规范（v4 五段式通感场景）
脚本自动读取歌词文件，提取物件/动作写进 prompt。风格：英文电影摄影场景描述，暗色调电影质感，极简构图一个核心视觉主体，歌名中文文字自然融入场景元素。

**禁止**出现 "album cover"、"design" 等设计指令词。

### ✅ 正确做法（优先 fetch，回退同步）

```python
import subprocess, os, json, sys
VAULT = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
PYTHON = sys.executable
PENDING = os.path.join(VAULT, "data/pending_covers.json")

if os.path.exists(PENDING):
    # ✅ 异步模式：A' 已提交，B 只需 fetch（秒级）
    print("📥 Fetching covers from async submissions...")
    result = subprocess.run(
        [PYTHON, os.path.join(VAULT, "regenerate_covers.py"), "--fetch"],
        cwd=VAULT, capture_output=True, text=True, timeout=300)
    print(result.stdout[-2000:])
    if result.returncode != 0:
        print(f"⚠️ fetch 失败，回退到同步模式")
        # 回退：同步生成
        songs = ["歌名1", "歌名2"]  # 从 pending_audio.json 获取
        result = subprocess.run(
            [PYTHON, os.path.join(VAULT, "regenerate_covers.py"), "--run", "--songs"] + songs,
            cwd=VAULT, capture_output=True, text=True, timeout=1800)
        print(result.stdout[-2000:])
else:
    # 回退：同步生成（A' 未提交或 pending_covers.json 丢失）
    print("⚠️ pending_covers.json 不存在，回退到同步模式")
    songs = ["歌名1", "歌名2"]  # 从 pending_audio.json 获取
    cmd = [PYTHON, os.path.join(VAULT, "regenerate_covers.py"), "--run", "--songs"] + songs
    result = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True, timeout=1800)
    print(result.stdout[-2000:])
```

封面规格：ListenHub (GPT Image 2 via provider=openai)，1:1 2048×2048。Lovart (generate_image_gpt_image_2) 作为 fallback。脚本内置分辨率兜底（Pillow Lanczos 放大不足 2048 的图片）。

⛔ 封面脚本传入的 `--songs` 参数用**纯歌名**（不含日期前缀），脚本内部会自动匹配目录。

⛔ **封面生成铁律**：
- 必须调用 `regenerate_covers.py`，禁止自行写 API 调用、禁止用 mmx/gcli/ListenHub/generate_image 等其他工具替代
- BizyAir 失败（429 限额/停服/超时）→ 记录失败，在报告中标记，**禁止用其他工具补图**
- ListenHub/Lovart 全部失败同理 → 记录失败，不补图
- BizyAir 停服期间（2026-06-30 起）封面通过 ListenHub→Lovart 链路生成


---

## BeatPrints 海报生成

对每首歌：
1. **检查封面是否存在**：`~/Music/音乐项目/YYYY-MM-DD_歌名/cover_*.{jpg,png}`，不存在则跳过海报。**注意：目录名带日期前缀，从 pending_audio.json 或 songs.json 的 `dir` 字段获取准确路径。**
2. **检查海报是否已存在**：`~/Music/音乐项目/YYYY-MM-DD_歌名/歌名_poster.png`，**已存在则跳过**（除非 `--force`）。
3. 从 mp3 读取真实时长（mutagen）：
```python
from mutagen.mp3 import MP3
# song_dir 从 pending_audio.json 的 songs[].song_dir 获取，或从 songs.json 的 dir 字段
mp3_path = os.path.join(song_dir, f"{song_name}_v1.mp3")
if os.path.exists(mp3_path):
    secs = int(MP3(mp3_path).info.length)
    duration = f"{secs//60}:{secs%60:02d}"
```
3. 从档案笔记提取歌词中最有画面感的 **4 行**，用 `\n` 拼接

逐首生成海报（run_python）：
```python
import subprocess, os
song_name = "歌名"  # 纯歌名，不含日期前缀
song_dir = "~/Music/音乐项目/2026-06-14_歌名"  # 从 pending_audio.json 获取完整目录路径
lyrics_4lines = "第一行\n第二行\n第三行\n第四行"  # 替换
duration = "2:30"  # 真实时长
cover_path = os.path.join(os.path.expanduser(song_dir), f"{song_name}_cover.png")
output_dir = os.path.expanduser(song_dir)
python = "/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints/.venv/bin/python3.13"
script = "/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints/generate_poster.py"
result = subprocess.run([python, script, "--name", song_name, "--artist", "王同学", "--lyrics", lyrics_4lines, "--album", song_name, "--released", "2026", "--duration", duration, "--label", "AI Original", "--theme", "Dark", "--accent", "--cover-path", cover_path, "--output", output_dir], capture_output=True, text=True, timeout=60)
print(result.stdout[-1000:])
```

关键：`--duration` 必须是 mp3 真实时长，`--lyrics` 必须4行用 `\n` 拼接。

---

## 歌词对齐（ForcedAligner）

使用 **Qwen3-ForcedAligner-0.6B** 本地服务，纯本地对齐，不依赖任何在线 API。

### 架构

- **唯一服务**: M2 Mac mini (MLX/MPS, 16GB 统一内存, 端口 7778)
- ~~PC WSL2~~: 已于 2026-06-14 停用，释放 VRAM 给 DiffusionGemma
- 音频 + 已知歌词 → 直接输出 LRC 时间戳，无需 ASR 识别

### 前置检查

```python
import subprocess, os, sys, requests

M2_URL = "http://192.168.50.243:7778"

try:
    r = requests.get(f"{M2_URL}/api/health", timeout=5)
    if r.status_code == 200:
        print(f"✅ M2 MLX: {r.json()['device']}")
    else:
        print("❌ M2 服务异常")
except Exception:
    print("❌ 无可用 ForcedAligner 服务，跳过 LRC 对齐")
```

### 对齐命令

```python
import subprocess, os, sys
VAULT_DIR = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
PYTHON = sys.executable

# 增量对齐（M2 Mac mini 唯一服务）
subprocess.run([PYTHON, os.path.join(VAULT_DIR, "lrc_align.py")],
               capture_output=True, text=True, timeout=600, cwd=VAULT_DIR)
```

### 性能

| 指标 | 旧方案（DashScope ASR+DTW） | 新方案（ForcedAligner） |
|------|---------------------------|------------------------|
| 速度 | ~35s/首 | **~30s/首 (M2 MLX)** |
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
📝 LRC对齐: K个版本 (ForcedAligner M2, ~30s/首)
🏗️ 网站已重建: 总歌曲数首 / 总LRC版本

明细:
✅ 歌名1: 海报+对齐(ForcedAligner M2 28s)
⏭️ 歌名2: 已有LRC
❌ 歌名3: 无封面(海报跳过)
```
