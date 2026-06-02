#!/usr/bin/env python3
"""
lrc_align.py — 歌词同步 LRC 对齐工具

使用 DashScope FunASR WebSocket API 做逐字时间戳对齐，输出：
1. 标准 LRC 文件（.lrc）单歌版本
2. data/lrc_data.json 全库索引（增量更新）

Usage:
    # 对齐单首歌（v1 版本）
    python lrc_align.py --song ~/Desktop/📂\ 音乐/六月之后 --version v1

    # 对齐所有版本
    python lrc_align.py --song ~/Desktop/📂\ 音乐/六月之后 --all-versions

    # 批量处理（增量，跳过已对齐）
    python lrc_align.py --batch

    # 强制重新对齐
    python lrc_align.py --song ~/Desktop/📂\ 音乐/六月之后 --version v1 --force

依赖：pip install websockets
环境变量：DASHSCOPE_API_KEY
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

# FunASR WebSocket
try:
    import websockets
except ImportError:
    websockets = None
    print("⚠️  websockets 未安装：pip install websockets")

# ─── Config ───────────────────────────────────────────────────────────────────

DASHSCOPE_WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-fe3ef14b490d44628698d98a1cdb6113")
FFMPEG = "/opt/homebrew/bin/ffmpeg"

# 歌词清洗
SECTION_PATTERN = re.compile(r'^\[.+\]$')
PUNCT_PATTERN = re.compile(r'[，。、！？；：""''…—·,.\-!?;:\'\"()\[\]{}\s♫🎵🎶🎼😔]')


# ─── FunASR 转写 ──────────────────────────────────────────────────────────────

async def transcribe_audio(mp3_path: str) -> list:
    """
    FunASR 转写音频 → 返回带逐字时间戳的句子列表。
    自动将 mp3 转 mono 16kHz wav（不落盘）。
    """
    if websockets is None:
        print("   ❌ websockets 未安装")
        return []

    if not os.path.isfile(mp3_path):
        print(f"   ❌ 音频文件不存在：{mp3_path}")
        return []

    # ffmpeg 转换 wav（不落盘）
    try:
        proc = subprocess.run(
            [FFMPEG, "-y", "-i", mp3_path, "-ac", "1", "-ar", "16000", "-f", "wav", "-"],
            capture_output=True, timeout=60
        )
        audio_data = proc.stdout
    except Exception as e:
        print(f"   ❌ ffmpeg 失败：{e}")
        return []

    if not audio_data:
        print(f"   ❌ 音频转码失败")
        return []

    task_id = str(uuid.uuid4())
    sentences = []
    total = len(audio_data)

    try:
        async with websockets.connect(
            DASHSCOPE_WS_URL,
            additional_headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
            max_size=None, ping_interval=30, ping_timeout=60,
        ) as ws:
            await ws.send(json.dumps({
                "header": {"task_id": task_id, "action": "run-task", "streaming": "duplex"},
                "payload": {
                    "task_group": "audio", "task": "asr", "function": "recognition",
                    "model": "fun-asr-realtime",
                    "parameters": {
                        "format": "wav", "sample_rate": 16000,
                        "language_hints": ["zh"],
                        "semantic_punctuation_enabled": True,
                        "heartbeat": True,
                    },
                    "input": {},
                }
            }))

            resp = await asyncio.wait_for(ws.recv(), timeout=30)
            msg = json.loads(resp)
            if msg.get("header", {}).get("event") != "task-started":
                print("   ❌ FunASR 任务未启动")
                return []

            async def send_audio():
                offset = 0
                while offset < total:
                    await ws.send(audio_data[offset:offset + 32000])
                    offset += 32000
                    await asyncio.sleep(0.05)
                await ws.send(json.dumps({
                    "header": {"task_id": task_id, "action": "finish-task"}, "payload": {},
                }))

            async def recv_results():
                while True:
                    resp = await asyncio.wait_for(ws.recv(), timeout=120)
                    msg = json.loads(resp)
                    event = msg.get("header", {}).get("event")
                    if event == "result-generated":
                        sentence = msg.get("payload", {}).get("output", {}).get("sentence", {})
                        if sentence.get("sentence_end") and not sentence.get("heartbeat"):
                            words = sentence.get("words", [])
                            sentences.append({
                                "text": sentence.get("text", ""),
                                "begin_ms": sentence.get("begin_time", 0),
                                "end_ms": sentence.get("end_time", 0),
                                "words": [
                                    {"text": w.get("text", ""), "begin_ms": w.get("begin_time", 0), "end_ms": w.get("end_time", 0)}
                                    for w in words
                                ],
                            })
                    elif event == "task-finished":
                        return
                    elif event == "task-failed":
                        print(f"   ❌ FunASR: {msg.get('header',{}).get('error_message','')}")
                        return

            await asyncio.gather(send_audio(), recv_results())

    except Exception as e:
        print(f"   ❌ WebSocket: {e}")

    return sentences


# ─── 逐字对齐 ────────────────────────────────────────────────────────────────

def normalize_for_match(text: str) -> str:
    """去除标点和空白。"""
    return PUNCT_PATTERN.sub('', text)


def build_char_timeline(asr_sentences: list) -> list:
    """将 ASR 句子展平为 [{char, time_s}, ...] 时间轴。"""
    timeline = []
    for sent in asr_sentences:
        for w in sent["words"]:
            char = w["text"].strip()
            if char and w["begin_ms"] > 0:
                timeline.append({
                    "char": char,
                    "time_s": w["begin_ms"] / 1000.0,
                })
    return timeline


def align_lyrics_word_level(lyrics_lines: list, asr_sentences: list) -> list:
    """
    逐字时间戳对齐 → LRC 条目列表。
    策略：滑动窗口 + SequenceMatcher 模糊匹配。
    """
    timeline = build_char_timeline(asr_sentences)
    if not timeline:
        return []

    asr_text = ''.join(c["char"] for c in timeline)
    asr_norm = normalize_for_match(asr_text)

    lrc_entries = []
    asr_search_start = 0

    for line in lyrics_lines:
        norm_line = normalize_for_match(line)

        # 段落标记 [Intro] [Verse] 等
        if SECTION_PATTERN.match(line):
            if asr_search_start < len(timeline):
                lrc_entries.append({
                    'time': round(timeline[asr_search_start]["time_s"], 2),
                    'text': line,
                })
            elif lrc_entries:
                lrc_entries.append({'time': lrc_entries[-1]['time'], 'text': line})
            else:
                lrc_entries.append({'time': 0.0, 'text': line})
            continue

        if not norm_line:
            continue

        # 在 ASR 文本中找最佳匹配位置
        best_pos = -1
        best_score = 0
        search_window = min(80, len(timeline) - asr_search_start)
        for offset in range(0, search_window):
            for length in range(min(len(norm_line), 12), max(2, len(norm_line) - 8), -1):
                subseq = norm_line[:length]
                # 在 asr_norm 中从当前位置开始找
                idx = asr_norm.find(subseq, asr_search_start)
                if idx < 0:
                    continue
                # 简单评分：子串长度 / (位置偏移)
                pos_penalty = 1.0 - (idx - asr_search_start) * 0.001
                score = length * pos_penalty
                if score > best_score:
                    best_score = score
                    best_pos = idx

        if best_pos >= 0:
            # 找到对应的时间戳
            lrc_time = timeline[best_pos]["time_s"] if best_pos < len(timeline) else (timeline[-1]["time_s"] if timeline else 0)
            lrc_entries.append({'time': round(lrc_time, 2), 'text': line})
            asr_search_start = best_pos + len(norm_line) // 2
        else:
            # 找不到匹配，用上一行时间
            if lrc_entries:
                lrc_entries.append({'time': lrc_entries[-1]['time'], 'text': line})
            else:
                lrc_entries.append({'time': 0.0, 'text': line})

    return lrc_entries


# ─── LRC 输出 ────────────────────────────────────────────────────────────────

def format_lrc_time(seconds: float) -> str:
    """[mm:ss.xx]"""
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"[{m:02d}:{s:05.2f}]"


def write_lrc_file(entries: list, output_path: str, metadata: dict = None) -> None:
    """写入标准 LRC 文件。"""
    header_lines = [
        "[ti:{}]".format(metadata.get('title', '')),
        "[ar:{}]".format(metadata.get('artist', 'Violin')),
        "[al:{}]".format(metadata.get('album', 'AI 原创歌曲 · 作品集')),
        "[by:{}]".format(metadata.get('generator', 'FunASR + lrc_align.py')),
    ]

    with open(output_path, 'w', encoding='utf-8') as f:
        for h in header_lines:
            f.write(h + '\n')
        for e in entries:
            f.write(f"{format_lrc_time(e['time'])}{e['text']}\n")

    size = os.path.getsize(output_path)
    print(f"   ✅ LRC 写入：{output_path} ({size} B, {len(entries)} 行)")


# ─── 单歌处理 ────────────────────────────────────────────────────────────────

def find_lyrics_file(song_dir: str) -> str:
    """查找歌词文件。优先级：_clean.txt > _lyrics.txt > *.txt"""
    d = Path(song_dir)
    candidates = []
    for f in sorted(d.iterdir()):
        name = f.name.lower()
        if not f.is_file() or not name.endswith('.txt'):
            continue
        if 'lyrics' in name and name.endswith('_clean.txt'):
            return str(f)
        if 'lyrics' in name:
            candidates.insert(0, str(f))
        elif not name.startswith('.'):
            candidates.append(str(f))
    return candidates[0] if candidates else ""


def find_mp3_for_version(song_dir: str, version: str) -> str:
    """查找指定版本的 mp3。"""
    d = Path(song_dir)
    matches = []
    for f in d.iterdir():
        name = f.name.lower()
        if not f.is_file() or not name.endswith('.mp3'):
            continue
        if f"_v{version[1:]}" in name or version in name:
            matches.append(str(f))
    return matches[0] if matches else ""


def find_all_mp3(song_dir: str) -> list:
    """查找所有 mp3。"""
    d = Path(song_dir)
    return sorted([str(f) for f in d.iterdir() if f.is_file() and f.name.lower().endswith('.mp3')])


def extract_version_tag(mp3_path: str) -> str:
    """从 mp3 文件名提取版本号。"""
    m = re.search(r'_v(\d+)', Path(mp3_path).stem)
    return f"v{m.group(1)}" if m else "v1"


def process_one(song_dir: str, version: str, output_lrc_path: str = "", force: bool = False) -> dict:
    """
    处理一首歌的某个版本。
    返回：{'time': 秒, 'entries': [...]}
    """
    song_dir = str(Path(song_dir).expanduser())
    song_name = Path(song_dir).name

    if not output_lrc_path:
        output_lrc_path = os.path.join(song_dir, f"{song_name}_{version}.lrc")

    # 跳过已存在
    if os.path.isfile(output_lrc_path) and not force:
        print(f"   ⏭️  LRC 已存在（--force 重新生成）：{output_lrc_path}")
        return None

    # 1. 找歌词 + mp3
    lyrics_file = find_lyrics_file(song_dir)
    if not lyrics_file:
        print(f"   ❌ 未找到歌词文件：{song_dir}")
        return None

    mp3_file = find_mp3_for_version(song_dir, version)
    if not mp3_file:
        print(f"   ❌ 未找到 mp3：{song_dir} (v{version})")
        return None

    print(f"   🎙️  FunASR 转写：{Path(mp3_file).name} ({os.path.getsize(mp3_file) // 1024} KB)")

    # 2. 读取歌词
    with open(lyrics_file, 'r', encoding='utf-8') as f:
        lyrics_lines = [line.strip() for line in f.readlines() if line.strip()]

    # 3. ASR 转写
    import time
    start = time.time()
    asr_sentences = asyncio.run(transcribe_audio(mp3_file))
    elapsed = time.time() - start
    print(f"   ⏱️  ASR 耗时：{elapsed:.1f}s, 识别 {len(asr_sentences)} 句")

    if not asr_sentences:
        print(f"   ❌ FunASR 转写失败")
        return None

    # 4. 对齐
    entries = align_lyrics_word_level(lyrics_lines, asr_sentences)
    print(f"   🔗 对齐完成：{len(entries)}/{len(lyrics_lines)} 行")

    if not entries:
        return None

    # 5. 写 LRC
    write_lrc_file(entries, output_lrc_path, metadata={
        'title': song_name,
        'generator': f'FunASR + lrc_align.py ({elapsed:.1f}s)',
    })

    return {
        'song_dir': song_dir,
        'version': version,
        'mp3': mp3_file,
        'lrc': output_lrc_path,
        'entries': entries,
        'elapsed_s': round(elapsed, 1),
        'asr_sentences': len(asr_sentences),
    }


# ─── 批量 & 索引 ──────────────────────────────────────────────────────────────

def update_lrc_index(song_name: str, version: str, entries: list, data_dir: str) -> None:
    """增量更新 data/lrc_data.json。"""
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    lrc_json = data_dir / "lrc_data.json"

    lrc_data = {}
    if lrc_json.exists():
        with open(lrc_json, 'r', encoding='utf-8') as f:
            lrc_data = json.load(f)

    key = f"{song_name}__{version}"
    lrc_data[key] = entries

    with open(lrc_json, 'w', encoding='utf-8') as f:
        json.dump(lrc_data, f, ensure_ascii=False, indent=2)

    print(f"   📇 索引更新：{key} → data/lrc_data.json")


def batch_process(music_dir: str, data_dir: str, force: bool = False) -> dict:
    """
    批量处理 ~/Desktop/📂 音乐/ 下所有歌曲。
    策略：每个歌曲目录每个 mp3 独立生成 LRC。
    """
    music_dir = Path(music_dir).expanduser()
    data_dir = Path(data_dir)

    if not music_dir.exists():
        print(f"❌ 音乐目录不存在：{music_dir}")
        return {}

    results = {}
    failed = []

    # 跳过 Album Cover 等非歌曲目录
    skip_dirs = {'Album Cover', 'Album Cover .zip', '.git', '.DS_Store'}

    for song_dir in sorted(music_dir.iterdir()):
        if not song_dir.is_dir() or song_dir.name in skip_dirs:
            continue

        song_name = song_dir.name
        mp3_files = find_all_mp3(str(song_dir))

        if not mp3_files:
            continue

        results[song_name] = {}

        for mp3 in mp3_files:
            version = extract_version_tag(mp3)
            output_lrc = str(song_dir / f"{song_name}_{version}.lrc")

            # 跳过已存在
            if os.path.isfile(output_lrc) and not force:
                print(f"⏭️  [{song_name}/{version}] 已存在")
                continue

            print(f"\n🎵 [{song_name}/{version}] {Path(mp3).name}")
            result = process_one(str(song_dir), version, output_lrc, force)

            if result:
                update_lrc_index(song_name, version, result['entries'], str(data_dir))
                results[song_name][version] = result['lrc']
            else:
                failed.append(f"{song_name}/{version}")

    print(f"\n{'='*60}")
    print(f"✅ 完成：{sum(len(v) for v in results.values())} 个 LRC")
    if failed:
        print(f"❌ 失败：{len(failed)}")
        for f in failed[:10]:
            print(f"   - {f}")

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LRC 歌词对齐工具 (FunASR)")
    parser.add_argument('--song', help='单首歌目录路径（包含 .mp3 和 .txt）')
    parser.add_argument('--version', default='v1', help='版本号（默认 v1）')
    parser.add_argument('--all-versions', action='store_true', help='处理所有版本')
    parser.add_argument('--output', help='LRC 输出路径（默认：{歌名}_{版本}.lrc）')
    parser.add_argument('--batch', action='store_true', help='批量处理 ~/Desktop/📂 音乐/ 下所有歌曲')
    parser.add_argument('--music-dir', default='~/Desktop/📂 音乐', help='批量模式下的音乐根目录')
    parser.add_argument('--data-dir', default='./data', help='lrc_data.json 输出目录')
    parser.add_argument('--force', action='store_true', help='强制重新生成（覆盖已有）')
    parser.add_argument('--index-only', action='store_true', help='只更新索引，不生成 LRC')

    args = parser.parse_args()

    if args.batch:
        batch_process(args.music_dir, args.data_dir, force=args.force)
    elif args.song:
        song_dir = os.path.expanduser(args.song)
        if args.all_versions:
            for mp3 in find_all_mp3(song_dir):
                version = extract_version_tag(mp3)
                print(f"\n🎵 [{Path(song_dir).name}/{version}]")
                output = args.output or os.path.join(song_dir, f"{Path(song_dir).name}_{version}.lrc")
                result = process_one(song_dir, version, output, args.force)
                if result:
                    update_lrc_index(Path(song_dir).name, version, result['entries'], args.data_dir)
        else:
            output = args.output or os.path.join(song_dir, f"{Path(song_dir).name}_{args.version}.lrc")
            result = process_one(song_dir, args.version, output, args.force)
            if result:
                update_lrc_index(Path(song_dir).name, args.version, result['entries'], args.data_dir)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
