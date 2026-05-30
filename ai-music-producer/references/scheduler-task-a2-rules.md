# 调度器任务 A' 规则集（音频+封面）

> 本文件由任务 A' prompt 引用，包含 mmx CLI 用法、封面生成脚本调用方式、Telegram 通知。

---

## mmx CLI 音频生成

- mmx路径：`~/Library/Application Support/remio/Users/SharedData/runtime/npm-global/bin/mmx`
- Node路径：`~/.nvm/versions/node/v22.18.0/bin`（必须加入PATH）
- 命令：`mmx music generate --prompt "风格描述" --lyrics-file 歌词.txt --model music-2.6 --out 输出.mp3`

单首失败不阻塞，超时600s。输出目录：`~/Desktop/📂 音乐/[歌名]/[歌名]_v1.mp3`

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

封面规格：bozo-aigc (BizyAir GPT Image 2)，1:1 2048×2048。

---

## Telegram 通知

```javascript
const https = require('https');
const data = JSON.stringify({chat_id:'6428839227', text: report_text});
const req = https.request('https://api.telegram.org/bot8650394988:AAEXYZe4AZekKfE1xjVDpG0t1fjgglxjsdA/sendMessage', {method:'POST', headers:{'Content-Type':'application/json'}}, res => {});
req.write(data); req.end();
```
