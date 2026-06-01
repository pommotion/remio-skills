# remio 对话档案整理 · 运行参数

## 脚本路径
- 提取层脚本: `~/Library/Application Support/remio/Users/F2313D5DDFE8FCF316DC1149F06BB14B/agent/.session/整理脚本/remio_archiver.py`
- 提取结果: `extracted_sessions.json`（同目录下）

## MOC 笔记
- Remio 笔记版 MOC noteId: `mpiak8lzgsik1hgtflq`
- Obsidian 版 MOC 路径: `/Users/wanglingwei/Documents/Obsidian/09.经验沉淀/remio对话档案/MOC/MOC-对话总索引.md`

## 时间线 & 标签路径
- 时间线: `/Users/wanglingwei/Documents/Obsidian/09.经验沉淀/remio对话档案/时间线/YYYY-MM.md`
- 标签页: `/Users/wanglingwei/Documents/Obsidian/09.经验沉淀/remio对话档案/tags/{标签名}.md`

## 标签选项
AI音乐制作、定时任务、技术排障、提示词管理、aApp开发、微信群、日常对话

## Session 文件格式
```yaml
---
session_id: mp...
title: "精炼标题"
date: YYYY-MM-DD
time: HH:MM – HH:MM
message_count: N
tags: [标签1, 标签2]
---
```

## extracted_sessions.json 结构
```json
{
  "extracted_at": "...",
  "total": N,
  "sessions": [
    {
      "session_id": "mp...",
      "start_time": "...",
      "end_time": "...",
      "message_count": N,
      "first_user_message": "...",
      "user_messages": ["...", "..."],
      "tool_calls": ["..."]
    }
  ]
}
```
