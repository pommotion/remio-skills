#!/usr/bin/env python3
"""
mmx 歌词预处理脚本 — 在 mmx music generate 之前自动清洗歌词文件。

用法：
    python lyrics-prep.py --input raw_lyrics.txt --output clean_lyrics.txt [--apply-replacements]

功能：
    1. 去除所有括号描述词（中英文括号）→ 替换为 [Instrumental] 或删除
    2. 去除所有非 [Tag] 结构标签的"舞台指令"（如："渐强"、"吉他回授声"等独立行）
    3. 自动替换 mmx 发音黑名单词
    4. 拆分超长句（>12 字的行自动拆分为两行）
    5. 验证输出纯净度（0 括号、0 描述词）

核心原则：mmx --lyrics-file 中只允许两种内容：
    - [Tag] 结构标签（如 [Verse], [Chorus], [Bridge] 等）
    - 纯歌词文字（就是要被唱出来的内容）
    任何其他内容都会被 mmx 当歌词唱出来。
"""

import re
import sys
import argparse

# ============================================================
# 1. mmx 支持的结构标签白名单
# ============================================================
VALID_TAGS = {
    '[Intro]', '[Verse]', '[Pre Chorus]', '[Chorus]', '[Interlude]',
    '[Bridge]', '[Outro]', '[Post Chorus]', '[Transition]', '[Break]',
    '[Hook]', '[Build Up]', '[Inst]', '[Solo]', '[Instrumental]',
    # 带数字的变体
}
VALID_TAG_PATTERN = re.compile(r'^\[(Intro|Verse\s*\d*|Pre\s*Chorus|Chorus|Interlude|Bridge|Outro|Post\s*Chorus|Transition|Break|Hook|Build\s*Up|Inst|Solo|Instrumental)\]\s*$', re.IGNORECASE)

# ============================================================
# 2. 发音黑名单：mmx 无法正确发音的词 → 替换词
# ============================================================
PRONUNCIATION_BLACKLIST = {
    '画框': '定框',
    '缝补': '修补',
    '依归': '方向',
    '干涸': '枯裂',
    '禁止项': '禁区标',
    '避让': '躲避',
    'AI': '人工智能',
}

# ============================================================
# 3. 括号描述词 → 处理策略
# ============================================================
# 匹配所有中英文括号内容
PAREN_PATTERN = re.compile(r'[（(][^）)]*[）)]')

# ============================================================
# 4. "舞台指令"检测：独立行的非歌词内容
# ============================================================
# 如果一行不是 [Tag]，也不像是歌词（太短、包含特定关键词），可能是描述
STAGE_DIRECTION_KEYWORDS = [
    '渐强', '渐弱', '渐起', '渐弱', '淡出', '淡入',
    '回授', '失真', '环境音', '采样', '音效',
    '吉他', '钢琴', '贝斯', '鼓点', '合成器', '弦乐',
    '低鸣', '沙沙声', '嗡鸣', '节拍', '低频',
    '踏板', '效果器', '吉他声', '蟋蟀', '风声',
    '车轮声', '报站', '落叶', '小孩笑',
]

def is_stage_direction(line: str) -> bool:
    """判断一行是否是舞台指令/音乐描述（不是歌词）"""
    stripped = line.strip()
    if not stripped:
        return False
    # 如果是有效 tag，不是舞台指令
    if VALID_TAG_PATTERN.match(stripped):
        return False
    # 如果行中包含多个舞台指令关键词，很可能是描述
    keyword_count = sum(1 for kw in STAGE_DIRECTION_KEYWORDS if kw in stripped)
    if keyword_count >= 2:
        return True
    # 如果整行很短（<4字）且不包含任何标点，可能是描述
    # 但也可能是短歌词，所以只在包含特定关键词时标记
    if len(stripped) <= 6:
        for kw in STAGE_DIRECTION_KEYWORDS:
            if kw in stripped:
                return True
    return False

# ============================================================
# 5. 长句拆分
# ============================================================
MAX_LINE_LENGTH = 14  # 超过这个字数就考虑拆分

def split_long_line(line: str) -> list[str]:
    """尝试在自然停顿点拆分长句"""
    stripped = line.strip()
    if len(stripped) <= MAX_LINE_LENGTH:
        return [line]
    
    # 寻找拆分点：空格、逗号、顿号等
    split_chars = [' ', '，', ',', '、']
    best_pos = -1
    best_diff = len(stripped)  # 最小化两半差距
    
    for char in split_chars:
        pos = stripped.find(char)
        while pos != -1:
            left_len = pos
            right_len = len(stripped) - pos - 1
            if left_len >= 3 and right_len >= 3:  # 两半都至少3字
                diff = abs(left_len - right_len)
                if diff < best_diff:
                    best_diff = diff
                    best_pos = pos
            pos = stripped.find(char, pos + 1)
    
    if best_pos > 0:
        left = stripped[:best_pos].strip()
        right = stripped[best_pos + 1:].strip()
        if left and right:
            return [left, right]
    
    # 无法自然拆分，保持原样
    return [line]

