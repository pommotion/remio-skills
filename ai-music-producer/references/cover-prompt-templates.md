# GPT-Image-2 封面提示词模板库

> 基于 OpenAI 官方 Prompting Guide + 社区最佳实践整理
> 适用于 BizyAir GPT_IMAGE_2 / mmx image / OpenAI 官方 API
> 2026-05-20

---

## 核心原则

### 1. Scene → Subject → Details → Use case → Constraints 五段式

GPT-Image-2 是**推理型模型**，不是关键词标签匹配器。结构化提示词让模型「先规划构图再生成」，效果远超堆砌形容词。

```
Scene:     场景/环境/光源/时间
Subject:   主体/构图核心
Details:   材质/质感/镜头/色彩/氛围
Use case:  用途（album cover / poster / thumbnail）
Constraints: 约束（no text / no watermark / exact color 等）
```

### 2. 朴素 > 堆砌

| 维度 | ❌ 旧模型习惯 | ✅ GPT-Image-2 最佳 |
|------|-------------|-------------------|
| 长度 | 50-150 词 | 15-40 词 |
| 形容词 | 10+ 个 | 2-3 个即可 |
| 构图指令 | "centered / rule of thirds" | 简单描述或省略 |
| 光线 | "dramatic cinematic volumetric lighting" | "soft morning light" 足够 |
| 首次成功率 | 40-60% | 80%+ |

### 3. 文字渲染的「引号法则」

要让封面里出现歌名，用英文引号包住：
```
Title "看不见的界面" in elegant serif, centered at bottom
```
中文渲染准确率 >95%。要竖排中文加 `vertical Chinese text`。

---

## 风格一：留白极简（Negative Space）

适合：电子/氛围/沉思类歌曲

```
Scene: Empty room with a single light source from above, casting soft shadows on matte white walls.
Subject: One small object [描述核心意象] sits at the exact center.
Details: Monochrome with a single accent color [指定颜色]. Ultra-clean, no texture, no pattern. The object should feel like a 3D render — perfect geometry, soft shadow.
Use case: Album cover, 1:1 square format.
Constraints: No text, no watermark, no gradient, no grain. Maximum negative space — the object should occupy less than 15% of the frame.
```

**示例（看不见的界面）：**
```
Scene: Dark void with a single faint blue screen glow in the center.
Subject: A translucent glass screen floating horizontally, reflecting nothing.
Details: Deep navy background, the screen emits cold blue light. The glass has subtle fingerprints visible on its surface. Clean 3D render aesthetic, soft ambient occlusion shadows.
Use case: Album cover, 1:1 square.
Constraints: No text, no watermark, no people. The screen occupies less than 10% of frame. No other light sources.
```

---

## 风格二：摄影写实（Cinematic Photography）

适合：民谣/摇滚/叙事类歌曲

```
Scene: [具体地点和时间], [光源描述].
Subject: [具体主体/人物/物体], [位置和姿态].
Details: Shot on 35mm film, [光圈/镜头], [颗粒感/色温], [色调倾向]. Natural imperfections — film grain, slight light leaks.
Use case: Album cover photography, 1:1 square crop.
Constraints: No text overlay, no watermark, photorealistic, no CGI look. Reserve top 30% as dark space for title placement.
```

**示例（地铁到站）：**
```
Scene: Inside a late-night subway car, fluorescent lights humming, window reflecting city lights outside.
Subject: An empty seat by the window, a pair of wireless headphones left on it.
Details: Shot on 35mm film, 50mm f/1.8, shallow depth of field. Warm amber tones from the platform lights mixing with cool fluorescent. Subtle film grain, slight vignette. The window shows blurred station lights passing.
Use case: Album cover, 1:1 square crop.
Constraints: No people visible, no text, no watermark. Photorealistic. The empty seat should feel emotionally charged, not just empty.
```

---

## 风格三：概念插画（Conceptual Illustration）

适合：艺术流行/实验电子/哲学主题

```
Scene: [抽象场景描述], [情绪底色].
Subject: [核心隐喻意象], rendered in [插画风格].
Details: [色彩方案], [线条/笔触特征], [层次感描述]. Fine art quality, like a gallery print.
Use case: Album cover art, 1:1 square.
Constraints: No text, no watermark. Avoid cartoon style. Think museum poster, not children's book.
```

**示例（神经末梢）：**
```
Scene: A vast dark space where biology meets electricity, branches of light growing outward like neural networks.
Subject: A single neuron rendered as a branching tree of light, its dendrites reaching toward the edges of the frame, each tip glowing a different color.
Details: Deep indigo and electric blue palette. Bioluminescent glow effect, semi-transparent layers. Mix of scientific illustration precision and organic fluidity. Fine ink lines with watercolor wash.
Use case: Album cover art, 1:1 square.
Constraints: No text, no watermark, no cartoon. Should feel like a cross between a scientific plate and a contemporary art piece. The branching pattern should feel infinite, extending beyond the frame edges.
```

---

## 风格四：纹理质感（Textural / Material）

适合：后摇/暗潮/情绪浓烈的歌曲

```
Scene: [材质/纹理场景], [微观或宏观视角].
Subject: [核心材质或物体], shot in extreme [detail/close-up].
Details: [材质描述: 金属/玻璃/布料/纸张/水], [光影描述]. Macro photography feel, every texture visible.
Use case: Album cover, 1:1 square.
Constraints: No text, no watermark, photorealistic texture. Focus on material authenticity.
```

