# MiniMax Music 已知避坑清单

> 被 SKILL.md Phase 4 引用。生成前必读。

---

## 🔴🔴🔴 强制预处理（每次生成前必须执行）

**问题根因**：mmx `--lyrics-file` 把文件中所有非 `[Tag]` 文本都当歌词唱。括号 `()` 不起保护作用，`「环境音：键盘声」`、`（吉他回授声 渐强）` 这些描述词每次都会被唱出来。

**⛔ 永久解决方案**：生成前必须运行 `lyrics-prep.py` 自动清洗歌词文件：

```bash
python <SKILL_ROOT>/scripts/lyrics-prep.py \
  --input 原始歌词.txt \
  --output 清洗后歌词.txt \
  --apply-replacements
```

该脚本自动处理：
1. ✅ 去除所有括号描述词（中英文括号）
2. ✅ 去除舞台指令/音乐描述行
3. ✅ 替换 mmx 发音黑名单词
4. ✅ 拆分超长句（>14字）
5. ✅ 验证输出纯净度（0 括号、0 描述词）

**验证通过后才允许执行 `mmx music generate`。**

**在 agent 流程中（非终端），也可以用 Python 直接调用：**
```python
import sys
sys.path.insert(0, '<SKILL_ROOT>/scripts')
from lyrics_prep import process_lyrics, validate

cleaned, warnings = process_lyrics(raw_lyrics, apply_replacements=True)
errors = validate(cleaned)
assert not errors, f"歌词验证失败: {errors}"
with open(output_path, 'w') as f:
    f.write(cleaned)
```

---

## 🔴 绝对禁止（每次都会出错）

### 0. 使用 `--lyrics-optimizer`
- **现象**：输出英文套路歌词，且不消耗 `lyrics_generation` 额度（只是让音乐模型自行发挥）
- **原因**：CLI 的 `--lyrics-optimizer` 并没有调用独立的歌词生成 API，它只是省略了 `--lyrics` 参数让模型自由编
- **解决**：如需 AI 写词，调用**独立的 `POST /v1/lyrics_generation` API**（详见 `references/lyrics-generation-api.md`）

### 1. 歌词块中放括号注释
- **现象**：`(温暖的Rhodes电钢琴)` 会被 mmx 当歌词唱出来
- **原因**：mmx `--lyrics-file` 把所有非 `[Tag]` 文本当歌词，括号 `()` 不起保护作用
- **解决**：音乐描述只写在 `--prompt` 参数中

### 2. 「AI」出现在歌词中
- **现象**：发音扭曲，变成奇怪的音节
- **解决**：写成「人工智能」或具体工具名

---

## 🟡 常见问题（视情况处理）

### 3. 长句吞字
- **现象**：超过 8 个字的行容易吞字
- **处理**：视具体位置决定是否拆分，不要全拆（会破坏韵律）
- **注意**：mmx 对某些词组有顽固发音困难（如「缝补」「画框」「避让」），属于模型级中文局限

### 4. Outro 丢失
- **现象**：生成时 Outro 被跳过或截断
- **处理**：在 Outro 后多写一行重复收尾句，或用 `--structure` 明确标注

### 5. Dream Pop 混响吞字
- **现象**：混响重的风格人声含糊
- **处理**：`--vocals` 加 `but consonants must be clear`

### 6. `--structure` 过度使用
- **现象**：强制结构会让歌曲机械
- **处理**：只在确实跳了关键段落时使用，不要默认全加上

### 7. `--vocals` 过度约束
- **现象**：约束太多让人声失去自然感
- **处理**：保留上一版有特色的人声处理，只修正确实有问题的地方

---

## 🟢 好的习惯

1. **生成前创建目录和歌词文件**：
   ```bash
   mkdir -p ~/Desktop/📂\ 音乐/[歌名]
   cat > /tmp/mmx-songs/[歌名]_lyrics.txt << 'EOF'
   [歌词内容]
   EOF
   ```

2. **每次生成前检查配额**：music-2.6 配额 100 次/日

3. **输出到规范路径**：`--out ~/Desktop/📂\ 音乐/[歌名]/[歌名]_v1.mp3`

4. **版本命名**：v1、v2、v3 并存，不覆盖

5. **先保亮点再修问题**：每次精修前先列出上一版亮点，确保不被破坏
