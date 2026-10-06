#pragma once

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::bridge {

enum class FrameWriteStage {
  not_started,
  handle,
  empty,
  size_limit,
  header,
  payload,
  complete,
};

struct FrameWriteDiagnostic {
  std::uint64_t payload_bytes = 0;
  std::uint64_t limit_bytes = 0;
  FrameWriteStage stage = FrameWriteStage::not_started;
  bool success = false;
  std::optional<std::uint32_t> windows_error;
};

inline std::string_view FrameWriteStageName(FrameWriteStage stage) noexcept {
  switch (stage) {
  case FrameWriteStage::not_started: return "not_started";
  case FrameWriteStage::handle: return "handle";
  case FrameWriteStage::empty: return "empty";
  case FrameWriteStage::size_limit: return "size_limit";
  case FrameWriteStage::header: return "header";
  case FrameWriteStage::payload: return "payload";
  case FrameWriteStage::complete: return "complete";
  }
  return "not_started";
}

} // namespace xar::bridge
