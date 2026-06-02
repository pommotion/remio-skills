#!/usr/bin/env python3
"""
site_publish.py — 网站发布工具

调用 music-vault 的 vault.py build + serve 流程：
1. 触发 build.py extract 扫描 ~/Desktop/📂 音乐/
2. 触发 vault.py build 重建 site/index.html
3. （可选）启动 serve 进程
4. 更新 songs.json 的 poster / lrc 字段

Usage:
    # 完整发布（构建 + 重建网站 + 扫描新歌）
    python site_publish.py --build

    # 只扫描新歌（不重建网站）
    python site_publish.py --scan-only

    # 重建网站（不扫描新歌）
    python site_publish.py --rebuild

    # 自定义 music-vault 路径
    python site_publish.py --vault-dir /custom/path/to/music-vault

依赖：music-vault 目录结构
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_VAULT_DIR = str(
    Path.home() / "Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault"
)
DEFAULT_MUSIC_DIR = "~/Desktop/📂 音乐"
PORT = 8892


def run_cmd(cmd: list, cwd: str, timeout: int = 120) -> dict:
    """执行 shell 命令并返回结果。"""
    print(f"   💻 {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': f'Timeout after {timeout}s'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def scan_new_songs(vault_dir: str, music_dir: str) -> dict:
    """Step 1: 扫描音乐目录 + 提取封面/歌词/封面色调。"""
    print("\n📂 Step 1: 扫描新歌...")
    build_py = os.path.join(vault_dir, "build.py")

    if not os.path.isfile(build_py):
        return {'success': False, 'error': f'build.py 不存在：{build_py}'}

    result = run_cmd(
        ["python3", build_py, "extract"],
        cwd=vault_dir,
        timeout=120,
    )

    if result['success']:
        songs_json = os.path.join(vault_dir, "data", "songs.json")
        if os.path.isfile(songs_json):
            with open(songs_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            total = len(data.get('songs', []))
            print(f"   ✅ 扫描完成：{total} 首歌")

    return result


def build_site(vault_dir: str) -> dict:
    """Step 2: 重建 site/index.html。"""
    print("\n🌐 Step 2: 重建网站...")
    vault_py = os.path.join(vault_dir, "vault.py")

    if not os.path.isfile(vault_py):
        return {'success': False, 'error': f'vault.py 不存在：{vault_py}'}

    result = run_cmd(
        ["python3", vault_py, "build"],
        cwd=vault_dir,
        timeout=180,
    )

    if result['success']:
        site_dir = os.path.join(vault_dir, "site")
        if os.path.isdir(site_dir):
            index = os.path.join(site_dir, "index.html")
            if os.path.isfile(index):
                size_kb = os.path.getsize(index) // 1024
                print(f"   ✅ 网站已生成：{index} ({size_kb} KB)")

    return result


def check_serve_running(port: int = 8892) -> bool:
    """检查 serve 进程是否在运行。"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        result = s.connect_ex(('127.0.0.1', port))
        s.close()
        return result == 0
    except Exception:
        return False


def start_serve(vault_dir: str, port: int = 8892, no_browser: bool = True) -> dict:
    """Step 3: 启动 serve 进程。"""
    print(f"\n🚀 Step 3: 启动 HTTP 服务 (端口 {port})...")

    if check_serve_running(port):
        print(f"   ℹ️  端口 {port} 已在运行，无需启动")
        return {'success': True, 'already_running': True}

    vault_py = os.path.join(vault_dir, "vault.py")
    if not os.path.isfile(vault_py):
        return {'success': False, 'error': f'vault.py 不存在：{vault_py}'}

    # 后台启动
    log_path = os.path.join(vault_dir, "server.log")
    try:
        if no_browser:
            with open(log_path, 'a') as logf:
                proc = subprocess.Popen(
                    ["python3", vault_py, "serve", "--no-browser"],
                    cwd=vault_dir, stdout=logf, stderr=logf,
                    start_new_session=True
                )
        else:
            proc = subprocess.Popen(
                ["python3", vault_py, "serve"],
                cwd=vault_dir,
                start_new_session=True
            )

        time.sleep(2)
        if check_serve_running(port):
            print(f"   ✅ 服务已启动：http://localhost:{port}/")
            return {'success': True, 'pid': proc.pid}
        else:
            return {'success': False, 'error': '启动后端口仍未监听'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def full_publish(vault_dir: str, music_dir: str, no_browser: bool = True) -> dict:
    """完整发布流程：扫描 → 构建 → （可选）启动 serve。"""
    print(f"{'='*60}")
    print(f"🌐 Music Vault 完整发布流程")
    print(f"   Vault: {vault_dir}")
    print(f"   Music: {music_dir}")
    print(f"{'='*60}")

    results = {}

    # 1. 扫描
    results['scan'] = scan_new_songs(vault_dir, music_dir)
    if not results['scan'].get('success'):
        return results

    # 2. 构建网站
    results['build'] = build_site(vault_dir)
    if not results['build'].get('success'):
        return results

    # 3. （可选）启动 serve
    if not no_browser:
        results['serve'] = start_serve(vault_dir, PORT, no_browser)
    else:
        results['serve'] = {'success': True, 'note': 'no_browser 模式，未启动 serve'}

    # 汇总
    print(f"\n{'='*60}")
    print(f"📊 发布结果")
    print(f"   扫描：{'✅' if results['scan'].get('success') else '❌'}")
    print(f"   构建：{'✅' if results['build'].get('success') else '❌'}")
    if 'serve' in results and 'pid' in results.get('serve', {}):
        print(f"   服务：http://localhost:{PORT}/ (PID {results['serve']['pid']})")

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Music Vault 网站发布工具")
    parser.add_argument('--vault-dir', default=DEFAULT_VAULT_DIR, help='music-vault 目录路径')
    parser.add_argument('--music-dir', default=DEFAULT_MUSIC_DIR, help='音乐根目录')
    parser.add_argument('--build', action='store_true', help='完整发布（扫描+构建+启动服务）')
    parser.add_argument('--scan-only', action='store_true', help='只扫描新歌，不重建网站')
    parser.add_argument('--rebuild', action='store_true', help='只重建网站，不扫描')
    parser.add_argument('--no-browser', action='store_true', default=True, help='不自动打开浏览器')
    parser.add_argument('--port', type=int, default=PORT, help='HTTP 端口')

    args = parser.parse_args()

    if args.build:
        full_publish(args.vault_dir, args.music_dir, no_browser=args.no_browser)
    elif args.scan_only:
        scan_new_songs(args.vault_dir, args.music_dir)
    elif args.rebuild:
        build_site(args.vault_dir)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
