#!/usr/bin/env python3
"""
beatprint_gen.py — BeatPrints 海报生成器（Wrapper）

⚠️ v2.0: 本脚本是 BeatPrints 项目的 wrapper，不再用 Pillow 手搓。
内部调用真正的 BeatPrints 库（BeatPrints.poster.Poster）生成专业海报。

如果 BeatPrints 不可用，会报错退出（不再 fallback 到 Pillow 假海报）。

Usage:
    # 单首歌
    python beatprint_gen.py --cover ~/path/cover.png --title "歌名" --genre "Pop" --duration 192 --emotion "倔强" --lyrics "歌词第1行\\n歌词第2行\\n歌词第3行\\n歌词第4行"

    # 批量（扫描 music-vault 的 songs.json）
    python beatprint_gen.py --from-vault /Users/.../music-vault

    # 自定义输出
    python beatprint_gen.py --cover /path/cover.png --title "歌名" --output /path/poster.png
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ─── BeatPrints 路径 ─────────────────────────────────────────────────────────

BP_DIR = Path("/Users/wanglingwei/Movies/Github_Projects/BeatPrints/BeatPrints")
BP_PYTHON = BP_DIR / ".venv/bin/python3.13"
BP_SCRIPT = BP_DIR / "generate_poster.py"


def call_beatprints(
    name: str,
    artist: str = "王同学",
    lyrics: str = "",
    album: str = "",
    released: str = "2026",
    duration: str = "",
    label: str = "AI Original",
    theme: str = "Dark",
    accent: bool = True,
    cover_path: str = "",
    output_dir: str = "",
) -> str:
    """
    调用 BeatPrints generate_poster.py 生成海报。
    返回输出文件路径。
    """
    if not BP_PYTHON.exists():
        print(f"❌ BeatPrints Python 不存在：{BP_PYTHON}")
        print(f"   请确认 BeatPrints 项目已安装在 {BP_DIR}")
        sys.exit(1)

    if not BP_SCRIPT.exists():
        print(f"❌ BeatPrints generate_poster.py 不存在：{BP_SCRIPT}")
        sys.exit(1)

    cmd = [
        str(BP_PYTHON),
        str(BP_SCRIPT),
        "--name", name,
        "--artist", artist,
        "--lyrics", lyrics,
        "--album", album or name,
        "--released", released,
        "--duration", duration,
        "--label", label,
        "--theme", theme,
        "--cover-path", cover_path,
        "--output", output_dir,
    ]
    if accent:
        cmd.append("--accent")

    print(f"🎨 BeatPrints 生成海报：{name}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"   ❌ BeatPrints 错误：{result.stderr[-500:]}")
        return ""

    # 从 stdout 找输出路径
    output = result.stdout.strip()
    if output:
        print(f"   ✅ {output}")

    return output


# ─── Vault 批量模式 ──────────────────────────────────────────────────────────

def find_cover_in_song_dir(song_dir: str) -> Optional[str]:
    """在歌曲目录中查找封面。"""
    d = Path(song_dir)
    name = d.name

    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        candidate = d / f"cover_{name}{ext}"
        if candidate.exists():
            return str(candidate)

    for ext in ['.png', '.jpg', '.jpeg', '.webp']:
        candidate = d / f"{name}_cover{ext}"
        if candidate.exists():
            return str(candidate)

    for f in d.iterdir():
        if f.is_file() and f.name.lower().startswith('cover') and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            return str(f)

    return None


def find_lyrics_file(song_dir: str) -> Optional[str]:
    """在歌曲目录中查找歌词文件。"""
    d = Path(song_dir)
    for f in sorted(d.iterdir()):
        if 'lyrics' in f.name.lower() and f.suffix == '.txt':
            return str(f)
    for f in sorted(d.iterdir()):
        if f.suffix == '.txt' and not f.name.startswith('.'):
            return str(f)
    return None


def extract_best_4_lines(lyrics_path: str) -> str:
    """从歌词文件中提取最有画面感的 4 行。"""
    try:
        with open(lyrics_path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
    except Exception:
        return ""

    # 过滤掉段落标记和太短的行
    content_lines = [
        l for l in lines
        if not re.match(r'^\[.+\]$', l) and len(l) >= 4
    ]

    if len(content_lines) <= 4:
        return "\\n".join(content_lines)

    # 简单启发式：选长度适中、有画面感的行
    # 优先选前 1/3 和中间偏后的行（通常是主歌+副歌）
    total = len(content_lines)
    candidates = content_lines[:total//3] + content_lines[total//2:total//2+total//4]
    if len(candidates) >= 4:
        # 均匀取 4 行
        step = len(candidates) // 4
        selected = [candidates[i * step] for i in range(4)]
    else:
        selected = content_lines[:4]

    return "\\n".join(selected)


def format_duration(seconds: int) -> str:
    """秒数 → M:SS"""
    if not seconds:
        return ""
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def batch_from_vault(vault_dir: str, music_dir: str, force: bool = False) -> dict:
    """
    从 music-vault 扫描所有歌曲，批量生成海报。
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

        if not os.path.isdir(song_dir):
            continue

        # 查封面
        cover = song.get('cover', {}).get('path', '') if song.get('cover') else ''
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

        # 提取歌词 4 行
        lyrics_path = find_lyrics_file(song_dir)
        lyrics_4 = extract_best_4_lines(lyrics_path) if lyrics_path else title

        # 时长
        duration = format_duration(song.get('duration', 0))

        # 调用 BeatPrints
        try:
            call_beatprints(
                name=title,
                lyrics=lyrics_4,
                duration=duration,
                cover_path=cover,
                output_dir=song_dir,
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
    parser = argparse.ArgumentParser(description="BeatPrints 海报生成器（Wrapper）")
    parser.add_argument('--cover', help='封面图片路径')
    parser.add_argument('--title', help='歌曲标题')
    parser.add_argument('--genre', default='', help='流派标签（已忽略，BeatPrints 自动处理）')
    parser.add_argument('--emotion', default='', help='情感标签（已忽略）')
    parser.add_argument('--duration', type=int, default=0, help='时长（秒）')
    parser.add_argument('--lyrics', default='', help='4 行歌词（用 \\n 拼接）')
    parser.add_argument('--output', help='输出目录（默认：封面同目录）')
    parser.add_argument('--from-vault', help='从 music-vault 批量生成海报')
    parser.add_argument('--music-dir', default='~/Desktop/📂 音乐', help='音乐根目录')
    parser.add_argument('--force', action='store_true', help='强制覆盖已有海报')

    args = parser.parse_args()

    if args.from_vault:
        batch_from_vault(args.from_vault, args.music_dir, force=args.force)
    elif args.cover and args.title:
        output_dir = args.output or os.path.dirname(args.cover)
        call_beatprints(
            name=args.title,
            lyrics=args.lyrics or args.title,
            duration=format_duration(args.duration),
            cover_path=args.cover,
            output_dir=output_dir,
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
