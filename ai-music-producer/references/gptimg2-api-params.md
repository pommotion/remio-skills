# GPT Image 2 API 参数参考

## 版本 A: gcli2api (Nano Banana 2 / gemini-3.1-flash-image)

- API: POST http://${GCLI2API_HOST}:7861/antigravity/v1/models/gemini-3.1-flash-image:generateContent
- Headers: {"x-goog-api-key": "violin", "Content-Type": "application/json"}
- Body: {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
- 返回 candidates[0].content.parts 中 inlineData.data 是 base64 图片
- 耗时约 15-25s，免费

## 版本 B: BizyAir GPT_IMAGE_2 (原生 GPT Image 2)

- API: POST https://api.bizyair.cn/w/v1/webapp/task/openapi/create
- ⚠️ **必须设置代理**: `os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"`
- Headers: {"Content-Type": "application/json", "Authorization": "Bearer sk-hpncrzwkqyghhzqxpvpawdorfszsykrbbquioohhrloaovzi"}
- Body: {"web_app_id": 52416, "suppress_preview_output": false, "input_values": {"4:BizyAir_GPT_IMAGE_2_T2I_API.prompt": prompt, "4:BizyAir_GPT_IMAGE_2_T2I_API.aspect_ratio": "16:9"}}
- 返回 status=="Success" 后从 outputs[0].object_url 下载图片
- 耗时约 90-180s，API 付费

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
