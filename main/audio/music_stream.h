#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>

// Decodes MP3 or ADTS AAC from the `read` callback, resamples to `output_rate`
// and pushes mono PCM to `sink`. Negative read result means I/O failure; zero
// means EOF. The sink provides backpressure and returns false to cancel.
bool DecodeMusic(const std::function<int(uint8_t*, size_t)>& read,
                 const std::function<bool()>& cancelled, int output_rate,
                 const std::function<bool(std::vector<int16_t>&&)>& sink);
