#!/usr/bin/env python3
"""Notion 同步代码 — 被 GPT Image 2 提示词任务 Phase 6 引用。
用法：作为 run_python 的内联代码执行，变量 new_prompts 需由调用方传入。
"""
import json, subprocess, os

NTN = os.path.expanduser("~/.local/bin/ntn")
PAGE_ID = "3541b1d7-1d88-816a-afbc-ffee788d83bf"

def ntn_api(path, method="GET", data=None):
    cmd = [NTN, "api", path, "-X", method]
    if data:
        cmd += ["-d", json.dumps(data, ensure_ascii=False)]
    env = os.environ.copy()
    env["NOTION_API_VERSION"] = "2022-06-28"
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    return json.loads(r.stdout) if r.returncode == 0 else None

def make_blocks(p):
    blocks = []
    heading = f"#{p['number']} {p['title']}"
    cat = p.get('category', '')
    ptype = p.get('type', '')
    if cat or ptype:
        heading += f"  ({' · '.join(filter(None, [cat, ptype]))})"
    blocks.append({"object": "block", "type": "heading_3",
        "heading_3": {"rich_text": [{"type": "text", "text": {"content": heading[:2000]}}]}})
    # Meta
    meta = []
    if p.get('date'): meta.append(f"📅 {p['date']}")
    if p.get('heat'): meta.append(f"🔥 {p['heat']}")
    if p.get('refDesc'): meta.append(p['refDesc'])
    if p.get('postUrl'): meta.append(f"[原帖]({p['postUrl']})")
    if meta:
        blocks.append({"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": ' | '.join(meta)[:2000]}}]}})
    if p.get('innovation'):
        blocks.append({"object": "block", "type": "quote",
            "quote": {"rich_text": [{"type": "text", "text": {"content": f"💡 {p['innovation']}"[:2000]}}]}})
    # Prompt text
    s = p.get('structure', {})
    text = s.get('full', '')
    if not text and s.get('broth'):
        parts = []
        if s.get('broth'): parts.append(f"【汤底】\n{s['broth']}")
        if s.get('spice'): parts.append(f"【佐料】\n{s['spice']}")
        if s.get('catalyst'): parts.append(f"【药引子】\n{s['catalyst']}")
        text = '\n\n'.join(parts)
    if text:
        for chunk in [text[i:i+2000] for i in range(0, len(text), 2000)]:
            blocks.append({"object": "block", "type": "code",
                "code": {"rich_text": [{"type": "text", "text": {"content": chunk}}], "language": "plain text"}})
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def sync_to_notion(new_prompts):
    """将新提示词同步到 Notion 页面。new_prompts 是列表，每个元素含:
    number, title, date, category, type, heat, refDesc, postUrl, innovation, structure 等
    """
    all_blocks = []
    for p in new_prompts:
        all_blocks.extend(make_blocks(p))

    for i in range(0, len(all_blocks), 100):
        batch = all_blocks[i:i+100]
        ntn_api(f"v1/blocks/{PAGE_ID}/children", method="PATCH", data={"children": batch})
        print(f"  ✅ Batch {i//100+1}: {len(batch)} blocks")

    print(f"✅ Notion 同步完成: {len(new_prompts)} 条新提示词 → {len(all_blocks)} blocks")

# 调用示例（由 agent 注入 new_prompts 变量后执行）：
# sync_to_notion(new_prompts)
