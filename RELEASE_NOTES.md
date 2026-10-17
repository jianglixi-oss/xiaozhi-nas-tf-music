# v0.1.0：NAS 与 TF 音乐首版

为 Waveshare ESP32-S3-AUDIO-Board 增加 NAS MP3 点歌与 TF MP3 播放，继续使用 xiaozhi.me 官方服务器。用户已确认两种播放通过。

## 下载

- `xiaozhi-nas-tf-music-v0.1.0-waveshare-jd9853.zip`：固件合并镜像，解压后 `merged-binary.bin` 烧录地址 **0x0**。
- `xiaozhi-nas-tf-music-v0.1.0-nas.zip`：NAS MCP 源码与 Docker 部署文件，不含真实凭据。
- `SHA256SUMS.txt`：附件 SHA-256 校验值。

固件仅用于 Waveshare ESP32-S3-AUDIO-Board、默认 JD9853 屏幕。其他型号或 ST7789 屏幕需重新编译。烧录前备份 Flash；合并镜像可能覆盖配网和绑定数据。

TF 使用 FAT32，根目录 `/music` 放入 MP3。NAS 配置步骤与工具调用提示见 README。原版固件不含设备音乐工具，需安装本音乐固件。

基础固件 v2.5.2，项目发布版本 v0.1.0；关闭自动安装官方 OTA，后续手动升级专用固件。

当前不支持 FLAC/AAC、暂停续播、上下首、自动连播和飞牛音乐歌单。实际设备测试由用户完成；其他硬件、屏幕变体及完整异常场景尚未逐项验收。

NAS 自动化测试 5 项通过；固件 ESP-IDF 6.1 完整构建通过。上游主机测试既有记录为 103 通过、1 跳过、6 个 Windows/主机工具环境错误。详见 MUSIC_SETUP.md。
