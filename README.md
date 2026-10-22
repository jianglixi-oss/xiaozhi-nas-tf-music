# XiaoZhi NAS / TF Music

为 **Waveshare ESP32-S3-AUDIO-Board** 增加 NAS MP3 点歌和 TF 卡 MP3 播放，继续使用 **xiaozhi.me 官方服务器**。

基于 [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) v2.5.2（`49b4380b3faa0ceadd28a3e78aaf0f311c46c57e`）。这是社区改造版本，与小智、微雪官方无隶属关系。保留上游源码与来源信息；原说明见 [README_UPSTREAM.md](README_UPSTREAM.md)。

## 已验证

2026-10-17，用户在 Waveshare ESP32-S3-AUDIO-Board 上确认 **TF 卡播放、飞牛 NAS 语音点歌播放均通过**。NAS 端另验证了 MP3 HTTP 下载与签名拒绝。其他板型、屏幕变体、完整异常场景和所有网络模式尚未逐项验收。

## HomePod（当前主分支）

NAS MCP 可通过 Home Assistant 向配置的 HomePod 搜歌投放并停止播放，用户已于 2026-10-22 确认播放、停止通过。无需重刷板子固件。配置见 [NAS 说明](nas-music/README.md#homepod-播放可选)。HA token 只保存在私有 `.env` 中。立体声同步尚未验证。

此功能尚未包含在 v0.1.0 发布附件中，请使用当前主分支的 NAS 源码。

## 快速开始

1. 从 [Releases](https://github.com/jianglixi-oss/xiaozhi-nas-tf-music/releases) 下载固件包和 NAS 包。预编译固件仅适用于上述板型、默认 JD9853 屏幕。
2. 备份当前 Flash；解压固件包，将 `merged-binary.bin` 作为合并镜像从 **0x0** 烧录。合并烧录可能覆盖配网与绑定数据，之后按小智正常流程配网、绑定。
3. TF：使用 FAT32 文件系统，在卡根目录创建 `music`，放入 MP3。语音说“播放 TF 卡里的某某”。最多索引 1000 首、四层子目录；挂载失败不会格式化卡。容量主要受 FAT32 格式与卡兼容性影响，未验证所有容量；exFAT 不支持。
4. NAS：按 [NAS 部署说明](nas-music/README.md) 配置 MCP 接入点、音乐目录和内网 IP，启动 Docker 服务。
5. 在小智角色配置中加入下方工具调用提示，再说“从 NAS 播放某某”。

```text
播放 NAS 音乐时先调用 nas_music_search，选择用户要求的歌曲和版本，
再调用选中结果的 device_tool，原样传入 device_arguments。
播放 TF 音乐时先 self.music.tf_search，再 self.music.tf_play。
停止使用 self.music.stop，查询状态使用 self.music.status。
只有工具报告实际播放时才说明已播放，排队不代表已经出声。
```

## 工作方式与限制

- NAS MCP 按 MP3 文件名搜索；设备通过局域网 HTTP 拉流、解码并输出。签名 URL 有效期 15 分钟。
- TF 本地文件读取无需 NAS；语音指令和点歌仍依赖官方云端。
- 支持停止、现有音量控制，唤醒或 BOOT 返回对话。输出为单声道。
- 暂不支持 FLAC/AAC、暂停续播、自动连播、上下首、进度跳转、歌词。
- 直接读取共享音乐目录，不调用飞牛音乐私有 API，不读取收藏或歌单。
- 音乐变体关闭自动安装官方 OTA；后续升级需手动使用适配的音乐固件。
- 原版官方固件没有音乐设备工具，单独部署 NAS MCP 无法完成播放。

## 开发与反馈

ESP-IDF 最低 6.0.1，推荐 6.1。激活 SDK 后执行：

```sh
python scripts/build.py waveshare/esp32-s3-audio-board --name esp32-s3-audio-board-music --zip
python -m pip install -r nas-music/requirements.txt
python -m unittest discover -s nas-music -p 'test_*.py' -v
```

更完整的硬件、编译与验收说明见 [MUSIC_SETUP.md](MUSIC_SETUP.md)。反馈请使用 Issues，提交前去除 token、签名 URL、Wi-Fi 和账号信息。见 [贡献指南](CONTRIBUTING.md)、[路线图](ROADMAP.md) 和 [变更记录](CHANGELOG.md)。

## 来源与许可

沿用 [MIT 许可证](LICENSE)，保留上游版权声明。MCP 桥接程序来自 [78/mcp-calculator](https://github.com/78/mcp-calculator)，该项目 README 声明 MIT；详见 [第三方说明](THIRD_PARTY_NOTICES.md)。第三方组件各自的许可证继续适用。
