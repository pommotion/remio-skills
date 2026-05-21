#!/usr/bin/env python3
"""
gcli2api 图像生成脚本 — 使用群晖 NAS 上的 Antigravity gemini-3.1-flash-image 模型
用于 ai-music-producer 封面生成（免费，基于 Google OAuth 凭证池）

用法:
  python gcli-cover-gen.py --prompt "极简封面..." --output ~/Desktop/📂 音乐/歌名/cover_歌名.png [--aspect 1:1]
"""

import argparse, base64, json, os, sys, time, urllib.request, urllib.error


def generate_image(prompt, output_path, aspect="1:1",
                   model="gemini-3.1-flash-image",
                   api_url="http://${GCLI2API_HOST}:7861",
                   api_key="violin"):
    """调用 gcli2api Antigravity 端点生成图片"""
    aspect_map = {"1:1":"", "16:9":"-16x9", "9:16":"-9x16", "4:3":"-4x3", "3:4":"-3x4", "21:9":"-21x9"}
    suffix = aspect_map.get(aspect, "")
    full_model = f"{model}{suffix}"
    endpoint = f"{api_url}/antigravity/v1/models/{full_model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    print(f"🎨 gcli2api 图像生成 | 模型: {full_model} | 提示词: {prompt[:60]}...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            start = time.time()
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            print(f"   ⏱ {time.time()-start:.1f}s")
            if "candidates" not in result:
                return {"ok": False, "error": f"无 candidates"}
            parts = result["candidates"][0].get("content", {}).get("parts", [])
            for p in parts:
                if "inlineData" in p:
                    img_data = base64.b64decode(p["inlineData"]["data"])
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    size_kb = len(img_data) / 1024
                    print(f"   ✅ {output_path} ({size_kb:.0f} KB)")
                    return {"ok": True, "path": output_path, "size_kb": size_kb, "model": full_model}
            return {"ok": False, "error": "API 未返回图片数据"}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            print(f"   ⚠️ HTTP {e.code}: {body}")
            if e.code in (429, 500, 502, 503) and attempt < max_retries - 1:
                time.sleep((attempt+1)*15); continue
            return {"ok": False, "error": f"HTTP {e.code}: {body}"}
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep((attempt+1)*10); continue
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "达到最大重试次数"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--aspect", default="1:1")
    parser.add_argument("--model", default="gemini-3.1-flash-image")
    parser.add_argument("--api-url", default="http://${GCLI2API_HOST}:7861")
    parser.add_argument("--api-key", default="violin")
    args = parser.parse_args()
    result = generate_image(args.prompt, args.output, args.aspect, args.model, args.api_url, args.api_key)
    if not result["ok"]:
        print(f"❌ {result['error']}"); sys.exit(1)
