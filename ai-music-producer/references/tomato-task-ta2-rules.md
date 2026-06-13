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
- ⚠️ **时长要求**：T-A 的 mmx_prompt 已包含 `full length song 3-4 minutes` 指引，目标时长 ≥180s。生成后用 `afinfo` 校验，低于 170s 的重试。

单首失败不阻塞，超时600s。

### 输出目录（番茄专项）

```
~/Music/番茄音乐/YYYY-MM-DD_歌名/[歌名]_v1.mp3
```

⚠️ **路径铁律**：目录名必须带日期前缀（从 `tomato_audio.json` 的 `song_dir` 字段读取，不要自行拼接）。

### 逐首生成流程

```python
import subprocess, os, json

VAULT = os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/tomato-vault")
MMX = os.path.expanduser("~/Library/Application Support/remio/Users/SharedData/runtime/npm-global/bin/mmx")

with open(os.path.join(VAULT, "data/tomato_audio.json")) as f:
    data = json.load(f)

for song in data["songs"]:
    song_dir = song["song_dir"]
    os.makedirs(song_dir, exist_ok=True)
    
    # 写歌词临时文件
    lyrics_path = os.path.join(song_dir, "lyrics.txt")
    with open(lyrics_path, "w") as f:
        f.write(song["lyrics"])
    
    # 生成音频
    out_path = os.path.join(song_dir, f"{song['title']}_v1.mp3")
    if os.path.exists(out_path):
        print(f"⏭️ {song['title']} 已存在，跳过")
        continue
    
    env = os.environ.copy()
    env["PATH"] = os.path.expanduser("~/.nvm/versions/node/v22.18.0/bin") + ":" + env["PATH"]
    
    result = subprocess.run([
        MMX, "music", "generate",
        "--prompt", song["mmx_prompt"],
        "--lyrics-file", lyrics_path,
        "--model", "music-2.6",
        "--out", out_path
    ], capture_output=True, text=True, timeout=600, env=env)
    
    # 时长校验
    if os.path.exists(out_path):
        af = subprocess.run(['afinfo', out_path], capture_output=True, text=True, timeout=5)
        for line in af.stdout.split('\n'):
            if 'estimated duration' in line:
                secs = round(float(line.split(':')[-1].strip().replace('sec', '').strip()))
                print(f"{'✅' if secs >= 170 else '⚠️'} {song['title']} → {secs//60}:{secs%60:02d}")
                break
    else:
        print(f"❌ {song['title']}")
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

⚠️ 封面规格：1:1 方形，目标 1024×1024，GPT Image 2 via BizyAir ModelZoo。`generate_one` 已内置 sips center-crop 兜底（下载后自动裁方）。生成后统一缩放到 1024×1024。

### 调用方式

```python
import subprocess, os, json, time, shutil
from pathlib import Path
from datetime import datetime

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

for i, song in enumerate(data["songs"]):
    title = song["title"]
    genre_code = song["genre_code"]
    song_dir = song["song_dir"]
    prompt = COVER_PROMPTS[genre_code]

    out_path = os.path.join(song_dir, f"cover_{title}.jpg")
    if os.path.exists(out_path):
        print(f"⏭️  [{i+1}] {title} 封面已存在")
        continue

    tmp_path = f"/tmp/cover_tomato_{title}.jpg"
    result = generate_one(prompt, tmp_path)
    if result["ok"]:
        # 统一缩放到 1024×1024
        subprocess.run(['sips', '-z', '1024', '1024', tmp_path],
                      capture_output=True, timeout=10)
        shutil.copy2(tmp_path, out_path)
        print(f"   ✅ {title}: {result['size_kb']}KB (1024×1024)")
    else:
        print(f"   ❌ {title}: {result['error'][:80]}")
    if i < len(data["songs"]) - 1:
        time.sleep(2)
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
