# 变更记录

## v0.2.0 — 2026-11-17

- 新增电台功能：NAS 端 `stations.json` 管理电台列表，`nas_radio_list`/`nas_radio_refresh` 工具列出与刷新电台，复用设备 `self.music.play_url` 播放连续流。
- 音乐解码支持 AAC（ADTS / AAC-Plus）：`DecodeMusic` 自动识别 MP3/AAC 并选用对应解码器，使蜻蜓FM 等国内电台 AAC 流可播。
- 新增 HomePod 目标查询、NAS 搜歌后通过 HA 投放、停止播放工具；绕开 HomePod 不具备 SEARCH_MEDIA 能力的限制。
- 9 项自动化测试通过；用户确认小智控制 HomePod 播放和停止均通过。

## v0.1.0 — 2026-10-17

- 基于官方小智 v2.5.2，新增 Waveshare ESP32-S3-AUDIO-Board 音乐构建变体。
- 支持 TF FAT32 `/music` MP3 搜索、播放和刷新。
- 提供 NAS MCP 搜索、刷新及短期签名 HTTP 拉流。
- 支持播放停止、状态查询，与原有语音输出协调。
- 用户确认 TF 与飞牛 NAS 点歌播放通过。
- 发布默认 JD9853 屏幕固件、NAS Docker 部署包和 SHA-256 校验值。