**示例（碎片里的人）：**
```
Scene: A dark surface covered in broken mirror shards, each piece reflecting a different angle of warm golden light.
Subject: The largest shard in the center reflects a human silhouette that's incomplete — half face, half void.
Details: Cool steel grey shards against warm amber reflections. Extreme macro detail — every crack edge, every dust particle visible. High contrast between the cold sharp shards and the warm soft reflections. Shallow depth of field, only the center shard is tack sharp.
Use case: Album cover, 1:1 square.
Constraints: No text, no watermark. The reflected silhouette should be ambiguous — could be anyone. Photorealistic, no illustration style.
```

---

## 风格五：电影帧（Cinematic Frame / Still）

适合：叙事性强、画面感明确的歌曲

```
Scene: [电影场景描述], [时段/天气/季节].
Subject: [角色/动作/物体], framed from [角度/距离].
Details: Cinematic color grade — [色调描述]. Anamorphic lens flare, [宽高比暗示]. Shallow depth of field. The image should feel like a paused frame from an A24 film.
Use case: Album cover, 1:1 square crop from a wider cinematic frame.
Constraints: No text, no faces visible (silhouette or back view only). Moody, atmospheric, not bright or cheerful. Should feel like a movie poster without the title.
```

**示例（第十一次搬家）：**
```
Scene: A bare room at golden hour, sunlight streaming through a single window, dust particles floating in the light beam.
Subject: A single brown cardboard box in the center of the empty room, casting a long shadow across the wooden floor. The box has handwritten text in marker but it's intentionally unreadable.
Details: Warm sepia color grade with crushed blacks. 35mm anamorphic lens feel, subtle lens flare from the window light. The room should feel lived-in — scuff marks on the floor, a faint rectangle on the wall where a picture frame used to hang. Shallow focus on the box, room edges soft.
Use case: Album cover, 1:1 square crop.
Constraints: No people, no text readable, no watermark. The feeling should be "someone just left" — presence through absence. Not sad, not hopeful, just still.
```

---

## 风格六：带文字的唱片封面（Typographic Cover）

适合：所有类型，当需要歌名出现在封面上时

```
Scene: [纯色/渐变/纹理背景描述].
Subject: The song title "[歌名]" rendered in [字体风格], [位置和对齐].
Details: [色彩方案], [装饰元素], [质感]. The typography IS the artwork — no illustration needed.
Use case: Album cover with title, 1:1 square.
Constraints: Title text must render exactly as written in quotes. No other text. No watermark. Render verbatim, no substitutions.
```

**示例（叫你的名字）：**
```
Scene: Warm cream background with subtle paper texture, like aged letter paper.
Subject: The title "叫你的名字" rendered in elegant handwritten Chinese calligraphy, centered, with the last character slightly trailing off as if the writer's hand was trembling.
Details: Black ink on warm cream. The calligraphy should feel personal and emotional — not machine-perfect, with visible brush pressure variations. A single dried flower petal rests near the bottom right corner. Subtle warm vignette around edges.
Use case: Album cover with title, 1:1 square.
Constraints: Title "叫你的名字" must render exactly as written, no substitutions. No other text. No watermark. The calligraphy should feel human, not typeset.
```

---

## 快速配方：按情绪选风格

| 歌曲情绪 | 推荐风格 | 核心技巧 |
|---------|---------|---------|
| 反思/不安 | 留白极简 | 单色+单一意象，<15% 占比 |
| 温暖/留恋 | 摄影写实 | 35mm 胶片，暖色调，有颗粒感 |
| 好奇/眩晕 | 概念插画 | 科学插画×艺术，生物发光效果 |
| 破碎/觉醒 | 纹理质感 | 微观细节，冷暖对比，裂纹/碎片 |
| 坚韧/释然 | 电影帧 | A24 色调，silhouette，presence through absence |
| 温柔/思念 | 带文字封面 | 手写书法，纸张质感，情感笔触 |

---

## 旧版 vs 新版提示词对比

以「看不见的界面」为例：

### ❌ 旧版（堆砌风格）
```
Minimalist album cover art. Dark blue negative space, a single glowing screen 
icon in center casting soft blue light, thin geometric grid lines barely visible. 
No text, no watermark. Clean modern aesthetic, cinematic lighting, 4K quality.
```
问题：形容词堆砌（minimalist/cinematic/4K），没有结构，模型注意力分散。

### ✅ 新版（Scene → Subject → Details → Constraints）
```
Scene: Dark void with a single faint blue screen glow in the center.
Subject: A translucent glass screen floating horizontally, reflecting nothing.
Details: Deep navy background, the screen emits cold blue light. The glass has 
subtle fingerprints visible on its surface. Clean 3D render aesthetic, soft 
ambient occlusion shadows.
Use case: Album cover, 1:1 square.
Constraints: No text, no watermark, no people. The screen occupies less than 
10% of frame. No other light sources.
```
提升点：五段结构、具体材质（translucent glass）、具体光影（ambient occlusion）、明确占比约束（<10%）。

---

## 参考来源

- [OpenAI 官方 GPT Image Prompting Guide](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide)
- [GPT Image 2 提示词完全指南（videotoprompt.app）](https://www.videotoprompt.app/zh/posts/gpt-image-2-prompt-guide)
- [gpt-image-2 做海报实测（apiyi.com）](https://help.apiyi.com/gpt-image-2-poster-cover-prompts-guide.html)
- [Geniea Minimalist Album Cover Prompts](https://www.geniea.com/prompts/gpt-image-minimalist-album-cover)
- [Media.io AI Album Cover Design Prompts](https://www.media.io/ai-prompts/ai-album-cover-design-prompts.html)
