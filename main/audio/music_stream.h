#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>

// Negative read result means I/O failure; zero means EOF. The sink provides
// backpressure and returns false when playback is cancelled.
bool DecodeMusicMp3(const std::function<int(uint8_t*, size_t)>& read,
                    const std::function<bool()>& cancelled, int output_rate,
                    const std::function<bool(std::vector<int16_t>&&)>& sink);
