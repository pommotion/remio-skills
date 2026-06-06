#!/usr/bin/env python3
"""
lrc_align.py — 歌词 LRC 对齐工具（ForcedAligner 版）

通过本地 WSL2 GPU 上的 Qwen3-ForcedAligner-0.6B 服务，一键生成精确 LRC。

核心优势（vs 旧版 FunASR + DTW）：
- 逐字精确时间戳，不惧 Chorus 重复
- ~2s/首（vs 旧版 ~35s）
- 不需要 DashScope API，完全本地

Usage:
    # 对齐单首歌（v1 版本）
    python lrc_align.py --song ~/Desktop/📂\ 音乐/六月之后 --version v1

    # 对齐所有版本
    python lrc_align.py --song ~/Desktop/📂\ 音乐/六月之后 --all-versions

    # 批量处理（增量，跳过已对齐）
    python lrc_align.py --batch

    # 强制重新对齐
    python lrc_align.py --song ~/Desktop/📂\ 音乐/六月之后 --version v1 --force

依赖：pip install requests
环境变量：ASR_URL（默认自动获取 cloudflared tunnel URL）
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ requests 未安装：pip install requests")
    sys.exit(1)

# ─── Config ───────────────────────────────────────────────────────────────────

MUSIC_DIR = Path("~/Desktop/📂 音乐").expanduser()
DATA_DIR = Path(__file__).parent / "data"

# ─── ASR 服务地址 ────────────────────────────────────────────────────────────

def get_asr_url() -> str:
    """获取 ForcedAligner 服务地址。优先级：环境变量 > cloudflared tunnel > 局域网。"""
    # 1. 环境变量
    url = os.environ.get("ASR_URL", "")
    if url:
        return url.rstrip("/")

    # 2. 尝试 cloudflared tunnel（通过 SSH 查询）
    try:
        import subprocess
        result = subprocess.run(
            ["ssh", "pc", "journalctl -u cloudflared-asr --no-pager | grep -o 'https://[a-z0-9-]*\\.trycloudflare\\.com' | tail -1"],
            capture_output=True, text=True, timeout=10,
        )
        tunnel = result.stdout.strip()
        if tunnel:
            # 验证可用
            try:
                r = requests.get(f"{tunnel}/api/health", timeout=5, verify=False)
                if r.status_code == 200:
                    return tunnel
            except Exception:
                pass
    except Exception:
        pass

    # 3. 局域网直连（需要 Windows 端口转发）
    try:
        r = requests.get("http://192.168.50.157:7777/api/health", timeout=3)
        if r.status_code == 200:
            return "http://192.168.50.157:7777"
    except Exception:
        pass

    print("❌ ForcedAligner 服务不可用。请检查：")
    print("   1. WSL2 服务是否启动：asr-on")
    print("   2. cloudflared tunnel 是否运行")
    sys.exit(1)


# ─── ForcedAligner API ───────────────────────────────────────────────────────

def align_lrc(asr_url: str, audio_path: str, lyrics_text: str, language: str = "Chinese") -> dict:
    """调用 ForcedAligner 服务生成 LRC。"""
    r = requests.post(
        f"{asr_url}/api/align/lrc",
        json={"audio_path": audio_path, "lyrics_text": lyrics_text, "language": language},
        timeout=120, verify=False,
    )
    r.raise_for_status()
    return r.json()


def check_health(asr_url: str) -> dict:
    """健康检查。"""
    r = requests.get(f"{asr_url}/api/health", timeout=10, verify=False)
    r.raise_for_status()
    return r.json()


# ─── 文件查找 ─────────────────────────────────────────────────────────────────

def find_lyrics_file(song_dir: Path) -> str:
    """查找歌词文件。优先级：_clean.txt > _lyrics.txt > *.txt"""
    candidates = []
    for f in sorted(song_dir.iterdir()):
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


def find_mp3_for_version(song_dir: Path, version: str) -> str:
    """查找指定版本的 mp3。"""
    for f in sorted(song_dir.iterdir()):
        if not f.is_file() or not f.name.lower().endswith('.mp3'):
            continue
        if f"_v{version[1:]}" in f.name or version in f.name:
            return str(f)
    return ""


def find_all_mp3(song_dir: Path) -> list:
    """查找所有 mp3。"""
    return sorted([str(f) for f in song_dir.iterdir() if f.is_file() and f.name.lower().endswith('.mp3')])


def extract_version_tag(mp3_path: str) -> str:
    """从 mp3 文件名提取版本号。"""
    m = re.search(r'_v(\d+)', Path(mp3_path).stem)
    return f"v{m.group(1)}" if m else "v1"


# ─── LRC 索引 ─────────────────────────────────────────────────────────────────

def load_lrc_data() -> dict:
    """加载 lrc_data.json。"""
    lrc_json = DATA_DIR / "lrc_data.json"
    if lrc_json.exists():
        with open(lrc_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_lrc_data(data: dict) -> None:
    """保存 lrc_data.json。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lrc_json = DATA_DIR / "lrc_data.json"
    with open(lrc_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_lrc_text(lrc_text: str) -> list:
    """将 LRC 文本解析为 [{time, text}, ...] 列表。"""
    entries = []
    for line in lrc_text.strip().split("\n"):
        m = re.match(r'\[(\d{2}:\d{2}\.\d{2})\]\s*(.*)', line)
        if m:
            time_str, text = m.groups()
            parts = time_str.split(":")
            secs = int(parts[0]) * 60 + float(parts[1])
            entries.append({"time": round(secs, 2), "text": text})
    return entries


# ─── 单歌处理 ────────────────────────────────────────────────────────────────

def process_one(asr_url: str, song_dir: str, version: str, force: bool = False) -> dict:
    """处理一首歌的一个版本。返回结果或 None。"""
    song_dir = Path(song_dir).expanduser()
    song_name = song_dir.name
    output_lrc = str(song_dir / f"{song_name}_{version}.lrc")

    # 跳过已存在
    if os.path.isfile(output_lrc) and not force:
        print(f"   ⏭️  LRC 已存在：{output_lrc}")
        return None

    # 1. 找歌词 + mp3
    lyrics_file = find_lyrics_file(song_dir)
    if not lyrics_file:
        print(f"   ❌ 未找到歌词文件：{song_dir}")
        return None

    mp3_file = find_mp3_for_version(song_dir, version)
    if not mp3_file:
        print(f"   ❌ 未找到 mp3：{song_dir} ({version})")
        return None

    # 2. 读取歌词
    with open(lyrics_file, 'r', encoding='utf-8') as f:
        lyrics_text = f.read()

    # 3. 判断 mp3 路径在 WSL 还是 Mac
    # ForcedAligner 服务在 WSL 上，需要 WSL 路径
    # 如果 mp3 在 Mac 上，需要用 base64 传输
    mac_path = str(mp3_file)
    
    # 检查 ASR 服务是否能直接访问文件（同机器用路径，否则 base64）
    payload = {"lyrics_text": lyrics_text, "language": "Chinese"}
    
    # 尝试本地路径（如果 asr_url 是局域网/tunnel，文件在 Mac 上，服务在 WSL 上）
    # WSL 可以通过 /mnt/c/ 访问 Windows 文件，但 Mac 文件不行
    # 所以对于远程服务，必须用 base64
    if "127.0.0.1" in asr_url or "localhost" in asr_url:
        payload["audio_path"] = mac_path
    else:
        # 远程服务：base64 编码
        import base64
        with open(mac_path, 'rb') as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        payload["audio_base64"] = audio_b64

    print(f"   🎙️  ForcedAligner 对齐：{Path(mp3_file).name} ({os.path.getsize(mp3_file) // 1024} KB)")

    t0 = time.time()
    try:
        r = requests.post(f"{asr_url}/api/align/lrc", json=payload, timeout=120, verify=False)
        r.raise_for_status()
        result = r.json()
    except Exception as e:
        print(f"   ❌ ForcedAligner 失败：{e}")
        return None

    elapsed = time.time() - t0

    lrc_text = result.get("lrc", "")
    if not lrc_text:
        print(f"   ❌ LRC 为空")
        return None

    # 4. 写 LRC 文件
    with open(output_lrc, 'w', encoding='utf-8') as f:
        f.write(lrc_text)

    size = os.path.getsize(output_lrc)
    lines = result.get("lines", 0)
    print(f"   ✅ LRC 写入：{output_lrc} ({size} B, {lines} 行, {elapsed:.1f}s)")

    # 5. 解析为 entries（用于索引）
    entries = parse_lrc_text(lrc_text)

    return {
        "song_name": song_name,
        "version": version,
        "mp3": str(mp3_file),
        "lrc": output_lrc,
        "entries": entries,
        "elapsed_s": round(elapsed, 1),
    }


# ─── 批量处理 ────────────────────────────────────────────────────────────────

def batch_process(asr_url: str, music_dir: Path, force: bool = False) -> dict:
    """批量处理所有歌曲。"""
    if not music_dir.exists():
        print(f"❌ 音乐目录不存在：{music_dir}")
        return {}

    lrc_data = load_lrc_data()
    results = {}
    failed = []
    skip_dirs = {'Album Cover', 'Album Cover .zip', '.git', '.DS_Store'}

    for song_dir in sorted(music_dir.iterdir()):
        if not song_dir.is_dir() or song_dir.name in skip_dirs:
            continue

        song_name = song_dir.name
        mp3_files = find_all_mp3(song_dir)
        if not mp3_files:
            continue

        results[song_name] = {}

        for mp3 in mp3_files:
            version = extract_version_tag(mp3)
            key = f"{song_name}__{version}"

            # 增量跳过
            if not force and key in lrc_data:
                print(f"⏭️  [{song_name}/{version}] 索引已有")
                continue

            print(f"\n🎵 [{song_name}/{version}]")
            result = process_one(asr_url, str(song_dir), version, force)

            if result:
                lrc_data[key] = result["entries"]
                results[song_name][version] = result["lrc"]
            else:
                # 也检查文件是否存在（可能 process_one 跳过了）
                lrc_file = str(song_dir / f"{song_name}_{version}.lrc")
                if os.path.isfile(lrc_file):
                    with open(lrc_file, 'r', encoding='utf-8') as f:
                        entries = parse_lrc_text(f.read())
                    lrc_data[key] = entries
                    results[song_name][version] = lrc_file
                else:
                    failed.append(f"{song_name}/{version}")

    # 保存索引
    save_lrc_data(lrc_data)
    total = sum(len(v) for v in results.values())
    print(f"\n{'='*60}")
    print(f"✅ 完成：{total} 个 LRC，索引共 {len(lrc_data)} 个版本")
    if failed:
        print(f"❌ 失败：{len(failed)}")
        for f in failed[:10]:
            print(f"   - {f}")

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LRC 歌词对齐工具 (ForcedAligner)")
    parser.add_argument('--song', help='单首歌目录路径')
    parser.add_argument('--version', default='v1', help='版本号（默认 v1）')
    parser.add_argument('--all-versions', action='store_true', help='处理所有版本')
    parser.add_argument('--output', help='LRC 输出路径')
    parser.add_argument('--batch', action='store_true', help='批量处理 ~/Desktop/📂 音乐/ 下所有歌曲')
    parser.add_argument('--music-dir', default='~/Desktop/📂 音乐', help='音乐根目录')
    parser.add_argument('--data-dir', default='', help='lrc_data.json 输出目录')
    parser.add_argument('--force', action='store_true', help='强制重新生成')
    parser.add_argument('--rebuild', action='store_true', help='对齐后重建网站')
    parser.add_argument('--health', action='store_true', help='检查 ForcedAligner 服务状态')

    args = parser.parse_args()

    global DATA_DIR
    if args.data_dir:
        DATA_DIR = Path(args.data_dir)
    else:
        DATA_DIR = Path(__file__).parent / "data"

    # 获取服务地址
    asr_url = get_asr_url()

    # 健康检查
    if args.health:
        health = check_health(asr_url)
        print(f"✅ 服务正常：{health}")
        return

    # 确认服务可用
    try:
        health = check_health(asr_url)
        print(f"✅ ForcedAligner 服务：{health['gpu']} ({health['vram_used_gb']}GB VRAM)")
    except Exception as e:
        print(f"❌ 服务不可用：{e}")
        sys.exit(1)

    if args.batch:
        music_dir = Path(args.music_dir).expanduser()
        batch_process(asr_url, music_dir, force=args.force)
        if args.rebuild:
            import subprocess
            vault_dir = Path(__file__).parent.parent.parent / "music-vault"
            if not vault_dir.exists():
                vault_dir = Path(os.path.expanduser("~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault"))
            build_py = vault_dir / "build.py"
            if build_py.exists():
                print(f"\n🏗️  重建网站...")
                r = subprocess.run([sys.executable, str(build_py)], capture_output=True, text=True, timeout=120, cwd=str(vault_dir))
                print(r.stdout[-500:] if r.stdout else "(no output)")
                if r.returncode != 0:
                    print(f"⚠️  rebuild 失败: {r.stderr[-500:]}")
            else:
                print(f"⚠️  未找到 build.py: {build_py}")
    elif args.song:
        song_dir = Path(args.song).expanduser()
        if args.all_versions:
            for mp3 in find_all_mp3(song_dir):
                version = extract_version_tag(mp3)
                print(f"\n🎵 [{song_dir.name}/{version}]")
                result = process_one(asr_url, str(song_dir), version, args.force)
                if result:
                    lrc_data = load_lrc_data()
                    lrc_data[f"{song_dir.name}__{version}"] = result["entries"]
                    save_lrc_data(lrc_data)
        else:
            result = process_one(asr_url, str(song_dir), args.version, args.force)
            if result:
                lrc_data = load_lrc_data()
                lrc_data[f"{song_dir.name}__{args.version}"] = result["entries"]
                save_lrc_data(lrc_data)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
