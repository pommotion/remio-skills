# LLM API 配置（A/A'/B 共用）

> 本文件被调度器任务 A 引用。所有 LLM API 的 URL、模型名、Key 读取方式在此维护。

## Key 读取工具函数

```python
import re, os, json

def read_env(name):
    p = os.path.expanduser('~/.zshrc')
    if not os.path.exists(p): return ''
    text = open(p).read()
    m = re.search(rf'^export {name}=(["\x27]?)([^"\'\n]+)\1', text, re.M)
    return m.group(2) if m else ''
```

⛔ **禁止** `subprocess.run(['zsh','-c','source ~/.zshrc ...'])`，sandbox 会拦截 `/dev/null` 导致整个 source 失败。统一用上面的 `read_env()`。

## API 优先级（成功即停，每个只试一次，超时 60s）

| # | API | Base URL | Model | Key |
|---|-----|----------|-------|-----|
| 1 | SiliconFlow（⚠️ 优先） | `https://api.siliconflow.cn/v1/` | `nex-agi/Nex-N2-Pro` | `read_env('SF_API_KEY')` |
| 2 | GLM（智谱） | `https://open.bigmodel.cn/api/coding/paas/v4/` | `glm-5.1` | `read_env('GLM_API_KEY')` |
| 3 | MiniMax | `https://api.minimaxi.com/v1/chat/completions` | `MiniMax-M3` | `json.load(open(os.path.expanduser('~/.mmx/config.json')))['api_key']` |
| 4 | DeepSeek | `https://api.deepseek.com/chat/completions` | `deepseek-chat` | `read_env('DEEPSEEK_API_KEY')` |
| 5 | Longcat | `https://longcat.chat/v1/chat/completions` | `longcat-llm` | `read_env('LONGCAT_API_KEY')` |

## 用途分配（Task A 各环节用哪个 API）

| 环节 | 主力 API | Fallback | 模型 | 为什么选它 |
|------|---------|----------|------|-----------|
| **歌词创作** | SiliconFlow | DeepSeek → MiniMax | `nex-agi/Nex-N2-Pro` | 响应快 ~7s、中文质量好、无 reasoning_content 膨胀 |
| **诗化审核** | DeepSeek（⛔ 强制） | 无（禁止 GLM） | `deepseek-chat` | 对短句规则执行克制，不过度压缩行长 |
| **Phase 0 探测** | SiliconFlow + DeepSeek | — | 两个都要测 | 只测实际会用的，不浪费时间 |

⚠️ **SiliconFlow**：无 reasoning_content 问题，响应快（~7s），中文质量好。歌词创作首选。
⚠️ **DeepSeek**：诗化审核首选。歌词创作时做 SiliconFlow 的 fallback。
⚠️ **GLM-5.1**：⛔ 禁止用于歌词/诗化审核（reasoning_content 膨胀 + 过度压缩行长）。仅保留做 Phase 5 状态报告。
⚠️ **MiniMax / Longcat**：仅兜底。