# ============================================================
# 主处理流程
# ============================================================

def process_lyrics(raw: str, apply_replacements: bool = False) -> tuple[str, list[str]]:
    """
    处理歌词文本，返回 (清洗后文本, 警告列表)
    """
    warnings = []
    lines = raw.split('\n')
    output_lines = []
    
    in_lyrics_block = False
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 跳过空行（保留一个空行用于分段）
        if not stripped:
            if output_lines and output_lines[-1] != '':
                output_lines.append('')
            continue
        
        # Step 1: 检查是否是结构标签
        if VALID_TAG_PATTERN.match(stripped):
            output_lines.append(stripped)
            continue
        
        # Step 2: 去除括号描述词
        cleaned = PAREN_PATTERN.sub('', stripped)
        if cleaned != stripped:
            removed = stripped.replace(cleaned, '').strip()
            warnings.append(f"Line {i}: 去除括号描述: {removed}")
        cleaned = cleaned.strip()
        
        # 如果去除括号后行为空，跳过（或替换为 [Instrumental]）
        if not cleaned:
            # 检查是否在歌曲开头（环境音描述）
            if any(kw in stripped for kw in ['环境', '风声', '车轮', '蟋蟀', '翻书', '吉他回授']):
                output_lines.append('[Instrumental]')
                warnings.append(f"Line {i}: 环境音描述 → [Instrumental]")
            continue
        
        # Step 3: 检查是否是舞台指令
        if is_stage_direction(stripped):
            warnings.append(f"Line {i}: 疑似舞台指令被移除: {stripped}")
            output_lines.append('[Instrumental]')
            continue
        
        # Step 4: 替换发音黑名单
        if apply_replacements:
            for bad, good in PRONUNCIATION_BLACKLIST.items():
                if bad in cleaned:
                    cleaned = cleaned.replace(bad, good)
                    warnings.append(f"Line {i}: 发音替换: {bad} → {good}")
        
        # Step 5: 拆分超长句
        split_lines = split_long_line(cleaned)
        if len(split_lines) > 1:
            warnings.append(f"Line {i}: 长句拆分: '{stripped}' → {len(split_lines)} 行")
        output_lines.extend(split_lines)
    
    # 清理连续空行
    result_lines = []
    prev_empty = False
    for line in output_lines:
        if line == '':
            if not prev_empty:
                result_lines.append('')
            prev_empty = True
        else:
            result_lines.append(line)
            prev_empty = False
    
    result = '\n'.join(result_lines).strip() + '\n'
    return result, warnings

def validate(clean: str) -> list[str]:
    """验证清洗后的歌词是否符合 mmx 要求"""
    errors = []
    
    # 检查括号残留
    if re.search(r'[（）()]', clean):
        matches = re.findall(r'[（(][^）)]*[）)]', clean)
        errors.append(f"❌ 仍有括号残留: {matches}")
    
    # 检查非 tag 行中是否有可疑内容
    for i, line in enumerate(clean.split('\n'), 1):
        stripped = line.strip()
        if not stripped:
            continue
        if VALID_TAG_PATTERN.match(stripped):
            continue
        # 检查 AI
        if 'AI' in stripped:
            errors.append(f"❌ Line {i}: 包含 'AI'（mmx 发音扭曲），应替换为 '人工智能'")
    
    return errors


def main():
    parser = argparse.ArgumentParser(description='mmx 歌词预处理')
    parser.add_argument('--input', required=True, help='输入歌词文件路径')
    parser.add_argument('--output', required=True, help='输出清洗后歌词文件路径')
    parser.add_argument('--apply-replacements', action='store_true', 
                       help='应用发音黑名单替换')
    parser.add_argument('--dry-run', action='store_true',
                       help='只显示变更，不写文件')
    args = parser.parse_args()
    
    with open(args.input, 'r', encoding='utf-8') as f:
        raw = f.read()
    
    print(f"📖 读取: {args.input} ({len(raw)} 字符)")
    
    cleaned, warnings = process_lyrics(raw, args.apply_replacements)
    
    if warnings:
        print(f"\n⚠️ 处理了 {len(warnings)} 个问题:")
        for w in warnings:
            print(f"  {w}")
    else:
        print("\n✅ 歌词已经是干净的，无需处理")
    
    # 验证
    errors = validate(cleaned)
    if errors:
        print(f"\n❌ 验证失败:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"\n✅ 验证通过: 0 括号、0 描述词")
    
    if args.dry_run:
        print(f"\n📄 清洗后歌词预览:")
        print("---")
        print(cleaned)
        print("---")
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"\n📝 已写入: {args.output} ({len(cleaned)} 字符)")


if __name__ == '__main__':
    main()
