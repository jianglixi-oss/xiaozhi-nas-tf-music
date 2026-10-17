# Waveshare ESP32-S3-AUDIO-Board：NAS / TF 音乐改造

基于官方 v2.5.2，提交 `49b4380b3faa0ceadd28a3e78aaf0f311c46c57e`。
仍使用 xiaozhi.me 官方服务器。新增功能只在 `esp32-s3-audio-board-music` 变体启用。

## 当前范围

- NAS：云端 MCP 按文件名搜索 MP3，返回 15 分钟有效地址，再调用设备 `self.music.play_url`。
- TF：FAT32 卡根目录创建 `music` 文件夹，放入 MP3；支持最多四层子目录，索引上限 1000 首。
- 设备：MP3 解码、立体声混为单声道、重采样到现有音频驱动采样率（24kHz），共用 AudioService 输出队列。
- 搜歌、播放、停止、现有音量工具；唤醒或按 BOOT 结束音乐并回到对话。
- 暂未实现暂停续播、自动连续播放、上下首、进度跳转、FLAC/AAC、歌词、飞牛音乐收藏/歌单接口。
- TF 文件播放本身无需 NAS，语音点歌仍依赖官方云端。未增加离线按键点歌。
- 此工程必须编译通过并在真实硬件上测试后，才能认定功能可用。

## 硬件

微雪原理图 v1.1：SD CLK=GPIO40、D0=GPIO41、CMD=GPIO42，使用 SDMMC 1-bit。
DAT3 由 TCA9555 P03 拉高。LCD SPI 和音频 I2S 引脚保持官方设置。
卡挂载失败只返回错误，绝不格式化。
来源：https://files.waveshare.com/wiki/ESP32-S3-AUDIO-Board/ESP32-S3-AUDIO-Board_1.1.pdf

## 编译环境

此源码明确要求 ESP-IDF >=6.0.1，推荐 6.1，不能使用旧版 5.x 教程。
VS Code 安装 Espressif 官方 `ESP-IDF` 扩展（`espressif.esp-idf-extension`）。
通过扩展选择本机 ESP-IDF 6.1，打开本工程文件夹。
也可以在 ESP-IDF PowerShell 中执行：

```powershell
./build-music.ps1
# 或在已激活的 ESP-IDF 环境中：
python scripts/build.py waveshare/esp32-s3-audio-board --name esp32-s3-audio-board-music --zip
```

Windows 可直接使用官方 ESP-IDF 终端。`enter-idf.ps1` 是可选的短路径辅助脚本，
需要在工程上一级安装 `esp-idf-v6.1` 和 `esp-tools`，并使用空闲 Q: 盘符。
其他安装布局请使用自行激活的 IDF 环境执行上述 Python 编译命令。

音乐变体禁用自动安装官方 OTA 固件，避免音乐功能被原版覆盖；
官方激活及版本检查仍保留，后续固件升级需使用专用音乐版本。

需要切换屏幕时，在 menuconfig 选择原板对应的 JD9853 或 ST7789；默认沿用官方 JD9853。
在烧录前先备份当前 Flash 和对应原厂固件。本文不提供未经编译验证的烧录地址。
不要把其他 Waveshare 型号的二进制刷进此板。

## NAS 服务

无需更改飞牛音乐设置，直接挂载它使用的同一音乐文件夹。当前仅索引 MP3 文件名，
建议命名为 `歌手 - 歌名.mp3`；不会读取或改写飞牛音乐数据库。

1. 把 `nas-music` 目录放到 NAS 的 Docker 项目目录。
2. 复制 `.env.example` 为 `.env`。
3. 填入官方 MCP 接入点、实际音乐目录、NAS 内网 IP 和随机签名密钥。
4. NAS Docker 中执行 `docker compose up -d --build`。
5. NAS 防火墙允许小智设备访问 TCP 8765；设备与 NAS 应在可互通的网络。

容器用户 UID=10001，需对音乐目录有读取权限。目录以只读方式挂载。
HTTP 只用于局域网，URL 签名仍属于短期凭据。请勿把端口直接暴露到公网。

小智角色说明中可加入：

```text
播放 NAS 音乐时，先调用 nas_music_search，按用户指定的歌手和版本选择结果，
再调用结果中的 self.music.play_url，原样传入 device_arguments。
播放 TF 卡音乐时，先 self.music.tf_search，再 self.music.tf_play。
TF 曲库在后台索引，首次开机可等待几秒；曲库变化后调用 self.music.tf_refresh。
停止音乐使用 self.music.stop。不要把排队成功说成已经播放成功。
```

`mcp_pipe.py` 来自 https://github.com/78/mcp-calculator ，沿用官方主动 WebSocket 接入模式。
NAS 搜歌不需要开放 NAS 管理端口，也不需要提供飞牛账号密码。

## 真机验收

1. 原有聊天、麦克风、音量、屏幕和唤醒正常。
2. TF 空卡、未插卡、错误文件、中文路径均给出合理结果，不重启、不格式化。
3. TF 和 NAS 各播放一首 44.1kHz 立体声 MP3，持续五分钟。
4. 播放中唤醒、按 BOOT、停止、切换来源，确认没有双重输出和任务泄漏。
5. NAS 断网、签名过期、HTTP 404、损坏 MP3、TF 读取失败后仍可继续对话。
6. WebSocket 和 MQTT/UDP 官方连接都需验证；远程 MCP 与设备 MCP 的连续调用需实测。

## 验证记录

- NAS 曲库/签名/过期/刷新：4 项主机测试通过。
- 真实本地 MCP 握手、工具发现、搜歌、HTTP 签名下载和篡改拒绝：1 项联调测试通过。
- MP3 模块已使用真实 ESP32-S3 编译器和实际依赖头文件通过语法检查。
- 上游 110 项主机测试：103 通过、1 跳过、6 环境错误（5 项 Windows 当前目录被占用导致清理失败；1 项缺少主机 C++ 编译器）。
- 全部 6 个修改的 C++ 模块已通过完整工程参数下的语法检查。
- ESP-IDF 6.1 完整编译、链接、合并及 ZIP 打包通过，构建命令返回 0。
- 应用大小 `0x2f7420`，应用分区 `0x3f0000`，约 25% 空间剩余。
- 固件 ZIP 与 NAS ZIP 的完整性校验通过。
- 2026-10-17：用户已烧录，并确认 TF 卡播放和飞牛 NAS 语音点歌通过；NAS 服务已连接官方 MCP。
- 其余验收清单尚未逐项验证，不代表所有板型、卡容量和网络模式均已覆盖。

交付文件：

- `releases/xiaozhi-nas-tf-music-v0.1.0-waveshare-jd9853.zip`：内含 `merged-binary.bin`，合并镜像起始地址为 `0x0`。
- `releases/xiaozhi-nas-tf-music-v0.1.0-nas.zip`：NAS 端源码与 Docker 部署配置，不含账号或 token。
- `releases/SHA256SUMS.txt`：两个压缩包的 SHA-256 校验值。

固件保持官方默认 JD9853 屏幕变体；ST7789 屏幕需要选择对应配置后重新编译。
首次刷写前备份当前固件及 Flash。合并镜像刷写可能覆盖配网/绑定等持久化数据。
