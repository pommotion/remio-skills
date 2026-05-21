# 🎹 remio-skills

Custom remio Agent Skills by [violin](https://github.com/pommotion).

## Skills

| Skill | 描述 | 版本 |
|-------|------|------|
| [ai-music-producer](./ai-music-producer/) | AI 音乐全流程制作：灵感→歌词→生成→精修→封面→上架 | v2.7.0 |
| [tuzi-api](./tuzi-api/) | 兔子中转站 API 统一封装（Chat / Image / Suno） | v1.0 |
| [material-writing](./material-writing/) | 资料驱动深度写作：苏格拉底式对话 × 卡片层级 × 断点续传 | v1.0 |
| [scene2lyric](./scene2lyric/) | 场景→歌词：五感素材 + 反陈词滥调 + 画面感法则 | v1.0 |
| [lyric-qa](./lyric-qa/) | 歌词质量四维检测：陈词滥调/画面感/Hook/韵律 | v1.0 |
| [music-prompt-templates](./music-prompt-templates/) | AI 音乐 Prompt 模板库：流派×场景，支持 MiniMax + Suno | v1.0 |
| [bozo-aigc](./bozo-aigc/) | 文生图与图生图（BizyAir GPT Image 2 + Gemini） | v1.0 |
| [listenhub](./listenhub/) | ListenHub CLI：播客 + TTS + 解说视频 | v1.0 |
| [lovart-api](./lovart-api/) | Lovart AI：图片/视频/音乐生成 + 项目管理 | v1.0 |

## 工具链关系

```
ai-music-producer (编排层)
├── tuzi-api (底层: Chat / Image / Suno)
├── scene2lyric (歌词精修)
├── lyric-qa (歌词质检)
├── music-prompt-templates (提示词模板)
├── bozo-aigc (封面生成回退)
└── listenhub (播客/TTS)

material-writing (独立系统)
└── 6 Agent: 资料解析→提问→扩展→结构→写作→成稿
```

## License

MIT
