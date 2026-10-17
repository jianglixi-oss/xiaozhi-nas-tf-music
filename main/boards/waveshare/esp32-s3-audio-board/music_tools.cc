#include "sdkconfig.h"
#ifdef CONFIG_WAVESHARE_NAS_TF_MUSIC

#include <dirent.h>
#include <sys/stat.h>
#include <algorithm>
#include <cctype>
#include <mutex>
#include <string>
#include <vector>
#include "application.h"
#include "driver/sdmmc_host.h"
#include "esp_vfs_fat.h"
#include "mcp_server.h"

namespace {
std::mutex card_mutex;
sdmmc_card_t* card = nullptr;
std::vector<std::string> library;
bool scanning = false;
bool ready = false;
bool library_truncated = false;

bool MountCard() {
    if (card)
        return true;
    sdmmc_host_t host = SDMMC_HOST_DEFAULT();
    host.max_freq_khz = SDMMC_FREQ_DEFAULT;
    sdmmc_slot_config_t slot = SDMMC_SLOT_CONFIG_DEFAULT();
    // Waveshare schematic v1.1: independent of LCD SPI2 and audio I2S.
    slot.clk = GPIO_NUM_40;
    slot.cmd = GPIO_NUM_42;
    slot.d0 = GPIO_NUM_41;
    slot.width = 1;
    slot.flags |= SDMMC_SLOT_FLAG_INTERNAL_PULLUP;
    esp_vfs_fat_sdmmc_mount_config_t mount = {};
    mount.format_if_mount_failed = false;  // Never format a user's music card.
    mount.max_files = 4;
    mount.allocation_unit_size = 16 * 1024;
    return esp_vfs_fat_sdmmc_mount("/sdcard", &host, &slot, &mount, &card) == ESP_OK;
}

bool ValidFile(const std::string& path) {
    if (!path.starts_with("/sdcard/music/") || path.find("..") != std::string::npos ||
        path.find('\\') != std::string::npos || path.size() > 240 || path.size() < 4)
        return false;
    std::string ext = path.substr(path.size() - 4);
    std::transform(ext.begin(), ext.end(), ext.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    struct stat st;
    return ext == ".mp3" && stat(path.c_str(), &st) == 0 && S_ISREG(st.st_mode);
}

void Scan(const std::string& directory, int depth, int& visited, std::vector<std::string>& paths,
          bool& truncated) {
    DIR* dir = opendir(directory.c_str());
    if (!dir)
        return;
    while (auto* entry = readdir(dir)) {
        if (entry->d_name[0] == '.')
            continue;
        if (++visited > 4000 || paths.size() >= 1000) {
            truncated = true;
            break;
        }
        std::string path = directory + "/" + entry->d_name;
        struct stat st;
        if (stat(path.c_str(), &st) != 0)
            continue;
        if (S_ISDIR(st.st_mode)) {
            if (depth < 4)
                Scan(path, depth + 1, visited, paths, truncated);
            else
                truncated = true;
        } else if (ValidFile(path)) {
            paths.push_back(path);
        }
        if (visited > 4000 || paths.size() >= 1000)
            break;
    }
    closedir(dir);
}

// MCP callbacks run on the application's main loop. All SD I/O must run
// on this worker; tools only query the bounded in-memory index.
bool StartScanLocked() {
    if (scanning)
        return true;
    scanning = true;
    if (xTaskCreate(
            [](void*) {
                bool mounted = MountCard();
                std::vector<std::string> paths;
                bool truncated = false;
                int visited = 0;
                if (mounted)
                    Scan("/sdcard/music", 0, visited, paths, truncated);
                std::sort(paths.begin(), paths.end());
                {
                    std::lock_guard<std::mutex> lock(card_mutex);
                    library = std::move(paths);
                    library_truncated = truncated;
                    ready = mounted;
                    scanning = false;
                }
                vTaskDelete(nullptr);
            },
            "tf_index", 6144, nullptr, 1, nullptr) != pdPASS) {
        scanning = false;
        return false;
    }
    return true;
}
}  // namespace

void InitializeAudioBoardMusicTools() {
    auto& mcp = McpServer::GetInstance();
    mcp.AddTool(
        "self.music.tf_refresh",
        "Start a background TF card rescan after inserting/changing the card.", PropertyList(),
        [](const PropertyList&) -> ToolResult {
            std::lock_guard<std::mutex> lock(card_mutex);
            if (!StartScanLocked())
                return std::unexpected("Unable to start TF scan worker");
            return std::string("TF indexing started. Query tf_search again after a few seconds.");
        });
    mcp.AddTool("self.music.status",
                "Get actual music status: idle, queued, playing, completed, failed or stopped.",
                PropertyList(), [](const PropertyList&) -> ReturnValue {
                    static const char* names[] = {"idle",      "queued", "playing",
                                                  "completed", "failed", "stopped"};
                    int status = Application::GetInstance().GetMusicStatus();
                    return std::string(names[status >= 0 && status < 6 ? status : 0]);
                });
    mcp.AddTool(
        "self.music.play_url",
        "Play an HTTP/HTTPS MP3 URL returned by the NAS music search tool. "
        "This queues playback and ends the current voice session; do not announce playback as "
        "completed.",
        PropertyList({Property("url", kPropertyTypeString).SetMaxLength(2048)}),
        [](const PropertyList& p) -> ToolResult {
            auto url = p["url"].value<std::string>();
            if ((!url.starts_with("http://") && !url.starts_with("https://")) ||
                url.find_first_of("\r\n\t ") != std::string::npos ||
                url.find('@') != std::string::npos)
                return std::unexpected("Expected HTTP/HTTPS MP3 URL without embedded credentials");
            Application::GetInstance().RequestMusic(std::move(url));
            return std::string("Playback requested; actual download/decoding may still fail.");
        });
    mcp.AddTool(
        "self.music.tf_search",
        "Search MP3 filenames under TF card /music. "
        "Returns up to 20 files. Use an empty query to browse. TF voice search needs the cloud.",
        PropertyList({Property("query", kPropertyTypeString, std::string()).SetMaxLength(120)}),
        [](const PropertyList& p) -> ToolResult {
            std::lock_guard<std::mutex> lock(card_mutex);
            if (!ready) {
                if (!StartScanLocked())
                    return std::unexpected("Unable to start TF scan worker");
                return std::string(
                    "TF not indexed. Background scan started; retry in a few seconds. Insert FAT32 "
                    "card if absent.");
            }
            auto* result = cJSON_CreateObject();
            auto* files = cJSON_AddArrayToObject(result, "files");
            bool truncated = library_truncated;
            const auto& query = p["query"].value<std::string>();
            size_t result_bytes = 0;
            for (const auto& path : library) {
                if (path.find(query) == std::string::npos)
                    continue;
                if (cJSON_GetArraySize(files) >= 20 || result_bytes + path.size() * 2 + 80 > 6000) {
                    truncated = true;
                    break;
                }
                auto* item = cJSON_CreateObject();
                cJSON_AddStringToObject(item, "name", path.substr(14).c_str());
                cJSON_AddStringToObject(item, "path", path.c_str());
                cJSON_AddItemToArray(files, item);
                result_bytes += path.size() * 2 + 80;
            }
            cJSON_AddBoolToObject(result, "truncated", truncated);
            return result;
        });
    mcp.AddTool("self.music.tf_play", "Play an MP3 path returned by self.music.tf_search.",
                PropertyList({Property("path", kPropertyTypeString).SetMaxLength(240)}),
                [](const PropertyList& p) -> ToolResult {
                    std::lock_guard<std::mutex> lock(card_mutex);
                    auto path = p["path"].value<std::string>();
                    if (!ready || std::find(library.begin(), library.end(), path) == library.end())
                        return std::unexpected("TF MP3 not indexed; search the TF library first");
                    Application::GetInstance().RequestMusic(std::move(path));
                    return std::string("TF playback requested.");
                });
    mcp.AddTool("self.music.stop", "Stop NAS or TF music and cancel any queued music request.",
                PropertyList(), [](const PropertyList&) -> ReturnValue {
                    Application::GetInstance().RequestMusicStop();
                    return std::string("Stop requested.");
                });
    std::lock_guard<std::mutex> lock(card_mutex);
    StartScanLocked();
}
#endif
