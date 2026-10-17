#include "music_stream.h"

#include <algorithm>
#include <array>
#include <cstring>
#include "esp_ae_rate_cvt.h"
#include "esp_mp3_dec.h"

bool DecodeMusicMp3(const std::function<int(uint8_t*, size_t)>& read,
                    const std::function<bool()>& cancelled, int output_rate,
                    const std::function<bool(std::vector<int16_t>&&)>& sink) {
    void* decoder = nullptr;
    if (esp_mp3_dec_open(nullptr, 0, &decoder) != ESP_AUDIO_ERR_OK)
        return false;
    esp_ae_rate_cvt_handle_t resampler = nullptr;
    int previous_rate = 0;
    std::array<uint8_t, 8192> input;
    std::vector<int16_t> decoded(2304);
    size_t buffered = 0;
    bool eof = false, ok = true, had_audio = false;
    // ID3v2 tags can be much larger than the decode buffer. Skip incrementally.
    int first = read(input.data(), 10);
    while (first > 0 && first < 10) {
        int n = read(input.data() + first, 10 - first);
        if (n <= 0) {
            first = -1;
            break;
        }
        first += n;
    }
    if (first == 10 && std::memcmp(input.data(), "ID3", 3) == 0) {
        uint32_t skip = 0;
        for (int i = 6; i < 10; ++i) {
            if (input[i] & 0x80) {
                ok = false;
                break;
            }
            skip = (skip << 7) | input[i];
        }
        if (input[5] & 0x10)
            skip += 10;  // optional ID3 footer
        while (ok && skip && !cancelled()) {
            int n = read(input.data(), std::min<size_t>(skip, input.size()));
            if (n <= 0) {
                ok = false;
                break;
            }
            skip -= n;
        }
    } else if (first == 10) {
        buffered = 10;
    } else {
        ok = false;
    }
    while (ok && !cancelled()) {
        while (!eof && buffered < input.size() && !cancelled()) {
            int n = read(input.data() + buffered, input.size() - buffered);
            if (n < 0) {
                ok = false;
                break;
            }
            eof = n == 0;
            buffered += n;
        }
        if (!ok || cancelled())
            break;
        if (buffered == 0)
            break;
        if (eof && buffered == 128 && std::memcmp(input.data(), "TAG", 3) == 0)
            break;
        esp_audio_dec_in_raw_t raw = {};
        raw.buffer = input.data();
        raw.len = buffered;
        esp_audio_dec_out_frame_t frame = {};
        frame.buffer = reinterpret_cast<uint8_t*>(decoded.data());
        frame.len = decoded.size() * sizeof(int16_t);
        esp_audio_dec_info_t info = {};
        auto err = esp_mp3_dec_decode(decoder, &raw, &frame, &info);
        if (raw.consumed > buffered) {
            ok = false;
            break;
        }
        buffered -= raw.consumed;
        std::memmove(input.data(), input.data() + raw.consumed, buffered);
        if (err != ESP_AUDIO_ERR_OK) {
            ok = false;
            break;
        }
        if (frame.decoded_size) {
            if (info.bits_per_sample != 16 || info.channel < 1 || info.channel > 2 ||
                info.sample_rate < 8000 || info.sample_rate > 48000) {
                ok = false;
                break;
            }
            size_t samples = frame.decoded_size / sizeof(int16_t) / info.channel;
            std::vector<int16_t> mono(samples);
            for (size_t i = 0; i < samples; ++i) {
                int sum = decoded[i * info.channel];
                if (info.channel == 2)
                    sum += decoded[i * 2 + 1];
                mono[i] = sum / info.channel;
            }
            if (previous_rate != static_cast<int>(info.sample_rate)) {
                if (resampler) {
                    esp_ae_rate_cvt_close(resampler);
                    resampler = nullptr;
                }
                previous_rate = info.sample_rate;
                if (previous_rate != output_rate) {
                    esp_ae_rate_cvt_cfg_t cfg = {};
                    cfg.src_rate = previous_rate;
                    cfg.dest_rate = output_rate;
                    cfg.channel = 1;
                    cfg.bits_per_sample = 16;
                    cfg.complexity = 2;
                    cfg.perf_type = ESP_AE_RATE_CVT_PERF_TYPE_SPEED;
                    if (esp_ae_rate_cvt_open(&cfg, &resampler) != ESP_AE_ERR_OK) {
                        ok = false;
                        break;
                    }
                }
            }
            if (resampler) {
                uint32_t capacity = 0;
                esp_ae_rate_cvt_get_max_out_sample_num(resampler, samples, &capacity);
                std::vector<int16_t> converted(capacity);
                if (esp_ae_rate_cvt_process(resampler,
                                            reinterpret_cast<esp_ae_sample_t>(mono.data()), samples,
                                            reinterpret_cast<esp_ae_sample_t>(converted.data()),
                                            &capacity) != ESP_AE_ERR_OK) {
                    ok = false;
                    break;
                }
                converted.resize(capacity);
                mono = std::move(converted);
            }
            had_audio = true;
            if (!mono.empty() && !sink(std::move(mono))) {
                ok = false;
                break;
            }
        }
        if (raw.consumed == 0 && frame.decoded_size == 0) {
            if (eof || buffered == input.size()) {
                ok = false;
                break;
            }
        }
    }
    if (resampler)
        esp_ae_rate_cvt_close(resampler);
    esp_mp3_dec_close(decoder);
    return ok && had_audio && !cancelled();
}
