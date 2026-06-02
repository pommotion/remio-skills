# BeatPrints 海报生成 Phase 8

> 目标：从每首歌的封面生成 9:16 竖版海报（2280×3480），用于短视频封面、社交媒体推广、音乐网站展示。

## 1. 设计规范

| 区域 | 规格 | 内容 |
|------|------|------|
| 顶部（0-280px） | 纯色背景 | 留白呼吸区 |
| 封面（280-2300px） | 1920×1920 居中 | 封面图 + 10px 白色描边 + 圆角 |
| 渐变区（2880-3480px） | 600px 高 | 黑色 200α → 0α 渐变 |
| 标题（2960-3120px） | 120pt 加粗 | 歌名（白色 240α + 黑色 200α 阴影）|
| 信息行（3120-3180px） | 48pt 常规 | 时长 · 流派 · 情绪（白色 160α） |

## 2. 工具调用

### 2.1 单首歌

```bash
python <SKILL_ROOT>/scripts/beatprint_gen.py \
  --cover "~/Desktop/📂 音乐/六月之后/cover_六月之后.png" \
  --title "六月之后" \
  --genre "Pop Rock" \
  --emotion "倔强" \
  --duration 192
```

参数：
- `--cover`：封面图片路径（必须）
- `--title`：歌曲标题（必须）
- `--genre`：流派标签（可选）
- `--emotion`：情感标签（可选）
- `--duration`：时长（秒）
- `--output`：输出路径（默认 `{歌名}_poster.png` 与 cover 同目录）

### 2.2 批量（从 music-vault 读取 songs.json）

```bash
python <SKILL_ROOT>/scripts/beatprint_gen.py \
  --from-vault "/Users/wanglingwei/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/music-vault" \
  --music-dir "~/Desktop/📂 音乐"
```

跳过已有 `_poster.png` 的歌曲（增量模式）。`--force` 重新生成。

### 2.3 强制重新生成

```bash
python <SKILL_ROOT>/scripts/beatprint_gen.py --from-vault /path/to/vault --force
```

## 3. 字体处理

macOS 字体优先级（脚本自动查找）：

```
/System/Library/Fonts/STHeiti Medium.ttc          # 华文黑体（推荐）
/System/Library/Fonts/STHeiti Light.ttc
/System/Library/Fonts/PingFang.ttc                # 苹果苹方
/System/Library/Fonts/Hiragino Sans GB.ttc        # 冬青黑体
/Library/Fonts/Arial Unicode.ttf                  # 跨平台
/System/Library/Fonts/Supplemental/Songti.ttc
```

**建议**：如果某个字体没有，按序 fallback 即可。如果所有系统字体都没找到，会使用 PIL 默认字体（位图字体，效果差）。

## 4. 输出

每张海报：
- 尺寸：2280×3480（9:16 竖版，Retina 友好）
- 格式：PNG
- 大小：约 800-1500 KB
- 路径：`{歌名}_poster.png`（与 cover 同目录）

## 5. 与 music-vault 集成

海报路径会写入 songs.json：

```json
{
  "title": "六月之后",
  "cover": {
    "path": "/Users/.../cover_六月之后.png"
  },
  "poster": "/Users/.../六月之后_poster.png"
}
```

music-vault 网站会自动展示海报：
- 主播放页：左下角 BeatPrints 缩略图
- 点击放大到全屏查看
- 移动端直接是 9:16 适配

## 6. 自检清单

- [ ] 海报文件存在
- [ ] 尺寸 = 2280×3480（用 `file` 命令或 PIL 验证）
- [ ] 标题在画面内（不溢出）
- [ ] 字体未降级到默认（查看 PNG 视觉确认）
- [ ] songs.json 的 `poster` 字段已更新

## 7. 故障排除

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 标题居中偏移 | 中文字体宽度计算偏差 | 检查 `font_large` 加载路径 |
| 字体降级到默认 | 系统字体全找不到 | 确认 `FONT_PATHS` 中至少有一个存在 |
| 封面无描边 | 描边 alpha 60 太低 | 调整 `frame` 的填充 alpha |
| 渐变太重/太轻 | `** 1.5` 指数 | 改为 `** 1.2`（更柔和）或 `** 2.0`（更强）|
| 文字看不清 | 渐变不充分 | 增加 `grad_h` 到 800px |
| 保存慢 | PNG optimize | 设置 `optimize=False` 加快速度 |

## 8. 检查点

```
BeatPrints 完成：[歌名] → 2280×3480, [KB]
批量模式：生成 N 张，跳过 M 张
确认后进入 4 维质量评分。
```
