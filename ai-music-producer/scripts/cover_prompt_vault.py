#!/usr/bin/env python3
"""
Music Vault 封面 Prompt 模板
融合小小东 #47 一字美学 + #68 丝网印刷风格
bozo-aigc (BizyAir GPT Image 2) 专用，1:1 2048×2048

用法:
  from cover_prompt import build_cover_prompt
  prompt = build_cover_prompt(title="随身携带", emotion="怀旧", genre="Indie Folk", lyrics_preview="...")
"""

# 歌曲意境 → 视觉象征物映射
EMOTION_SYMBOLS = {
    "怀旧": ["泛黄的照片", "旧信封", "锈蚀的怀表", "褪色的车票"],
    "温暖": ["暖光台灯", "一杯热茶", "毛毯", "壁炉余烬"],
    "孤独": ["空旷长椅", "路灯下的影子", "雾中孤舟", "空房间"],
    "思念": ["窗台上的信", "远方的灯塔", "断线的风筝", "未拨出的电话"],
    "释然": ["雨后彩虹", "打开的窗", "落叶飘远", "破晓的光"],
    "坚定": ["磐石", "扎根的树", "黎明前地平线", "铁轨延伸向远方"],
    "忧伤": ["枯萎的花", "碎裂的镜子", "雨天玻璃窗", "空酒杯"],
    "热烈": ["燃烧的火焰", "烟花", "盛夏阳光", "绽放的花"],
    "迷茫": ["迷宫", "分叉路口", "雾中森林", "模糊的路标"],
    "愤怒": ["雷电", "碎裂的地面", "暴风雨", "烧焦的痕迹"],
    "浪漫": ["月光", "花瓣", "星空下的剪影", "蜡烛光晕"],
    "自由": ["飞翔的鸟", "开阔的原野", "风中飘扬的布", "无边的海"],
    "成长": ["年轮", "阶梯", "破土的芽", "蜕壳"],
    "离别": ["车站月台", "渐行渐远的背影", "关上的门", "最后一张合影"],
}

# 歌曲流派 → 色彩温度 & 材质倾向
GENRE_PALETTE = {
    "folk":      {"warm": "锈红、赭石、枯叶橙",  "cool": "深青灰、雾蓝",     "texture": "旧纸纤维、木纹"},
    "rock":      {"warm": "暗红、焦黑",          "cool": "深蓝灰、冷铁灰",    "texture": "金属刮痕、砂纸"},
    "pop":       {"warm": "琥珀褐、蜜糖棕",      "cool": "浅烟蓝、灰紫",     "texture": "光滑纸面、轻微光泽"},
    "electronic":{"warm": "暗橙、电路铜",         "cool": "深蓝、霓虹青",     "texture": "印刷网点、数字噪点"},
    "blues":     {"warm": "深琥珀、旧铜",         "cool": "深靛蓝、夜色",     "texture": "旧唱片纹理、烟雾"},
    "ambient":   {"warm": "淡赭、暖雾",           "cool": "深雾蓝、水墨灰",    "texture": "宣纸晕染、水痕"},
    "punk":      {"warm": "鲜红、警示橙",         "cool": "死黑、冷白",       "texture": "撕裂纸边、喷涂"},
    "jazz":      {"warm": "深棕、黄铜",           "cool": "午夜蓝、深紫",     "texture": "丝绒、旧胶片颗粒"},
    "rnb":       {"warm": "玫瑰金、深蜜",         "cool": "深靛蓝、暗紫",     "texture": "光滑质感、微光"},
    "hip-hop":   {"warm": "暗金、铜锈",           "cool": "深灰、冷黑",       "texture": "混凝土、金属"},
    "cinematic": {"warm": "焦糖棕、暮光橙",       "cool": "深蓝灰、雾色",     "texture": "胶片颗粒、光晕"},
    "lofi":      {"warm": "米色、暖棕",           "cool": "灰绿、浅蓝灰",     "texture": "磁带噪点、旧纸"},
}


def _classify_genre(genre_str: str) -> str:
    """将流派字符串归类到 GENRE_PALETTE 的 key"""
    g = (genre_str or "").lower()
    mapping = [
        (["folk", "民谣", "country", "acoustic"], "folk"),
        (["rock", "punk", "post-rock", "post-punk", "grunge"], "rock"),
        (["pop", "synth-pop", "electro-pop", "dream-pop"], "pop"),
        (["electronic", "synth", "edm", "techno", "house"], "electronic"),
        (["blues", "blues-rock"], "blues"),
        (["ambient", "new-age", "chill"], "ambient"),
        (["jazz", "soul", "neo-soul", "r&b", "rnb"], "jazz"),
        (["hip-hop", "rap", "trap"], "hip-hop"),
        (["cinematic", "ballad", "epic"], "cinematic"),
        (["lo-fi", "lofi", "chillhop"], "lofi"),
    ]
    for keywords, key in mapping:
        if any(k in g for k in keywords):
            return key
    return "cinematic"  # 默认用电影感


