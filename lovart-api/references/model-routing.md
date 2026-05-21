# Lovart Model Routing Reference

Primary machine-readable source: `references/model-routing.yaml`

This Markdown file explains the intent behind the YAML rules and should stay aligned with it.

## Purpose

This file is a reference-only routing guide for model selection.

Apply it only when the user explicitly asks to:
- choose based on routing
- follow the routing guide
- according to the routing guide
- 根据路由选择模型
- 按路由选模型

Do not apply this file by default.
If the user does not mention routing, prefer normal Lovart routing or an explicit user model request.

## Priority Order

1. Explicit user model request
2. Explicit routing-based selection request
3. Global priority rules in this file
4. Task-specific default route
5. Task-specific fallback route
6. No forced model, let Lovart route automatically

## Availability Rule

Always verify current model availability with:

`python3 {baseDir}/agent_skill.py query-mode`

If the preferred alias is unavailable:
- use the fallback alias
- if fallback is also unavailable, omit `--prefer-models`

## Verified Aliases For This Account (2026-04-22)

### IMAGE
- `generate_image_gpt_image_1_5`
- `generate_image_gpt_image_2`
- `generate_image_nano_banana`
- `generate_image_nano_banana_2`
- `generate_image_nano_banana_pro`
- `generate_image_midjourney`
- `generate_image_seedream_v4`
- `generate_image_seedream_v4_5`

### VIDEO
- `generate_video_kling_v2_6`
- `generate_video_kling_omni_v1`
- `generate_video_wan_v2_6`

## Global Priority Rules

### Chinese Understanding First

If the task depends heavily on Chinese understanding, Chinese text accuracy, Chinese semantic nuance, or visible Chinese copy in the image, prefer:
- Default: `generate_image_gpt_image_2`
- Fallback: `generate_image_seedream_v4_5`

Typical cases:
- Chinese poster title
- Chinese cover headline
- Chinese infographic labels
- Chinese slogan or Chinese text inside the image
- cases where wording accuracy matters more than atmosphere

### Chinese Social Aesthetic First

If the task is mainly about Chinese content-platform visual style rather than text accuracy, prefer:
- Default: `generate_image_seedream_v4_5`
- Fallback: `generate_image_nano_banana_pro`

Typical cases:
- Xiaohongshu cover
- social platform visual hook
- Chinese-style promotional cover

### Atmosphere Or Art Direction First

If the task prioritizes mood, cinematic feel, visual impact, or brand atmosphere, prefer:
- Default: `generate_image_midjourney`
- Fallback: `generate_image_nano_banana_pro`

### Stable Editorial Or General Purpose First

If the task is general-purpose content imagery and does not strongly match another rule, prefer:
- Default: `generate_image_nano_banana_pro`
- Fallback: `generate_image_gpt_image_2`

### Structured Or Clean Design First

If the task needs cleaner layout feeling, product-design feel, or more structured composition, prefer:
- Default: `generate_image_nano_banana_2`
- Fallback: `generate_image_nano_banana_pro`

### Video Default

For general video generation, prefer:
- Default: `generate_video_kling_v2_6`
- Fallback: `generate_video_wan_v2_6`

For more specialized omni-style motion or video tasks:
- Default: `generate_video_kling_omni_v1`
- Fallback: `generate_video_kling_v2_6`

## Task Routes

### 公众号配图
- Default: `generate_image_nano_banana_pro`
- Fallback: `generate_image_gpt_image_2`
- Promote to `generate_image_gpt_image_2` if the image includes Chinese title, Chinese labels, or copy-sensitive Chinese content

### 小红书封面
- Default: `generate_image_seedream_v4_5`
- Fallback: `generate_image_nano_banana_pro`
- Promote to `generate_image_gpt_image_2` if Chinese text accuracy is more important than platform-style aesthetics

### 信息图
- Default: `generate_image_nano_banana_pro`
- Fallback: `generate_image_nano_banana_2`
- Promote to `generate_image_gpt_image_2` if there is significant Chinese text inside the visual

### 写实人物
- Default: `generate_image_gpt_image_2`
- Fallback: `generate_image_midjourney`
- Use Midjourney when atmosphere matters more than instruction precision

### 品牌海报 / KV / 概念海报
- Default: `generate_image_midjourney`
- Fallback: `generate_image_nano_banana_pro`
- Promote to `generate_image_gpt_image_2` if the poster must contain an accurate Chinese title or slogan

### 短视频
- Default: `generate_video_kling_v2_6`
- Fallback: `generate_video_wan_v2_6`
- Promote to `generate_video_kling_omni_v1` when the user explicitly wants more complex or omni-style motion behavior
