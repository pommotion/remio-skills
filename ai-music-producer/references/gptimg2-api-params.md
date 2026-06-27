# GPT Image 2 API 参数参考

## 版本 A: gcli2api (Nano Banana 2 / gemini-3.1-flash-image)

- API: POST http://${GCLI2API_HOST}:7861/antigravity/v1/models/gemini-3.1-flash-image:generateContent
- Headers: {"x-goog-api-key": "violin", "Content-Type": "application/json"}
- Body: {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
- 返回 candidates[0].content.parts 中 inlineData.data 是 base64 图片
- 耗时约 15-25s，免费

## 版本 B: BizyAir O.2 (ModelZoo 渠道版 GPT Image 2)

- API: POST https://api.bizyair.cn/x/v1/modelzoo/tasks/openapi/bza-image-o2-base/text-to-image
- 状态查询: GET https://api.bizyair.cn/x/v1/modelzoo/tasks/openapi/{request_id}
- 始终异步：返回 request_id 后需轮询 status 变 Success 再取 outputs[0].images[0] URL
- Headers: {"Content-Type": "application/json", "Authorization": "Bearer $BIZYAIR_API_KEY", "lang": "zh"}
- Body: {"prompt": prompt, "aspect_ratio": "1:1", "resolution": "2K"}
- 耗时约 60-180s，API 付费

> ⚠️ **BizyAir API Key**（硬编码，scheduler 子进程不继承 zshrc）：`sk-hpncrzwkqyghhzqxpvpawdorfszsykrbbquioohhrloaovzi`

> ⚠️ 旧版 /w/v1/webapp/task/openapi/create（同步 webapp 接口）已废弃：
> bozo-aigc 同步模式 + 无重试控制 → 超时重试导致重复提交（2026-06-02 2200 2800 积分根因）
> 现在统一走 ModelZoo 异步 API。

## bizyair-skill CLI 调用（推荐）

```bash
python3 ~/Library/Application\ Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/remio/skills/bizyair-skill/scripts/cli.py \
  modelzoo-run bza-image-o2-base/text-to-image \
  --param "prompt=..." \
  --param "aspect_ratio=1:1" \
  --param "resolution=2K" \
  --api-key $BIZYAIR_API_KEY
```

## 测试图片存储

- 保存到 /tmp/gptimg2_gcli_{编号}.png 和 /tmp/gptimg2_bizyair_{编号}.png
- 同时复制到 .notes/ 目录（remio 笔记图片从这里读取）
- 笔记中用 `![gcli2api](gptimg2_gcli_{编号}.png)` 和 `![BizyAir](gptimg2_bizyair_{编号}.png)` 引用

## Telegram Bot

- BOT_TOKEN: 8650394988:AAEXYZe4AZekKfE1xjVDpG0t1fjgglxjsdA
- CHAT_ID: 6428839227

## 笔记 & Collection

- 总笔记 ID: mov604kk7kdqjpkbyg7（@小小东 · GPT Image 2 提示词全集）
- Collection ID: mooe2nup0khf7ahkoa7e（GPT Image 2 提示词）
- Prompt Library Collection ID: moljqpf9qrxzyuhobqa
- Notion 页面 ID: 3541b1d7-1d88-816a-afbc-ffee788d83bf（GPT-image-2 提示词宝库）
