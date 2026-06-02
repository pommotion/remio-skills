#!/usr/bin/env python3
"""
beatprint_gen.py — BeatPrints 海报生成器

从歌曲封面生成 9:16 竖版海报（2280×3480），用于：
- 音乐网站展示
- 短视频封面
- 社交媒体推广

设计：
- 顶部：居中封面图（带 10px 白色描边框）
- 底部：标题（120pt）+ 流派/时长/情绪（48pt）
- 背景：封面图的高斯模糊 + 60% 黑色叠加
- 底部渐变：黑色从 200 alpha 渐变到 0

Usage:
    # 单首歌
    python beatprint_gen.py --cover ~/Desktop/📂\ 音乐/六月之后/cover_六月之后.png --title "六月之后" --genre "Pop Rock" --duration 192 --emotion "倔强"

    # 批量（扫描 music-vault 的 songs.json）
    python beatprint_gen.py --from-vault /Users/.../music-vault

    # 自定义输出
    python beatprint_gen.py --cover /path/cover.png --title "歌名" --output /path/poster.png

依赖：pip install Pillow
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
except ImportError:
    print("❌ Pillow 未安装：pip install Pillow")
    sys.exit(1)


# ─── Config ───────────────────────────────────────────────────────────────────

POSTER_W, POSTER_H = 2280, 3480
COVER_TARGET = 1920  # 居中封面大小
BORDER_PAD = 10
TOP_OFFSET = 280
GRADIENT_H = 600
TEXT_OFFSET_FROM_BOTTOM = 520

# 字体路径优先级
FONT_PATHS = [
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
    '/Library/Fonts/Arial Unicode.ttf',
    '/System/Library/Fonts/Supplemental/Songti.ttc',
    '/System/Library/Fonts/Supplemental/STHeiti Medium.ttc',
]


# ─── Font Loading ─────────────────────────────────────────────────────────────

_font_cache = {}

def load_font(size: int):
    """加载 macOS 系统字体（带缓存）。"""
    if size in _font_cache:
        return _font_cache[size]
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            try:
                f = ImageFont.truetype(fp, size)
                _font_cache[size] = f
                return f
            except Exception:
                continue
    f = ImageFont.load_default()
    _font_cache[size] = f
    return f


# ─── 核心生成 ────────────────────────────────────────────────────────────────

def format_duration(seconds: int) -> str:
    """秒数 → m:ss"""
    if not seconds:
        return ""
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def generate_poster(
    cover_path: str,
    title: str,
    genre: str = "",
    emotion: str = "",
    duration_sec: int = 0,
    output_path: str = "",
) -> str:
    """
    从封面生成竖版海报。
    返回输出路径。
    """
    if not os.path.isfile(cover_path):
        raise FileNotFoundError(f"封面不存在：{cover_path}")

    if not output_path:
        # 默认与 cover 同目录，文件名 + _poster
        cover_dir = os.path.dirname(cover_path)
        cover_stem = Path(cover_path).stem.replace('cover_', '').replace('cover.', '')
        output_path = os.path.join(cover_dir, f"{cover_stem}_poster.png")

    print(f"🎨 生成 BeatPrints 海报：{Path(cover_path).name} → {Path(output_path).name}")

    # EPERM 防护：emoji 路径（📂）在 bash 沙盒会触发 EPERM
    # 先写到 /tmp，再 shutil.move 到目标
    import tempfile
    import shutil
    staging_path = None
    try:
        # 试探性写入目标
        test_path = output_path + '.write_test'
        with open(test_path, 'w') as f:
            f.write('test')
        os.remove(test_path)
    except (PermissionError, OSError):
        # 目标不可写，写到 /tmp
        staging_path = os.path.join(
            tempfile.gettempdir(),
            f"poster_{Path(cover_path).stem}_{int(time.time())}.png"
        )
        print(f"   ⚠️  目标不可写（emoji 路径沙盒限制），staging：{staging_path}")
        output_path = staging_path

    # 1. 加载封面
    cover = Image.open(cover_path).convert('RGBA')

    # 2. 高斯模糊背景
    bg = cover.resize((POSTER_W, POSTER_H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=40))
    dark = Image.new('RGBA', (POSTER_W, POSTER_H), (0, 0, 0, 160))
    bg = Image.alpha_composite(bg, dark)

    # 3. 居中封面 + 描边
    cover_resized = cover.resize((COVER_TARGET, COVER_TARGET), Image.LANCZOS)
    frame_size = COVER_TARGET + BORDER_PAD * 2
    frame = Image.new('RGBA', (frame_size, frame_size), (255, 255, 255, 60))
    frame_draw = ImageDraw.Draw(frame)
    frame_draw.rounded_rectangle(
        [2, 2, frame_size - 3, frame_size - 3],
        radius=16,
        outline=(255, 255, 255, 100),
        width=2
    )
    frame.paste(cover_resized, (BORDER_PAD, BORDER_PAD), cover_resized)
    cover_x = (POSTER_W - frame_size) // 2
    bg.paste(frame, (cover_x, TOP_OFFSET), frame)

    # 4. 底部渐变
    gradient = Image.new('RGBA', (POSTER_W, POSTER_H), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient)
    grad_y_start = POSTER_H - GRADIENT_H
    for y in range(GRADIENT_H):
        alpha = int(200 * (y / GRADIENT_H) ** 1.5)
        grad_draw.line(
            [(0, grad_y_start + y), (POSTER_W, grad_y_start + y)],
            fill=(0, 0, 0, alpha)
        )
    bg = Image.alpha_composite(bg, gradient)

    # 5. 文字
    draw = ImageDraw.Draw(bg)
    font_large = load_font(120)
    font_small = load_font(48)

    text_y = POSTER_H - TEXT_OFFSET_FROM_BOTTOM

    if title:
        bbox = draw.textbbox((0, 0), title, font=font_large)
        tw = bbox[2] - bbox[0]
        tx = (POSTER_W - tw) // 2
        # 阴影
        draw.text((tx + 4, text_y + 4), title, fill=(0, 0, 0, 200), font=font_large)
        # 主体
        draw.text((tx, text_y), title, fill=(255, 255, 255, 240), font=font_large)

    # 信息行
    info_parts = []
    if duration_sec:
        info_parts.append(format_duration(duration_sec))
    if genre:
        info_parts.append(genre)
    if emotion:
        info_parts.append(emotion)

    if info_parts:
        info_text = '  ·  '.join(info_parts)
        bbox2 = draw.textbbox((0, 0), info_text, font=font_small)
        tw2 = bbox2[2] - bbox2[0]
        tx2 = (POSTER_W - tw2) // 2
        info_y = text_y + 160
        draw.text((tx2, info_y), info_text, fill=(255, 255, 255, 160), font=font_small)

    # 6. 保存
    bg.convert('RGB').save(output_path, 'PNG', optimize=True)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"   ✅ 海报已生成：{output_path} ({size_kb} KB, {POSTER_W}×{POSTER_H})")

    # 如果用了 staging，提示用户手动移动
    if staging_path:
        print(f"   📦 staging 路径，需手动移动：")
        print(f"      mv '{staging_path}' '<目标目录>/'")

    return output_path


# ─── Vault 批量模式 ──────────────────────────────────────────────────────────

def find_cover_in_song_dir(song_dir: str) -> Optional[str]:
    """在歌曲目录中查找封面。优先级：cover_{歌名}.* > {歌名}_cover.* > 任意 cover*"""
    d = Path(song_dir)
    name = d.name

    # 优先级 1: cover_歌名.*
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        candidate = d / f"cover_{name}{ext}"
        if candidate.exists():
            return str(candidate)

    # 优先级 2: 歌名_cover.*
    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        candidate = d / f"{name}_cover{ext}"
        if candidate.exists():
            return str(candidate)

    # 优先级 3: 任意 cover*
    for f in d.iterdir():
        if f.is_file() and f.name.lower().startswith('cover') and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            return str(f)

    return None


def batch_from_vault(vault_dir: str, music_dir: str, force: bool = False) -> dict:
    """
    从 music-vault 扫描所有歌曲，批量生成海报。
    跳过已有 _poster.png 的歌曲（增量模式）。
    """
    vault_dir = Path(vault_dir)
    music_dir = Path(music_dir).expanduser()
    songs_json = vault_dir / "data" / "songs.json"

    if not songs_json.exists():
        print(f"❌ 找不到 songs.json：{songs_json}")
        return {}

    with open(songs_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    songs = data.get('songs', [])
    print(f"📚 songs.json 共 {len(songs)} 首歌")

    results = {}
    skipped = 0
    failed = []

    for song in songs:
        slug = song.get('slug', '')
        title = song.get('title', '')
        song_dir = song.get('dir', '') or str(music_dir / title)
        cover = song.get('cover', {}).get('path', '') if song.get('cover') else ''

        # 优先用 songs.json 的 cover 字段，没有再扫描目录
        if not cover or not os.path.isfile(cover):
            cover = find_cover_in_song_dir(song_dir)

        if not cover or not os.path.isfile(cover):
            print(f"⏭️  [{title}] 无封面，跳过")
            continue

        # 跳过已存在
        poster_path = os.path.join(song_dir, f"{title}_poster.png")
        if os.path.isfile(poster_path) and not force:
            print(f"⏭️  [{title}] 海报已存在")
            skipped += 1
            continue

        # 提取元数据
        genre = song.get('genre', '')
        emotion = song.get('emotion', '')
        duration = song.get('duration', 0)

        try:
            generate_poster(
                cover_path=cover,
                title=title,
                genre=genre,
                emotion=emotion,
                duration_sec=duration,
                output_path=poster_path,
            )
            results[title] = poster_path
        except Exception as e:
            print(f"   ❌ [{title}] 失败：{e}")
            failed.append(title)

    print(f"\n{'='*60}")
    print(f"✅ 生成：{len(results)} 张")
    print(f"⏭️  跳过：{skipped} 张（已存在）")
    if failed:
        print(f"❌ 失败：{len(failed)}")
        for f in failed[:10]:
            print(f"   - {f}")

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BeatPrints 竖版海报生成器")
    parser.add_argument('--cover', help='封面图片路径')
    parser.add_argument('--title', help='歌曲标题')
    parser.add_argument('--genre', default='', help='流派标签')
    parser.add_argument('--emotion', default='', help='情感标签')
    parser.add_argument('--duration', type=int, default=0, help='时长（秒）')
    parser.add_argument('--output', help='输出路径（默认：{歌名}_poster.png）')
    parser.add_argument('--from-vault', help='从 music-vault 批量生成海报（指定 vault 目录）')
    parser.add_argument('--music-dir', default='~/Desktop/📂 音乐', help='音乐根目录（批量模式）')
    parser.add_argument('--force', action='store_true', help='强制覆盖已有海报')

    args = parser.parse_args()

    if args.from_vault:
        batch_from_vault(args.from_vault, args.music_dir, force=args.force)
    elif args.cover and args.title:
        generate_poster(
            cover_path=args.cover,
            title=args.title,
            genre=args.genre,
            emotion=args.emotion,
            duration_sec=args.duration,
            output_path=args.output,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
