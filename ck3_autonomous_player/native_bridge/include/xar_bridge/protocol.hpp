#pragma once

#include <windows.h>

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::uint32_t kProtocolVersion = 1;
inline constexpr std::uint32_t kMaximumFrameBytes = 1024U * 1024U;

enum class ReadStatus {
  none,
  frame,
  closed,
  invalid,
};

struct ReadResult {
  ReadStatus status = ReadStatus::none;
  std::string payload;
  DWORD windows_error = ERROR_SUCCESS;
};

// The transport is a little-endian uint32 byte count followed by one compact
// UTF-8 JSON document. It deliberately is not MCP: the external daemon owns
// MCP and translates its typed tools to this small process-local protocol.
bool WriteFrame(HANDLE pipe, std::string_view payload) noexcept;

// Non-blocking probe. A complete frame is consumed only when all of its bytes
// are already available in the pipe.
ReadResult TryReadFrame(HANDLE pipe) noexcept;

}  // namespace xar::bridge
