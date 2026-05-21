#!/usr/bin/env python3
"""
validate-archive.py — Phase 8 归档前自动验证
用法: python scripts/validate-archive.py --lyrics "歌词文本" --note "笔记内容" [--strict]
"""

import re
import sys
import json

def validate_lyrics(text: str) -> list:
    """检查歌词块中是否有括号残留"""
    issues = []
    # 匹配中文和英文括号
    bracket_pattern = re.compile(r'[\(（].*?[\)）]')
    matches = bracket_pattern.findall(text)
    if matches:
        for i, line in enumerate(text.split('\n'), 1):
            found = bracket_pattern.findall(line)
            if found:
                issues.append(f"L{i}: 发现括号残留: {found}")
    return issues

def validate_note(note_content: str) -> dict:
    """检查归档笔记 7 项 Checklist"""
    results = {}
    
    # 1. 情感锚点
    results["1_情感锚点"] = bool(re.search(r'情感锚点', note_content))
    
    # 2. 场景五感素材表
    results["2_场景五感"] = bool(re.search(r'(五感|场景.*素材)', note_content))
    
    # 3. 反陈词滥调清单
    results["3_反陈词滥调"] = bool(re.search(r'陈词滥调|不用：', note_content))
    
    # 4. Hook 设计思路
    results["4_Hook设计"] = bool(re.search(r'Hook.*思路|记忆点', note_content))
    
    # 5. 双平台 Prompt
    has_minimax = bool(re.search(r'(mmx music generate|--prompt|--lyrics-file)', note_content))
    has_suno = bool(re.search(r'Style of Music', note_content))
    results["5_双平台Prompt"] = has_minimax and has_suno
    if not has_minimax:
        results["5_缺MiniMax"] = True
    if not has_suno:
        results["5_缺Suno"] = True
    
    # 6. 音乐描述设定
    results["6_音乐描述设定"] = bool(re.search(r'音乐描述设定', note_content))
    
    # 7. 歌词块纯净 - 查找歌词正文区域
    lyric_match = re.search(r'## 二、歌词正文\s*```\s*(.*?)\s*```', note_content, re.DOTALL)
    if lyric_match:
        lyric_block = lyric_match.group(1)
        results["7_歌词纯净"] = len(validate_lyrics(lyric_block)) == 0
        if not results["7_歌词纯净"]:
            results["7_残留"] = validate_lyrics(lyric_block)
    else:
        results["7_歌词纯净"] = False
        results["7_残留"] = ["未找到歌词正文区域"]
    
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--lyrics", help="歌词文本（检查括号残留）")
    parser.add_argument("--note", help="笔记内容（7项 Checklist）")
    parser.add_argument("--strict", action="store_true", help="严格模式，任何缺失返回非零退出码")
    args = parser.parse_args()
    
    exit_code = 0
    
    if args.lyrics:
        issues = validate_lyrics(args.lyrics)
        if issues:
            print("❌ 歌词括号扫描未通过：")
            for issue in issues:
                print(f"  {issue}")
            exit_code = 1
        else:
            print("✅ 歌词纯净（零括号残留）")
    
    if args.note:
        results = validate_note(args.note)
        passed = sum(1 for k, v in results.items() 
                     if not k.endswith(("缺MiniMax", "缺Suno", "残留")) and v is True)
        total_checklist = 7
        
        print(f"\n📋 Checklist: {passed}/{total_checklist} 通过")
        
        all_pass = True
        for k, v in results.items():
            if k.endswith(("缺MiniMax", "缺Suno", "残留")):
                continue
            status = "✅" if v else "❌"
            print(f"  {status} {k}")
            if not v:
                all_pass = False
                # 显示额外信息
                for extra_key in [f"{k.split('_')[0]}_缺MiniMax", f"{k.split('_')[0]}_缺Suno", f"{k.split('_')[0]}_残留"]:
                    if extra_key in results and results[extra_key]:
                        if isinstance(results[extra_key], list):
                            for item in results[extra_key]:
                                print(f"     → {item}")
                        else:
                            print(f"     → 缺失: {extra_key.split('_')[-1]}")
        
        if not all_pass:
            exit_code = 1
    
    if args.strict and exit_code != 0:
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