def _pick_symbols(emotion: str, count: int = 3) -> list:
    """从情绪映射中挑选象征物"""
    emo = (emotion or "").lower()
    # 尝试匹配关键词
    for key, symbols in EMOTION_SYMBOLS.items():
        if key in emo:
            return symbols[:count]
    # 没匹配到就组合默认的
    return ["光影交错的纹理", "模糊的轮廓", "时间的痕迹"][:count]


def build_cover_prompt(
    title: str,
    emotion: str = "",
    genre: str = "",
    lyrics_preview: str = "",
    inspiration: str = "",
) -> str:
    """
    生成封面 prompt（汤底+佐料）
    
    Args:
        title: 歌曲标题（必填）
        emotion: 情绪标签
        genre: 流派标签
        lyrics_preview: 歌词前几行
        inspiration: 创作灵感/来源
    """
    genre_key = _classify_genre(genre)
    palette = GENRE_PALETTE.get(genre_key, GENRE_PALETTE["cinematic"])
    symbols = _pick_symbols(emotion, 3)
    
    # 标题字数决定排版策略
    title_len = len(title)
    if title_len <= 2:
        title_layout = f'两个字\u201c{title}\u201d以超大尺度占据画面中心，笔画像铁锈斑驳的重墨书法，每个字独立成章，之间有呼吸留白'
    elif title_len <= 4:
        title_layout = f'四个大字\u201c{title}\u201d作为画面视觉主体，使用粗犷厚重的不规则手写书法体，笔画带飞白、断笔、墨团渗化，字形大小错落，重心微晃，像压住画面的巨石'
    else:
        title_layout = f'标题\u201c{title}\u201d以竖排或错落的排版方式分布在画面中，手写书法体，字距疏朗，行距留出空气，像一组漂浮的标本'

    # 歌词意境补充（取前60字）
    lyrics_hint = ""
    if lyrics_preview:
        # 取第一行有意义的歌词
        lines = [l.strip() for l in lyrics_preview.split("\n") if l.strip()]
        if lines:
            lyrics_hint = f'\n歌词意境提示："{lines[0][:40]}"'

    # 创作灵感补充
    inspiration_hint = ""
    if inspiration:
        inspiration_hint = f"\n创作来源：{inspiration[:80]}"

    prompt = f"""为歌曲《{title}》设计一张1:1正方形专辑封面。

核心视觉：中文{title_layout}。标题占据画面中心偏上位置，是整张封面的视觉骨架和精神锚点。标题文字用旧纸白或淡象牙色，边缘带轻微晕染。

标题周围环绕象征物剪影：{'、'.join(symbols)}——这些物品只露出局部轮廓，从画面边缘裁切进入，不完整展示，与标题产生呼应关系。

所有图形处理为丝网印刷质感：半调网点、颗粒纹理、破损油墨、漏印、边缘毛糙。不要干净矢量图，不要写实照片。

色彩系统：暗色背景（深墨灰近黑），上半部分偏暖（{palette['warm']}），下半部分偏冷（{palette['cool']}），中间留出深色呼吸区域承托标题。{palette['texture']}质感融入背景。色彩低饱和、被纸张吸收、干燥、略微褪色。

整体气质：暗调、克制、有旧物感、有印刷品被时间侵蚀的质感。高级音乐专辑封面级别。{lyrics_hint}{inspiration_hint}

不要写实照片，不要3D，不要高饱和霓虹色，不要可爱风格，不要出现人脸。"""

    return " ".join(prompt.split())


# === CLI 快速测试 ===
if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        tests = [
            {"title": "铁门", "emotion": "怀旧", "genre": "Indie Folk"},
            {"title": "随身携带", "emotion": "温暖", "genre": "Acoustic Pop"},
            {"title": "看不见的界面", "emotion": "迷茫", "genre": "Synth Pop"},
            {"title": "你手机里那张照片", "emotion": "思念", "genre": "Lo-Fi Folk"},
        ]
        for t in tests:
            p = build_cover_prompt(**t)
            print(f"\n{'='*60}")
            print(f"《{t['title']}》| {t['emotion']} | {t['genre']}")
            print(f"{'='*60}")
            print(p[:200] + "...")
    elif len(sys.argv) > 1:
        # 用法: python cover_prompt.py "歌名" ["情绪"] ["流派"]
        title = sys.argv[1]
        emotion = sys.argv[2] if len(sys.argv) > 2 else ""
        genre = sys.argv[3] if len(sys.argv) > 3 else ""
        print(build_cover_prompt(title, emotion, genre))
    else:
        print("用法: python cover_prompt.py '歌名' ['情绪'] ['流派']")
        print("      python cover_prompt.py --test")
