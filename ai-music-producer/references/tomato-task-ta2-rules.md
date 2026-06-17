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

### 输出目录（番茄专项）

```
~/Music/番茄音乐/YYYY-MM-DD_歌名/[歌名]_v1.mp3
```

⚠️ **路径铁律**：目录名必须带日期前缀（从 `tomato_audio.json` 的 `song_dir` 字段读取，不要自行拼接）。

### ⚡ 并行生成流程（ThreadPoolExecutor max_workers=5）

> **根因修复（2026-06-17）**：串行 5 首 × 3-5min = 15-25min，叠加封面 ≈ 3min，总逼近 30min RPC 上限。
> mmx CLI 每个进程是独立 HTTP API 客户端，API 侧无并发限制 → 5 首同时跑，总耗时 ≈ 最慢的一首 ≈ 3-5min。

```python
import subprocess, os, json
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
        print(f"❌ {title} mmx 失败: {result.stderr[:200]}")
        return (title, False)
    
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

**⛔ 必须调用 `regenerate_covers.py`**（复用 music-vault 的脚本），禁止自行写 API 调用。

### 番茄专项封面提示词调整

`regenerate_covers.py` 会自动从歌词提取意象。但番茄专项需要额外风格化：

| 曲风 | 封面视觉方向 |
|:---|:---|
| ① 广场舞 | 霓虹灯 / 舞蹈剪影 / 鲜艳对比色 |
| ② 洗脑情歌 | 糖果色 / 少女风 / 可爱手绘 |
| ③ 伤感情绪 | 雨夜 / 窗台 / 冷色调 / 孤独感 |
| ④ 国风古风 | 水墨 / 扇面 / 古典纹样 / 朱砂 |
| ⑤ 家乡励志 | 田野 / 老屋 / 暖色调 / 夕阳 |

⚠️ 封面规格：1:1 方形，**双文件输出**：
- **`cover_{title}.jpg`** = 1024×1024（网页版，体积小，用于 tomato.1986318.xyz 网站，不影响加载速度）
- **`cover_{title}_2048.jpg`** = 2048×2048（上传版，用于番茄音乐平台上传，满足 ≥1440×1440 要求）

GPT Image 2 via BizyAir ModelZoo，`resolution=2K` 直接出 2048×2048。`generate_one` 已内置 sips center-crop 兜底（下载后自动裁方）。

### 调用方式

```python
import subprocess, os, json, time, shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

VAULT_TOMATO = Path.home() / "Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/tomato-vault"

# ⚠️ 不复用 regenerate_covers.py（绑定 music-vault 的 songs.json，不支持 TOMATO_MODE）
# 直接复用 generate_one 函数
VAULT_MUSIC = Path.home() / "Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault"
import importlib.util
spec = importlib.util.spec_from_file_location("regen_covers", str(VAULT_MUSIC / "regenerate_covers.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
generate_one = mod.generate_one

# 番茄封面提示词（按曲风）
COVER_PROMPTS = {
    "dance": "Album cover art for a Chinese square dance song. Neon lights, dance silhouettes, vibrant contrasting colors, energetic party atmosphere, DJ vibe, dynamic composition, 1:1 square format",
    "viral_pop": "Album cover art for a sweet Chinese pop love song. Candy colors, cute girly aesthetic, hand-drawn style, hearts and sweets, pastel pink background, kawaii style, 1:1 square format",
    "sad": "Album cover art for an emotional Chinese sad ballad. Rainy night, window sill, cold blue tones, lonely atmosphere, melancholic mood, minimalist design, 1:1 square format",
    "guofeng": "Album cover art for a Chinese traditional guofeng song. Chinese ink painting style, red seal stamps, plum blossom, ancient fan pattern, vermillion accents on rice paper texture, elegant and atmospheric, 1:1 square format",
    "hometown": "Album cover art for a Chinese folk hometown song. Warm sunset countryside, old village house with a glowing lamp, field landscape, nostalgic warm tones, emotional and heartfelt, 1:1 square format",
}

with open(VAULT_TOMATO / "data/tomato_audio.json") as f:
    data = json.load(f)

# ⚡ 并行生成封面（ThreadPoolExecutor）
# 根因修复：串行 5 首封面 ≈ 10-15min，叠加音频生成极易超时 30min
# 并行后 5 首同时跑，总耗时 ≈ 最慢的一首 ≈ 2-3min
def gen_one_cover(song):
    """单首封面生成 worker（含 1 次重试）"""
    title = song["title"]
    genre_code = song["genre_code"]
    song_dir = song["song_dir"]
    prompt = COVER_PROMPTS[genre_code]
    out_path = os.path.join(song_dir, f"cover_{title}.jpg")
    if os.path.exists(out_path):
        return {"title": title, "ok": True, "skipped": True}
    tmp_path = f"/tmp/cover_tomato_{title}.jpg"
    result = generate_one(prompt, tmp_path)
    if not result["ok"]:
        time.sleep(5)
        result = generate_one(prompt, tmp_path)
    if result["ok"]:
        from PIL import Image
        img = Image.open(tmp_path)
        img_1024 = img.resize((1024, 1024), Image.LANCZOS)
        img_1024.save(out_path, "JPEG", quality=90)
        out_2048 = out_path.replace('.jpg', '_2048.jpg')
        shutil.copy2(tmp_path, out_2048)
        size_1024 = os.path.getsize(out_path) // 1024
        size_2048 = os.path.getsize(out_2048) // 1024
        return {"title": title, "ok": True, "msg": f"1024 ({size_1024}KB) + 2048 ({size_2048}KB) in {result['elapsed']:.0f}s"}
    else:
        return {"title": title, "ok": False, "error": result["error"][:80]}

tasks_batch = [s for s in data["songs"]]
with ThreadPoolExecutor(max_workers=5) as pool:
    futures = {pool.submit(gen_one_cover, s): s for s in tasks_batch}
    for fut in as_completed(futures):
        r = fut.result()
        if r.get("skipped"):
            print(f"⏭️  {r['title']} 封面已存在")
        elif r["ok"]:
            print(f"   ✅ {r['title']}: {r['msg']}")
        else:
            print(f"   ❌ {r['title']}: {r['error']}")
```

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
