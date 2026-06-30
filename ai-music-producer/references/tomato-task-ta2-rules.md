# 番茄专项 Task T-A' 规则集（音频+封面）

> 本文件由番茄专项 Task T-A' prompt 引用。
> 与现有 Task A' 流程基本一致，仅数据源和输出目录不同。

---

## 数据源

读取 `tomato-vault/data/tomato_audio.json`（Task T-A 的产出）。
⚠️ **唯一数据源**，不依赖任何其他输入。

---

## mmx CLI 音频生成

- mmx路径：`~/Library/Application Support/remio/Users/SharedData/runtime/npm-global/bin/mmx`
- Node路径：`~/.nvm/versions/node/v22.18.0/bin`（必须加入PATH）
- 命令：`mmx music generate --prompt "风格描述" --lyrics-file 歌词.txt --model music-2.6 --out 输出.mp3`
- ⚠️ **时长要求**：生成后用 `afinfo` 校验。低于阈值的重试 **最多 1 次**，仍不达标则标记 ⚠️ 接受当前版本（不无限重试）。
  - 曲风阈值（T-A 歌词行数已提标，正常应全部达标）：
    - `dance` / `viral_pop` / `hometown`：≥150s（快节奏曲风天然偏短）
    - `sad` / `guofeng`：≥170s

单首失败不阻塞，超时600s。

⛔ **mmx 失败处理铁律**：任何 mmx 错误（code 1/5/6/网络/超时）→ 等 30s → 重试 1 次 → 还失败就跳过该首歌。**禁止排查代理、网络配置、vibe-isla、mmx config 等**，也不允许单独用 bash 调 mmx 测试。全在 `generate_one_song` 内完成。

### 输出目录（番茄专项）

```
~/Music/番茄音乐/YYYY-MM-DD_歌名/[歌名]_v1.mp3
```

⚠️ **路径铁律**：目录名必须带日期前缀（从 `tomato_audio.json` 的 `song_dir` 字段读取，不要自行拼接）。

### ⚡ 并行生成流程（ThreadPoolExecutor max_workers=5）

> **根因修复（2026-06-17）**：串行 5 首 × 3-5min = 15-25min，叠加封面 ≈ 3min，总逼近 30min RPC 上限。
> mmx CLI 每个进程是独立 HTTP API 客户端，API 侧无并发限制 → 5 首同时跑，总耗时 ≈ 最慢的一首 ≈ 3-5min。

```python
import subprocess, os, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed

VAULT = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/tomato-vault")
MMX = os.path.expanduser("~/Library/Application Support/remio/Users/SharedData/runtime/npm-global/bin/mmx")
MMX_ENV = os.environ.copy()
MMX_ENV["PATH"] = os.path.expanduser("~/.nvm/versions/node/v22.18.0/bin") + ":" + MMX_ENV["PATH"]

DURATION_THRESHOLD = {"dance": 150, "viral_pop": 150, "hometown": 150, "sad": 170, "guofeng": 170}

with open(os.path.join(VAULT, "data/tomato_audio.json")) as f:
    data = json.load(f)

# ---- 准备阶段（串行，快）----
tasks = []
for song in data["songs"]:
    song_dir = song["song_dir"]
    os.makedirs(song_dir, exist_ok=True)
    lyrics_path = os.path.join(song_dir, "lyrics.txt")
    with open(lyrics_path, "w") as f:
        f.write(song["lyrics"])
    out_path = os.path.join(song_dir, f"{song['title']}_v1.mp3")
    if os.path.exists(out_path):
        print(f"⏭️ {song['title']} 已存在，跳过")
        continue
    tasks.append(song)

# ---- 单首生成函数（供并行调用）----
def generate_one_song(song):
    """生成单首音频 + 时长校验 + 最多重试 1 次。返回 (title, success)"""
    song_dir = song["song_dir"]
    lyrics_path = os.path.join(song_dir, "lyrics.txt")
    out_path = os.path.join(song_dir, f"{song['title']}_v1.mp3")
    title = song['title']
    genre_code = song['genre_code']
    
    def check_duration(path, attempt=1):
        if not os.path.exists(path):
            print(f"❌ {title}: 文件不存在")
            return False
        af = subprocess.run(['afinfo', path], capture_output=True, text=True, timeout=5)
        for line in af.stdout.split('\n'):
            if 'estimated duration' in line:
                secs = round(float(line.split(':')[-1].strip().replace('sec', '').strip()))
                threshold = DURATION_THRESHOLD.get(genre_code, 170)
                ok = secs >= threshold
                print(f"{'✅' if ok else '⚠️'} {title} → {secs//60}:{secs%60:02d} (阈值 {threshold}s, 尝试 {attempt}/2)")
                return ok
        return False
    
    # 第 1 次生成
    result = subprocess.run([
        MMX, "music", "generate",
        "--prompt", song["mmx_prompt"],
        "--lyrics-file", lyrics_path,
        "--model", "music-2.6",
        "--out", out_path
    ], capture_output=True, text=True, timeout=600, env=MMX_ENV)
    
    if result.returncode != 0:
        print(f"⚠️ {title} mmx 第1次失败: {result.stderr[:200]}")
        print(f"   等 30s 后重试...")
        time.sleep(30)
        result2 = subprocess.run([
            MMX, "music", "generate",
            "--prompt", song["mmx_prompt"],
            "--lyrics-file", lyrics_path,
            "--model", "music-2.6",
            "--out", out_path
        ], capture_output=True, text=True, timeout=600, env=MMX_ENV)
        if result2.returncode != 0:
            print(f"❌ {title} mmx 重试后仍失败: {result2.stderr[:200]}")
            return (title, False)
        else:
            print(f"✅ {title} mmx 重试成功")
            result = result2  # 用重试结果继续走时长校验
    
    ok = check_duration(out_path, attempt=1)
    if not ok:
        os.remove(out_path)
        result2 = subprocess.run([
            MMX, "music", "generate",
            "--prompt", song["mmx_prompt"],
            "--lyrics-file", lyrics_path,
            "--model", "music-2.6",
            "--out", out_path
        ], capture_output=True, text=True, timeout=600, env=MMX_ENV)
        ok = check_duration(out_path, attempt=2)
        if not ok:
            print(f"   ⚠️ {title} 重试后仍偏短，接受当前版本")
    
    return (title, os.path.exists(out_path))

# ---- ⚡ 并行生成 5 首 ----
print(f"\n🎵 并行生成 {len(tasks)} 首音频 (max_workers=5)...")
with ThreadPoolExecutor(max_workers=5) as pool:
    futures = {pool.submit(generate_one_song, song): song for song in tasks}
    for future in as_completed(futures):
        title, success = future.result()
        status = "✅" if success else "❌"
        print(f"{status} {title} 完成")
```

