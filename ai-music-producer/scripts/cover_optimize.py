#!/usr/bin/env python3
"""
cover_optimize.py — 封面优化器（A/B 对比 + 多模型 fallback）

策略：
1. 一次生成 2 个候选（不同 prompt 变体）
2. 用 PIL 提取主色调，做视觉验证
3. 自动选择得分最高的保存
4. Fallback 链：bizyair (ModelZoo o2-t2i) → gcli2api → mmx image

⚠️ bizyair 调用走 cli.py modelzoo-run 子进程（ModelZoo 异步 API）：
   POST /x/v1/modelzoo/tasks/openapi/bza-image-o2-base/text-to-image
   GET  /x/v1/modelzoo/tasks/openapi/{request_id}
   不是旧版 /w/v1/webapp/task/openapi/create（已废弃，bozo-aigc 同步模式会重复提交）。

Usage:
    # 单首歌（自动选最优）
    python cover_optimize.py --title "六月之后" --prompt "..." --output "~/Desktop/📂 音乐/六月之后/cover_六月之后.png"

    # 批量（从 vault songs.json 读取待生成列表）
    python cover_optimize.py --batch

    # 只用 gcli2api（bizyair 失败时）
    python cover_optimize.py --title "..." --prompt "..." --provider gcli2api

    # 自定义候选数
    python cover_optimize.py --title "..." --prompt "..." --candidates 3

依赖：bizyair-skill, gcli2api, mmx（任一可用）
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("❌ PIL/numpy 未安装：pip install Pillow numpy")
    sys.exit(1)


# ─── Prompt 变体生成 ──────────────────────────────────────────────────────────

def make_variants(base_prompt: str, n: int = 2) -> list:
    """
    生成 N 个 prompt 变体。
    - Variant 1: base（基础）
    - Variant 2: 加色相偏移描述
    - Variant 3: 加材质细节
    """
    variants = [base_prompt]

    if n >= 2:
        # 冷色调变体
        v2 = base_prompt + " 偏冷色调，蓝色调主导，避免暖色"
        variants.append(v2)

    if n >= 3:
        # 暖色调变体
        v3 = base_prompt + " 偏暖色调，红色调和金黄色主导，增加温暖感"
        variants.append(v3)

    if n >= 4:
        # 高对比变体
        v4 = base_prompt + " 高对比度，深黑背景与亮色主体形成强烈反差"
        variants.append(v4)

    return variants[:n]


# ─── 视觉评分 ────────────────────────────────────────────────────────────────

def score_cover(image_path: str) -> dict:
    """
    对封面做自动视觉评分（0-100）。
    维度：
    - 色彩丰富度（HSV 空间标准差）
    - 对比度（亮度极差）
    - 视觉聚焦度（中心区域 vs 边缘区域的对比）
    - 文件大小合理性（避免白底/单色）
    """
    try:
        img = Image.open(image_path).convert('RGB')
    except Exception as e:
        return {'score': 0, 'error': str(e)}

    arr = np.array(img)

    # 1. 色彩丰富度
    h, w, _ = arr.shape
    center = arr[h//4:3*h//4, w//4:3*w//4]
    edge_h = 20
    edge_top = arr[:edge_h, :, :]
    edge_bottom = arr[-edge_h:, :, :]
    edge_left = arr[:, :edge_h, :]
    edge_right = arr[:, -edge_h:, :]
    edge = np.concatenate([edge_top.flatten(), edge_bottom.flatten(),
                           edge_left.flatten(), edge_right.flatten()])
    edge = edge.reshape(-1, 3)

    # 中心 vs 边缘的差异
    center_mean = center.mean(axis=(0, 1))
    edge_mean = edge.mean(axis=0)
    center_edge_diff = np.abs(center_mean - edge_mean).mean()
    focus_score = min(100, center_edge_diff * 2)

    # 2. 对比度（亮度极差）
    gray = arr.mean(axis=2)
    contrast = gray.max() - gray.min()
    contrast_score = min(100, contrast / 1.5)

    # 3. 色彩多样性（RGB 通道标准差）
    color_std = arr.std(axis=(0, 1)).mean()
    color_score = min(100, color_std / 2)

    # 4. 文件大小检查（避免白底小文件）
    file_size_kb = os.path.getsize(image_path) / 1024
    if file_size_kb < 50:
        size_score = 20
        size_penalty = "文件过小（<50KB）可能为白底"
    elif file_size_kb > 5000:
        size_score = 60
        size_penalty = "文件过大（>5MB）"
    else:
        size_score = 100
        size_penalty = ""

    # 加权综合
    weights = {'focus': 0.3, 'contrast': 0.25, 'color': 0.3, 'size': 0.15}
    overall = (
        focus_score * weights['focus'] +
        contrast_score * weights['contrast'] +
        color_score * weights['color'] +
        size_score * weights['size']
    )

    return {
        'score': round(overall, 1),
        'focus_score': round(focus_score, 1),
        'contrast_score': round(contrast_score, 1),
        'color_score': round(color_score, 1),
        'size_score': size_score,
        'file_size_kb': round(file_size_kb, 1),
        'size_penalty': size_penalty,
    }


# ─── 提供方调用 ──────────────────────────────────────────────────────────────

def call_bizyair(prompt: str, output_path: str) -> bool:
    """调用 bizyair-skill GPT Image 2 (ModelZoo o2-t2i，异步轮询）。

    正确调用方式：通过 bizyair-skill CLI 的 modelzoo-run 子命令调
    /x/v1/modelzoo/tasks/openapi/bza-image-o2-base/text-to-image，
    始终异步（不会同步超时重复提交）。
    """
    import subprocess

    # 读取 BIZYAIR_API_KEY
    api_key = os.environ.get("BIZYAIR_API_KEY", "")
    if not api_key:
        r = subprocess.run(
            ["bash", "-lc", "grep BIZYAIR_API_KEY ~/.zshrc | head -1 | sed 's/.*=//'"],
            capture_output=True, text=True,
        )
        api_key = r.stdout.strip().strip("'\"")

    if not api_key:
        print("   ⚠️  BIZYAIR_API_KEY 未设置")
        return False

    BIZYAIR_SKILL_DIR = Path.home() / "Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/remio/skills/bizyair-skill"
    BIZYAIR_CLI = BIZYAIR_SKILL_DIR / "scripts" / "cli.py"
    BIZYAIR_ENDPOINT = "bza-image-o2-base/text-to-image"

    cmd = [
        sys.executable, str(BIZYAIR_CLI),
        "modelzoo-run", BIZYAIR_ENDPOINT,
        "--param", f"prompt={prompt}",
        "--param", "aspect_ratio=1:1",
        "--param", "resolution=2K",
        "--api-key", api_key,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            cwd=str(BIZYAIR_SKILL_DIR),
        )

        # 解析输出：找 bizyair 生成的图片 URL
        img_url = None
        for line in result.stdout.split("\n"):
            line = line.strip()
            if "bizyair" in line and "http" in line:
                # 提取 URL
                for part in line.split():
                    if part.startswith("http"):
                        img_url = part
                        break
            elif line.startswith("http") and ("image" in line or "s3" in line or "aliyuncs" in line):
                img_url = line

        if img_url:
            import urllib.request
            urllib.request.urlretrieve(img_url, output_path)
            return True

        print(f"   ⚠️  bizyair 未返回图片 URL: {result.stdout[-200:]}")
        return False
    except Exception as e:
        print(f"   ⚠️  bizyair 失败：{e}")
    return False


def call_gcli2api(prompt: str, output_path: str) -> bool:
    """调用 gcli2api gemini-3.1-flash-image."""
    try:
        # gcli-cover-gen.py 已存在，复用
        from gcli_cover_gen import generate as gcli_generate

        # gcli-cover-gen 接受 prompt + output
        if gcli_generate(prompt=prompt, output_path=output_path):
            return True
    except Exception as e:
        print(f"   ⚠️  gcli2api 失败：{e}")
    return False


def call_mmx(prompt: str, output_path: str) -> bool:
    """调用 mmx image（最后兜底）。"""
    try:
        import subprocess
        result = subprocess.run(
            ["mmx", "image", "generate", "--prompt", prompt, "--output", output_path, "--ratio", "1:1"],
            capture_output=True, timeout=180, text=True
        )
        return result.returncode == 0 and os.path.isfile(output_path)
    except Exception as e:
        print(f"   ⚠️  mmx 失败：{e}")
    return False


PROVIDERS = ['bizyair', 'gcli2api', 'mmx']


def generate_with_fallback(prompt: str, output_path: str, provider: str = 'auto') -> str:
    """
    多 provider fallback 生成封面。
    返回实际成功的 provider 名称。
    """
    if provider == 'auto':
        providers = PROVIDERS
    else:
        providers = [provider]

    for p in providers:
        print(f"   🔄 尝试 {p}...")
        start = time.time()
        success = False
        if p == 'bizyair':
            success = call_bizyair(prompt, output_path)
        elif p == 'gcli2api':
            success = call_gcli2api(prompt, output_path)
        elif p == 'mmx':
            success = call_mmx(prompt, output_path)

        elapsed = time.time() - start
        if success and os.path.isfile(output_path):
            print(f"   ✅ {p} 成功 ({elapsed:.1f}s)")
            return p
        else:
            print(f"   ❌ {p} 失败 ({elapsed:.1f}s)")

    return ''


# ─── 单首歌 A/B 对比 ─────────────────────────────────────────────────────────

def optimize_cover(title: str, prompt: str, output_path: str, candidates: int = 2, provider: str = 'auto') -> dict:
    """
    为一首歌生成多个候选封面，自动选最优。
    """
    output_path = os.path.expanduser(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"\n🎨 优化封面：{title}")
    print(f"   输出：{output_path}")
    print(f"   候选数：{candidates}")

    variants = make_variants(prompt, candidates)
    candidates_data = []

    for i, variant_prompt in enumerate(variants, 1):
        candidate_path = output_path.replace('.png', f'_c{i}.png')
        print(f"\n   候选 {i}/{candidates}：{variant_prompt[:80]}...")

        provider_used = generate_with_fallback(variant_prompt, candidate_path, provider)
        if not provider_used:
            continue

        score = score_cover(candidate_path)
        print(f"   📊 评分：{score['score']}/100 "
              f"(focus={score.get('focus_score', 0)}, "
              f"contrast={score.get('contrast_score', 0)}, "
              f"color={score.get('color_score', 0)}, "
              f"size={score.get('size_score', 0)})")
        if score.get('size_penalty'):
            print(f"   ⚠️  {score['size_penalty']}")

        candidates_data.append({
            'candidate': i,
            'prompt': variant_prompt,
            'path': candidate_path,
            'provider': provider_used,
            'score': score,
        })

    if not candidates_data:
        return {'success': False, 'error': '所有候选都生成失败'}

    # 选最高分
    best = max(candidates_data, key=lambda c: c['score']['score'])
    print(f"\n   🏆 最佳候选：{best['candidate']}（{best['score']['score']}/100, {best['provider']}）")

    # 移动到目标位置
    import shutil
    shutil.move(best['path'], output_path)
    print(f"   ✅ 已保存最佳版本：{output_path}")

    # 清理其他候选
    for c in candidates_data:
        if c['path'] != output_path and os.path.isfile(c['path']):
            os.remove(c['path'])

    return {
        'success': True,
        'best_candidate': best,
        'all_candidates': candidates_data,
    }


# ─── 批量模式 ───────────────────────────────────────────────────────────────

def batch_optimize(music_dir: str, songs_json_path: str, force: bool = False) -> dict:
    """
    扫描 songs.json，对没有封面的歌曲自动生成。
    用 cover_prompt.py 作为 prompt 模板。
    """
    music_dir = Path(music_dir).expanduser()
    songs_json = Path(songs_json_path)

    if not songs_json.exists():
        print(f"❌ 找不到 songs.json：{songs_json}")
        return {}

    with open(songs_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 加载 cover_prompt 模块
    try:
        import importlib.util
        cp_spec = importlib.util.spec_from_file_location(
            "cover_prompt",
            Path(__file__).parent / "cover_prompt_vault.py"
        )
        cp = importlib.util.module_from_spec(cp_spec)
        cp_spec.loader.exec_module(cp)
    except Exception as e:
        print(f"❌ 加载 cover_prompt_vault 失败：{e}")
        return {}

    results = {}
    failed = []

    for song in data.get('songs', []):
        title = song.get('title', '')
        if not title or song.get('exclude'):
            continue

        song_dir = Path(song.get('dir', '') or music_dir / title)
        cover_path = song_dir / f"cover_{title}.png"

        if cover_path.exists() and not force:
            print(f"⏭️  [{title}] 封面已存在")
            continue

        # 生成 prompt
        try:
            prompt = cp.build_prompt(
                title=title,
                emotion=song.get('emotion', ''),
                genre=song.get('genre', ''),
            )
        except Exception as e:
            print(f"❌ [{title}] prompt 构建失败：{e}")
            continue

        print(f"\n🎨 [{title}]")
        result = optimize_cover(
            title=title,
            prompt=prompt,
            output_path=str(cover_path),
        )

        if result.get('success'):
            results[title] = result
        else:
            failed.append(title)

    print(f"\n{'='*60}")
    print(f"✅ 完成：{len(results)} 张")
    if failed:
        print(f"❌ 失败：{len(failed)}")
        for f in failed[:10]:
            print(f"   - {f}")

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="封面优化器（A/B 对比 + fallback）")
    parser.add_argument('--title', help='歌曲标题')
    parser.add_argument('--prompt', help='封面 prompt 字符串')
    parser.add_argument('--output', help='输出路径')
    parser.add_argument('--candidates', type=int, default=2, help='候选数（默认 2）')
    parser.add_argument('--provider', default='auto', choices=['auto', 'bizyair', 'gcli2api', 'mmx'])
    parser.add_argument('--batch', action='store_true', help='批量模式（从 songs.json 读取）')
    parser.add_argument('--music-dir', default='~/Desktop/📂 音乐')
    parser.add_argument('--songs-json', help='songs.json 路径（批量模式）')
    parser.add_argument('--force', action='store_true', help='强制重新生成')

    args = parser.parse_args()

    if args.batch:
        songs_json = args.songs_json or str(
            Path.home() / "Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault/data/songs.json"
        )
        batch_optimize(args.music_dir, songs_json, force=args.force)
    elif args.title and args.prompt and args.output:
        optimize_cover(
            title=args.title,
            prompt=args.prompt,
            output_path=args.output,
            candidates=args.candidates,
            provider=args.provider,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
