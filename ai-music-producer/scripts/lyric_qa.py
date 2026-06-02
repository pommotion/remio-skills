#!/usr/bin/env python3
"""
lyric_qa.py — 4 维歌词质量自动评分

按 lyric-qa skill 规范自动检测 D1-D4 四个维度，输出综合评分。
结果可写回 remio 笔记（"## 三、质量检测"段落）和 lrc_data.json。

Usage:
    # 评分单首歌词文件
    python lyric_qa.py --lyrics ~/Desktop/📂\ 音乐/六月之后/六月之后_lyrics.txt

    # 评分字符串（管道输入）
    python lyric_qa.py --text "$(cat lyrics.txt)"

    # 评分并写回笔记
    python lyric_qa.py --lyrics ... --note-id mpwo2judryqgjit4ghn

    # 批量（扫描音乐目录）
    python lyric_qa.py --batch --music-dir "~/Desktop/📂 音乐"

依赖：pip install jieba
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

try:
    import jieba
    jieba.setLogLevel(20)
except ImportError:
    print("⚠️  jieba 未安装：D1 关键词匹配精度降低，pip install jieba")
    jieba = None


# ─── D1: 陈词滥调扫描 ────────────────────────────────────────────────────────

CLICHE_CATEGORIES = {
    "直接情绪": [
        "我好想你", "我想你", "想你", "想念", "我想念",
        "心痛", "心碎", "心伤", "心死", "心酸",
        "难过", "悲伤", "痛苦", "忧伤", "伤心",
        "哭", "泪水", "眼泪", "流泪", "哭泣",
        "孤单", "孤独", "寂寞", "无助", "崩溃",
        "好想你", "好孤单", "好难过", "好伤心",
    ],
    "天气套路": [
        "暴雨如注", "倾盆大雨", "大雨倾盆",
        "大雪纷飞", "鹅毛大雪",
        "雷电交加", "风雨交加",
    ],
    "身体套路": [
        "泪水模糊双眼", "泪水模糊了双眼", "泪流满面",
        "心如刀割", "心如死灰", "心如刀绞",
        "窒息", "无法呼吸", "喘不过气",
        "浑身颤抖", "心在滴血",
    ],
    "时间套路": [
        "永远", "一生一世", "天长地久", "永永远远",
        "直到永远", "海枯石烂", "地老天荒",
    ],
    "动作套路": [
        "转身离去", "转身离开", "转身走",
        "独自走在雨中", "独自走在风里", "独自一人",
        "望着窗外", "眺望远方",
    ],
    "修辞套路": [
        "你是我的一切", "你是我全部", "我的全部",
        "失去你世界暗了", "没有你的世界", "失去你",
        "我的唯一", "我的世界",
    ],
    "AI 烂梗": [
        "愿你", "愿你安好", "愿你被这个世界温柔以待",
        "未来可期", "未来由你书写", "诗与远方",
        "星辰大海", "不负韶华", "不负遇见",
        "热爱生活", "活出精彩", "成为更好的自己",
        "拥抱明天", "心怀热爱", "奔赴山海",
        "用尽全力", "拼尽全力", "竭尽全力",
        "终将", "终会", "终究会",
        "岁月静好", "静好", "现世安稳",
        "梦想", "坚持", "加油", "努力", "奋斗",
        "青春无悔", "永远年轻", "永远热泪盈眶",
        "再见", "再会", "后会无期",  # 仅当无具体场景时算套路
    ],
}

# 反陈词滥调阈值：每 100 字允许的陈词滥调数
CLICHE_DENSITY_PER_100 = 0.5


def scan_cliche(lyrics: str) -> dict:
    """D1: 陈词滥调扫描。"""
    matches = []  # [{line_no, original, category, suggestion}]

    lines = lyrics.split('\n')
    for i, line in enumerate(lines, 1):
        # 跳过段落标记和空行
        if re.match(r'^\[.+\]$', line) or not line.strip():
            continue
        for cat, keywords in CLICHE_CATEGORIES.items():
            for kw in keywords:
                if kw in line:
                    # 给出替换建议
                    suggestion = ""
                    if cat == "直接情绪":
                        suggestion = f"用场景/物件暗示情感，例如「{line.replace(kw, '你走时忘了关那盏灯')}」"
                    elif cat == "天气套路":
                        suggestion = "换晴天反差，或用微天气（细雨/雾气）"
                    elif cat == "身体套路":
                        suggestion = "用反直觉的身体反应（如「手指不自觉地摸了摸手机」）"
                    elif cat == "时间套路":
                        suggestion = "用具体时间单位（如同样的十二年）"
                    elif cat == "动作套路":
                        suggestion = "换空间/动作细节（如「把门带上但没锁」）"
                    elif cat == "修辞套路":
                        suggestion = "用对比/反差替代直接比喻"
                    elif cat == "AI 烂梗":
                        suggestion = "用具体场景或具象行为替代口号式表达"
                    matches.append({
                        'line_no': i,
                        'line': line,
                        'keyword': kw,
                        'category': cat,
                        'suggestion': suggestion,
                    })
                    break  # 一行一个匹配

    # 评分
    total_chars = sum(len(line) for line in lines if line.strip() and not re.match(r'^\[.+\]$', line))
    density = len(matches) * 100 / max(total_chars, 1)

    if density == 0:
        score = 95
        level = "🟢 优秀"
    elif density <= 0.3:
        score = int(85 - density * 50)
        level = "🟡 良好"
    elif density <= 0.8:
        score = int(70 - density * 20)
        level = "🟠 需改进"
    else:
        score = max(0, int(50 - density * 10))
        level = "🔴 重写"

    return {
        'dimension': 'D1. 陈词滥调扫描',
        'score': score,
        'level': level,
        'matches': matches,
        'density_per_100': round(density, 2),
        'total_chars': total_chars,
    }


# ─── D2: 画面感评分 ───────────────────────────────────────────────────────────

# 抽象情绪词
EMOTION_KEYWORDS = {
    '想', '念', '爱', '恨', '痛', '伤', '悲', '喜', '怒', '忧', '怕', '惧',
    '孤单', '孤独', '寂寞', '无助', '迷茫', '彷徨',
    '美好', '幸福', '快乐', '温暖', '甜蜜', '苦涩',
    '心', '情', '感', '灵魂', '心碎', '心痛',
    '想', '思念', '想念', '怀念',
}

# 视觉/听觉/嗅觉/触觉/味觉
SENSE_PATTERNS = {
    '视觉': re.compile(r'(光|暗|色|影|形|远|近|亮|明|闪|亮|红|蓝|绿|白|黑|灰|黄|紫|彩|斑|纹|线|点|圈|圆|方|条|窗|门|墙|路|街|屋|房|台|桌|椅|床|灯|镜|钟|表|旗|画|照片|纸|页)'),
    '听觉': re.compile(r'(声|音|响|静|嗡|滴答|鸣|叫|啼|哭|笑|喊|吼|歌|曲|调|弦|鼓|铃|钟|轰|隆|雷|风|雨|沙|沙沙|唦|敲|拍|打)'),
    '嗅觉': re.compile(r'(香|味|臭|气息|味道|气|烟|雾|霉|花|草|木|土|海|风)'),
    '触觉': re.compile(r'(冷|热|软|硬|凉|温|暖|烫|冰|冻|湿|干|滑|粗|糙|轻|重|厚|薄)'),
    '味觉': re.compile(r'(苦|甜|酸|咸|涩|辣|鲜|香|淡|浓)'),
}

# 动词/动作词 → 叙事行
ACTION_KEYWORDS = re.compile(r'[一-龥]{1,3}(了|着|过|来|去|下|上|出|进|开|关|到|走|跑|坐|站|握|拿|放|看|听|说|写|读|想|睡|起|翻|压|碰|摸|折|撕|剪|开|关|穿|戴|收|藏|寄|送|递|交|关|拉|推|抬|低|弯|伸|抖|拍|握|抓|握|抓|摇|摆|推|敲|开|扔|丢|抛|撒)')

# 留白词
EMPTY_KEYWORDS = re.compile(r'^(哦|啊|呀|呢|嗯|哦|啊|哈|嘿|喂|喔|噢|呜|哎)\W*$|^(oh|ah|eh|hmm|yeah|hey|yo|oh)\W*$', re.IGNORECASE)


def classify_line(line: str) -> str:
    """把歌词行分类：画面/情绪/叙事/留白。"""
    line_clean = re.sub(r'[\s，。、！？；：,.!?;:\'"()\[\]{}]', '', line)

    if not line_clean:
        return 'empty'

    if EMPTY_KEYWORDS.match(line_clean):
        return 'whitespace'

    # 统计特征
    has_emotion = any(kw in line_clean for kw in EMOTION_KEYWORDS)
    has_action = bool(ACTION_KEYWORDS.search(line))
    sense_count = sum(1 for p in SENSE_PATTERNS.values() if p.search(line))

    if sense_count >= 2 and not has_emotion:
        return 'imagery'  # 纯画面
    if has_action and sense_count >= 1 and not has_emotion:
        return 'imagery'  # 画面+动作
    if has_action and not has_emotion:
        return 'narrative'  # 叙事
    if has_emotion and sense_count == 0:
        return 'emotion'  # 纯情绪
    if has_emotion and sense_count >= 1:
        return 'imagery_emotion'  # 混合（算画面）
    if sense_count >= 1:
        return 'imagery'  # 有感官词
    return 'narrative'  # 默认


def scan_imagery(lyrics: str) -> dict:
    """D2: 画面感评分。"""
    lines = lyrics.split('\n')
    classification = []
    sense_coverage = set()

    for i, line in enumerate(lines, 1):
        if re.match(r'^\[.+\]$', line) or not line.strip():
            classification.append({'line_no': i, 'line': line, 'class': 'section'})
            continue
        cls = classify_line(line)
        classification.append({'line_no': i, 'line': line, 'class': cls})
        for sense, p in SENSE_PATTERNS.items():
            if p.search(line):
                sense_coverage.add(sense)

    # 统计
    total = sum(1 for c in classification if c['class'] != 'section' and c['class'] != 'empty')
    imagery_count = sum(1 for c in classification if c['class'] in ['imagery', 'imagery_emotion'])
    imagery_ratio = imagery_count * 100 / max(total, 1)

    # 评分
    if imagery_ratio >= 70:
        score = 90 + min(10, int((imagery_ratio - 70) * 0.5))
        level = "🟢 优秀"
    elif imagery_ratio >= 50:
        score = 70 + int((imagery_ratio - 50) * 1)
        level = "🟡 良好"
    elif imagery_ratio >= 30:
        score = 40 + int((imagery_ratio - 30) * 1.5)
        level = "🟠 需改进"
    else:
        score = int(imagery_ratio * 1.3)
        level = "🔴 重写"

    return {
        'dimension': 'D2. 画面感评分',
        'score': min(100, score),
        'level': level,
        'imagery_ratio': round(imagery_ratio, 1),
        'imagery_count': imagery_count,
        'total_lines': total,
        'sense_coverage': sorted(sense_coverage),
        'sense_count': len(sense_coverage),
        'classification': classification,
    }


# ─── D3: Hook 强度 ───────────────────────────────────────────────────────────

# 提取副歌段落
def extract_chorus_sections(lyrics: str) -> list:
    """提取 [Chorus] 标记的所有段落。"""
    sections = re.split(r'\n(?=\[.+\])', lyrics)
    choruses = []
    current_label = None
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        lines = sec.split('\n')
        label = lines[0]
        content = '\n'.join(lines[1:]).strip()
        if not re.match(r'^\[.+\]$', label):
            continue
        label_clean = re.sub(r'[\[\]]', '', label).lower()
        if 'chorus' in label_clean or '副歌' in label_clean or 'hook' in label_clean or 'hook' in label_clean:
            choruses.append({'label': label, 'content': content, 'lines': content.split('\n') if content else []})
    return choruses


def score_hook(lyrics: str) -> dict:
    """D3: Hook 强度。"""
    choruses = extract_chorus_sections(lyrics)
    if not choruses:
        return {
            'dimension': 'D3. Hook 强度',
            'score': 0,
            'level': '🔴 无 Hook',
            'error': '未找到 [Chorus] 或 [副歌] 段落',
        }

    # 从所有 chorus 段落统计行频（不只 main）
    # 这样 Final Chorus 不会覆盖 C1/C2 的核心 hook
    all_lines = []
    for c in choruses:
        all_lines.extend([l for l in c['lines'] if l.strip()])

    lines = all_lines

    if not lines:
        return {
            'dimension': 'D3. Hook 强度',
            'score': 0,
            'level': '🔴 无 Hook',
            'error': '副歌内容为空',
        }

    # 1. 长度
    # 找最核心的重复句（出现 ≥2 次或最短）
    line_counter = Counter([re.sub(r'[\s，。、！？；：,.!?;:\'\"()\[\]{}]', '', l) for l in lines])
    if line_counter:
        core = line_counter.most_common(1)[0][0]
    else:
        core = lines[0]

    core_clean = re.sub(r'[\s，。、！？；：,.!?;:\'\"()\[\]{}]', '', core)
    length_ok = len(core_clean) <= 9
    length_score = 30 if length_ok else 0

    # 2. 重复次数
    repeat_count = line_counter.get(core_clean, 0)
    repeat_ok = repeat_count >= 2
    repeat_score = 30 if repeat_ok else 0

    # 3. 记忆点（重复字/叠字）
    chars = list(core_clean)
    has_double = any(chars[i] == chars[i+1] for i in range(len(chars) - 1)) if len(chars) > 1 else False
    has_repeat = has_double
    memory_score = 20 if has_repeat else 0

    # 4. 开头（动词/感叹词/具体名词）
    first_char = core_clean[0] if core_clean else ""
    starts_with_action = bool(re.match(r'[\u4e00-\u9fff]', first_char) and first_char not in '我你他她它们的是在有不')
    starts_score = 20 if starts_with_action else 10

    score = length_score + repeat_score + memory_score + starts_score
    if score >= 90:
        level = "🟢 强 Hook"
    elif score >= 60:
        level = "🟡 中等"
    elif score >= 30:
        level = "🟠 弱 Hook"
    else:
        level = "🔴 无 Hook"

    return {
        'dimension': 'D3. Hook 强度',
        'score': score,
        'level': level,
        'core': core,
        'length': len(core_clean),
        'repeat_count': repeat_count,
        'length_pass': length_ok,
        'repeat_pass': repeat_ok,
        'memory_pass': has_repeat,
        'starts_pass': starts_with_action,
        'all_choruses': len(choruses),
        'total_chorus_lines': len(all_lines),
    }


# ─── D4: 韵律一致性 ──────────────────────────────────────────────────────────

# 中文韵母检测（简化版）
RHYME_GROUPS = {
    'a': re.compile(r'[aāáǎà]'),
    'o': re.compile(r'[oōóǒò]'),
    'e': re.compile(r'[eēéěè]'),
    'i': re.compile(r'[iīíǐì]'),
    'u': re.compile(r'[uūúǔù]'),
    'v': re.compile(r'[üǖǘǚǜ]'),
    'ai': re.compile(r'ai'),
    'ei': re.compile(r'ei'),
    'ui': re.compile(r'ui'),
    'ao': re.compile(r'ao'),
    'ou': re.compile(r'ou'),
    'iu': re.compile(r'iu'),
    'ie': re.compile(r'ie'),
    've': re.compile(r've'),
    'er': re.compile(r'er'),
    'an': re.compile(r'an'),
    'en': re.compile(r'en'),
    'in': re.compile(r'in'),
    'un': re.compile(r'un'),
    'vn': re.compile(r'vn'),
    'ang': re.compile(r'ang'),
    'eng': re.compile(r'eng'),
    'ing': re.compile(r'ing'),
    'ong': re.compile(r'ong'),
    'ian': re.compile(r'ian'),
    'iang': re.compile(r'iang'),
    'iao': re.compile(r'iao'),
    'uai': re.compile(r'uai'),
    'uan': re.compile(r'uan'),
    'uang': re.compile(r'uang'),
}


def get_rhyme_vowel(line: str) -> str:
    """提取一行最后一个字的韵母。"""
    line_clean = re.sub(r'[\s，。、！？；：,.!?;:\'\"()\[\]{}]', '', line)
    if not line_clean:
        return ''
    last_char = line_clean[-1]

    # 简化：用拼音库（如果可用），否则用韵母组匹配
    try:
        from pypinyin import lazy_pinyin
        pinyin = lazy_pinyin(last_char)
        if pinyin and pinyin[0]:
            # 提取韵母部分
            full = pinyin[0]
            # 找韵母
            for group_name, pattern in sorted(RHYME_GROUPS.items(), key=lambda x: -len(x[0])):
                if pattern.search(full):
                    return group_name
    except ImportError:
        pass

    # Fallback: 用韵母组直接匹配（精度低）
    for group_name, pattern in sorted(RHYME_GROUPS.items(), key=lambda x: -len(x[0])):
        if pattern.search(last_char):
            return group_name
    return '?'


def score_rhyme(lyrics: str) -> dict:
    """D4: 韵律一致性。"""
    lines = lyrics.split('\n')
    sections = []
    current_section = None

    # 分段
    for line in lines:
        if re.match(r'^\[.+\]$', line):
            if current_section:
                sections.append(current_section)
            current_section = {'label': line, 'rhymes': [], 'lengths': []}
        elif current_section is not None and line.strip():
            rhyme = get_rhyme_vowel(line)
            length = len(re.sub(r'[\s，。、！？；：,.!?;:\'\"()\[\]{}]', '', line))
            current_section['rhymes'].append(rhyme)
            current_section['lengths'].append(length)

    if current_section:
        sections.append(current_section)

    if not sections:
        return {
            'dimension': 'D4. 韵律一致性',
            'score': 0,
            'level': '🔴 混乱',
            'error': '未识别到任何段落',
        }

    # 分析每段韵脚
    section_rhymes = [s['rhymes'] for s in sections if s['rhymes']]
    main_rhyme = Counter()
    for rhymes in section_rhymes:
        if rhymes:
            main_rhyme[rhymes[-1]] += 1  # 每段最后一行作主韵脚

    if not main_rhyme:
        return {
            'dimension': 'D4. 韵律一致性',
            'score': 0,
            'level': '🔴 混乱',
        }

    primary = main_rhyme.most_common(1)[0][0]
    primary_count = main_rhyme[primary]
    total_sections = len(main_rhyme)
    rhyme_consistency = primary_count / total_sections

    # 节奏
    all_lengths = [l for s in sections for l in s['lengths']]
    if all_lengths:
        avg_len = sum(all_lengths) / len(all_lengths)
        max_len = max(all_lengths)
        min_len = min(all_lengths)
        rhythm_score = 100 - min(50, abs(max_len - min_len) * 5)
    else:
        avg_len = 0
        max_len = 0
        min_len = 0
        rhythm_score = 0

    # 综合
    if rhyme_consistency >= 0.9 and rhythm_score >= 80:
        score = 95
        level = "🟢 优秀"
    elif rhyme_consistency >= 0.7 and rhythm_score >= 60:
        score = 80
        level = "🟡 良好"
    elif rhyme_consistency >= 0.5:
        score = 60
        level = "🟠 需改进"
    else:
        score = 30
        level = "🔴 混乱"

    return {
        'dimension': 'D4. 韵律一致性',
        'score': score,
        'level': level,
        'primary_rhyme': primary,
        'primary_count': primary_count,
        'total_sections': total_sections,
        'rhyme_consistency': round(rhyme_consistency * 100, 1),
        'avg_length': round(avg_len, 1),
        'max_length': max_len,
        'min_length': min_len,
        'rhythm_score': rhythm_score,
        'section_rhymes': [{'label': s['label'], 'rhymes': s['rhymes']} for s in sections if s['rhymes']],
    }


# ─── 综合评分 ────────────────────────────────────────────────────────────────

WEIGHTS = {
    'D1. 陈词滥调扫描': 0.25,
    'D2. 画面感评分': 0.35,
    'D3. Hook 强度': 0.25,
    'D4. 韵律一致性': 0.15,
}


def overall_score(d1: dict, d2: dict, d3: dict, d4: dict) -> dict:
    """加权综合。"""
    dims = {'D1. 陈词滥调扫描': d1, 'D2. 画面感评分': d2, 'D3. Hook 强度': d3, 'D4. 韵律一致性': d4}
    overall = sum(d['score'] * WEIGHTS[d['dimension']] for d in dims.values())

    if overall >= 85:
        level = "🟢 优秀"
    elif overall >= 70:
        level = "🟡 良好"
    elif overall >= 50:
        level = "🟠 需改进"
    else:
        level = "🔴 重写"

    return {
        'overall': round(overall, 1),
        'level': level,
        'dimensions': dims,
        'weights': WEIGHTS,
    }


# ─── 报告输出 ────────────────────────────────────────────────────────────────

def format_report(d1: dict, d2: dict, d3: dict, d4: dict, song_name: str = "") -> str:
    """格式化为 markdown 报告。"""
    overall = overall_score(d1, d2, d3, d4)

    lines = []
    lines.append("## 三、质量检测\n")
    lines.append("| 维度 | 评分 | 等级 |")
    lines.append("|------|------|------|")
    lines.append(f"| {d1['dimension']} | {d1['score']}/100 | {d1['level']} |")
    lines.append(f"| {d2['dimension']} | {d2['score']}/100 | {d2['level']} |")
    lines.append(f"| {d3['dimension']} | {d3['score']}/100 | {d3['level']} |")
    lines.append(f"| {d4['dimension']} | {d4['score']}/100 | {d4['level']} |")
    lines.append(f"| **综合评分** | **{overall['overall']}/100** | **{overall['level']}** |")
    lines.append("")

    # 详细
    lines.append("### 详细分析\n")
    lines.append(f"#### {d1['dimension']}")
    lines.append(f"陈词滥调密度：{d1['density_per_100']} 个/100 字")
    if d1['matches']:
        lines.append("\n| 行号 | 原文 | 类型 | 建议 |")
        lines.append("|------|------|------|------|")
        for m in d1['matches'][:10]:
            lines.append(f"| L{m['line_no']} | {m['line'][:30]} | {m['category']} | {m['suggestion'][:40]} |")
    else:
        lines.append("✅ 无陈词滥调")
    lines.append("")

    lines.append(f"#### {d2['dimension']}")
    lines.append(f"画面行占比：{d2['imagery_ratio']}%（{d2['imagery_count']}/{d2['total_lines']}）")
    lines.append(f"五感覆盖：{', '.join(d2['sense_coverage'])}（{d2['sense_count']}/5）")
    lines.append("")

    lines.append(f"#### {d3['dimension']}")
    lines.append(f"核心 Hook：`{d3.get('core', 'N/A')}`")
    lines.append(f"长度：{d3.get('length', 0)} 字 {'✅' if d3.get('length_pass') else '❌'}（≤9 字）")
    lines.append(f"重复：{d3.get('repeat_count', 0)} 次 {'✅' if d3.get('repeat_pass') else '❌'}（≥2 次）")
    lines.append(f"记忆点：{'✅' if d3.get('memory_pass') else '❌'}（叠字/重复字）")
    lines.append(f"开头：{'✅' if d3.get('starts_pass') else '❌'}（动词/名词开头）")
    lines.append("")

    lines.append(f"#### {d4['dimension']}")
    lines.append(f"主韵脚：`{d4.get('primary_rhyme', '?')}`（{d4.get('primary_count', 0)}/{d4.get('total_sections', 0)} 段）")
    lines.append(f"韵脚一致性：{d4.get('rhyme_consistency', 0)}%")
    lines.append(f"节奏：平均 {d4.get('avg_length', 0)} 字/行（最长 {d4.get('max_length', 0)}，最短 {d4.get('min_length', 0)}）")
    lines.append("")

    # 改进优先级
    lines.append("### 改进建议\n")
    if d1['score'] < 70:
        lines.append("1. **D1 优先**：清理陈词滥调（最基础质量门径）")
    if d2['score'] < 70:
        lines.append("2. **D2 优先**：增加画面感（替换情绪行为画面行）")
    if d3['score'] < 60:
        lines.append("3. **D3 优先**：重写 Hook（副歌是歌曲灵魂）")
    if d4['score'] < 70:
        lines.append("4. **D4 优先**：调整韵律（韵脚是音乐性基础）")
    if all(d['score'] >= 70 for d in [d1, d2, d3, d4]):
        lines.append("✅ 四维度均已通过质量门径")
    lines.append("")

    return "\n".join(lines)


# ─── 笔记写回 ────────────────────────────────────────────────────────────────

def find_insertion_point(note_content: str) -> Optional[int]:
    """找笔记中应插入质量检测的位置。

    优先级：
    1. "## 三、质量检测" 后面
    2. "## 三、" 之后
    3. "## 三、版本历史" 之前
    """
    if '## 三、质量检测' in note_content:
        return note_content.find('## 三、质量检测')
    if '## 三、版本历史' in note_content:
        return note_content.find('## 三、版本历史')
    if '## 二、' in note_content:
        # 插在 二、 之后
        marker = '## 二、'
        idx = note_content.find(marker)
        # 找下一个 ## 段
        next_section = note_content.find('\n## ', idx + 1)
        if next_section > 0:
            return next_section
    return None


# ─── 主流程 ────────────────────────────────────────────────────────────────

def run_qa(lyrics: str) -> tuple:
    """对歌词跑 4 维检测，返回 (d1, d2, d3, d4, overall)。"""
    d1 = scan_cliche(lyrics)
    d2 = scan_imagery(lyrics)
    d3 = score_hook(lyrics)
    d4 = score_rhyme(lyrics)
    return d1, d2, d3, d4


def main():
    parser = argparse.ArgumentParser(description="4 维歌词质量自动评分")
    parser.add_argument('--lyrics', help='歌词文件路径')
    parser.add_argument('--text', help='直接传歌词字符串（与 --lyrics 二选一）')
    parser.add_argument('--batch', action='store_true', help='批量评分 ~/Desktop/📂 音乐/')
    parser.add_argument('--music-dir', default='~/Desktop/📂 音乐')
    parser.add_argument('--note-id', help='写回 remio 笔记的 noteId')
    parser.add_argument('--output', help='报告输出路径（默认 stdout）')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown')

    args = parser.parse_args()

    if args.batch:
        music_dir = Path(args.music_dir).expanduser()
        results = []
        for song_dir in sorted(music_dir.iterdir()):
            if not song_dir.is_dir():
                continue
            # 找歌词
            lyrics_file = None
            for f in sorted(song_dir.iterdir()):
                if f.is_file() and 'lyrics' in f.name.lower() and f.suffix == '.txt':
                    lyrics_file = f
                    break
            if not lyrics_file:
                continue
            with open(lyrics_file, 'r', encoding='utf-8') as f:
                lyrics = f.read()
            d1, d2, d3, d4 = run_qa(lyrics)
            overall = overall_score(d1, d2, d3, d4)
            results.append({
                'song': song_dir.name,
                'overall': overall['overall'],
                'level': overall['level'],
                'd1': d1['score'], 'd2': d2['score'],
                'd3': d3['score'], 'd4': d4['score'],
            })
            print(f"✅ {song_dir.name}: {overall['overall']}/100 {overall['level']}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n报告已写入：{args.output}")
        return

    # 单首歌
    if args.lyrics:
        with open(os.path.expanduser(args.lyrics), 'r', encoding='utf-8') as f:
            lyrics = f.read()
    elif args.text:
        lyrics = args.text
    else:
        parser.print_help()
        return

    d1, d2, d3, d4 = run_qa(lyrics)
    overall = overall_score(d1, d2, d3, d4)

    if args.format == 'json':
        result = {
            'overall': overall['overall'],
            'level': overall['level'],
            'dimensions': overall['dimensions'],
        }
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = format_report(d1, d2, d3, d4)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"报告已写入：{args.output}")
    else:
        print(output)

    # 写回笔记
    if args.note_id:
        # 不直接 import remio（不是 Python 包）。
        # 输出报告到文件，让 agent 用 update_note syscall 写回。
        import tempfile
        report_path = os.path.join(
            tempfile.gettempdir(),
            f"qa_report_{args.note_id}.md"
        )
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n💡 报告已写入：{report_path}")
        print(f"   请用 remio_syscall update_note 写回：")
        print(f"   1. read_note {args.note_id}")
        print(f"   2. find_insertion_point(content) 定位")
        print(f"   3. content[:pos] + report + content[pos:] 拼接")
        print(f"   4. update_note(note_id={args.note_id}, content=...)")


if __name__ == '__main__':
    main()