---

## 封面生成

### ⚡ 异步提交模式（2026-06-28 改造）

> **2026-06-30 BizyAir 停服迁移**：封面生成从 BizyAir 切换到 ListenHub (provider=openai → GPT Image 2)，
> Lovart (generate_image_gpt_image_2) 作为 fallback。由 image_provider.py 统一调度。
> submit 现在是同步生成（保存到临时目录），fetch 从临时目录复制。调用方式不变。
> BizyAir 恢复后改回（见 regenerate_covers.py 注释保留的原始代码）。

音频生成完后，追加执行封面提交：

```python
import subprocess, os, sys
VAULT = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault")
PYTHON = sys.executable
# 提交封面任务（异步，< 5s/首），写入 tomato-vault/data/pending_covers.json
result = subprocess.run(
    [PYTHON, os.path.join(VAULT, "regenerate_covers.py"), "--submit", "--source", "tomato"],
    cwd=VAULT, capture_output=True, text=True, timeout=120)
print(result.stdout[-2000:])
if result.returncode != 0:
    print(f"⚠️ 封面提交失败: {result.stderr[-500:]}")
    # 不阻塞——T-B 会发现 pending_covers.json 不存在，回退到同步模式
```

⛔ **封面提交铁律**：
- 提交失败不阻塞音频结果，在报告中标记即可
- T-B 阶段会发现 pending_covers.json 不存在，回退到同步模式
- BizyAir 失败（429 限额/停服/超时）→ 记录失败，**禁止用其他工具补图**
- ListenHub/Lovart 失败同理 → 记录失败，不补图

### ⚠️ 封面提示词来源

**从 `tomato_audio.json` 每首歌的 `cover_prompt` 字段读取**（Task T-A 已为每首歌生成了差异化提示词）。
不再使用硬编码字典。

封面规格：1:1 方形，**双文件输出**：
- **`cover_{title}.jpg`** = 1024×1024（网页版，体积小，用于 tomato.1986318.xyz 网站，不影响加载速度）
- **`cover_{title}_2048.jpg`** = 2048×2048（上传版，用于番茄音乐平台上传，满足 ≥1440×1440 要求）

GPT Image 2 via ListenHub (provider=openai)，Lovart 作为 fallback。脚本内置 Pillow 分辨率兜底。

---

## 数据交接：写入 `tomato_postprocess.json`

生成完成后，将 5 首歌的状态写入：

```json
{
  "date": "2026-06-14",
  "songs": [
    {
      "title": "歌名",
      "genre_code": "dance",
      "genre_label": "广场舞",
      "song_dir": "/Users/wanglingwei/Music/番茄音乐/2026-06-14_歌名",
      "slug": "歌名_2026-06-14",
      "date": "2026-06-14",
      "chord": "6415",
      "bpm": 128,
      "mp3_path": "/Users/wanglingwei/Music/番茄音乐/2026-06-14_歌名/歌名_v1.mp3",
      "cover_path": "/Users/wanglingwei/Music/番茄音乐/2026-06-14_歌名/cover_*.jpg",
      "lyrics": "[完整歌词]"
    }
  ]
}
```

写入路径：`tomato-vault/data/tomato_postprocess.json`

---

## 产出校验

1. 确认 5 首 MP3 全部生成
2. 确认 5 张封面已生成
3. 确认 `tomato_postprocess.json` 已写入
4. 报告格式：`🍅 音频生成：5/5 成功；封面：5/5 成功`
