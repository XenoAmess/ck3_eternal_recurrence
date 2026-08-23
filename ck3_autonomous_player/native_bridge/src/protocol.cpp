#include "xar_bridge/protocol.hpp"

#include <array>
#include <limits>
#include <utility>
#include <vector>

namespace xar::bridge {
namespace {

std::array<std::byte, 4> EncodeLength(std::uint32_t value) noexcept {
  return {
      std::byte(value & 0xffU),
      std::byte((value >> 8U) & 0xffU),
      std::byte((value >> 16U) & 0xffU),
      std::byte((value >> 24U) & 0xffU),
  };
}

std::uint32_t DecodeLength(const std::byte* bytes) noexcept {
  return static_cast<std::uint32_t>(bytes[0]) |
         (static_cast<std::uint32_t>(bytes[1]) << 8U) |
         (static_cast<std::uint32_t>(bytes[2]) << 16U) |
         (static_cast<std::uint32_t>(bytes[3]) << 24U);
}

bool WriteAll(HANDLE pipe, const void* data, std::size_t size) noexcept {
  const auto* cursor = static_cast<const std::byte*>(data);
  while (size != 0U) {
    const auto chunk = static_cast<DWORD>(
        size > static_cast<std::size_t>((std::numeric_limits<DWORD>::max)())
            ? (std::numeric_limits<DWORD>::max)()
            : size);
    DWORD written = 0;
    if (!WriteFile(pipe, cursor, chunk, &written, nullptr) || written == 0U) {
      return false;
    }
    cursor += written;
    size -= written;
  }
  return true;
}

bool ReadAll(HANDLE pipe, void* data, std::size_t size, DWORD& error) noexcept {
  auto* cursor = static_cast<std::byte*>(data);
  while (size != 0U) {
    const auto chunk = static_cast<DWORD>(
        size > static_cast<std::size_t>((std::numeric_limits<DWORD>::max)())
            ? (std::numeric_limits<DWORD>::max)()
            : size);
    DWORD read = 0;
    if (!ReadFile(pipe, cursor, chunk, &read, nullptr) || read == 0U) {
      error = GetLastError();
      return false;
    }
    cursor += read;
    size -= read;
  }
  error = ERROR_SUCCESS;
  return true;
}

}  // namespace

bool WriteFrame(HANDLE pipe, std::string_view payload) noexcept {
  if (pipe == nullptr || pipe == INVALID_HANDLE_VALUE || payload.empty() ||
      payload.size() > kMaximumFrameBytes) {
    return false;
  }
  const auto header = EncodeLength(static_cast<std::uint32_t>(payload.size()));
  return WriteAll(pipe, header.data(), header.size()) &&
         WriteAll(pipe, payload.data(), payload.size());
}

ReadResult TryReadFrame(HANDLE pipe) noexcept {
  if (pipe == nullptr || pipe == INVALID_HANDLE_VALUE) {
    return {ReadStatus::closed, {}, ERROR_INVALID_HANDLE};
  }

  std::array<std::byte, 4> header{};
  DWORD header_bytes = 0;
  DWORD total_available = 0;
  if (!PeekNamedPipe(pipe, header.data(), static_cast<DWORD>(header.size()),
                     &header_bytes, &total_available, nullptr)) {
    const DWORD error = GetLastError();
    return {ReadStatus::closed, {}, error};
  }
  if (total_available < header.size() || header_bytes < header.size()) {
    return {};
  }

  const std::uint32_t payload_size = DecodeLength(header.data());
  if (payload_size == 0U || payload_size > kMaximumFrameBytes) {
    return {ReadStatus::invalid, {}, ERROR_INVALID_DATA};
  }
  const auto frame_size = static_cast<std::uint64_t>(header.size()) + payload_size;
  if (static_cast<std::uint64_t>(total_available) < frame_size) {
    return {};
  }

  std::array<std::byte, 4> consumed_header{};
  DWORD error = ERROR_SUCCESS;
  if (!ReadAll(pipe, consumed_header.data(), consumed_header.size(), error)) {
    return {ReadStatus::closed, {}, error};
  }
  if (DecodeLength(consumed_header.data()) != payload_size) {
    return {ReadStatus::invalid, {}, ERROR_INVALID_DATA};
  }

  std::string payload(payload_size, '\0');
  if (!ReadAll(pipe, payload.data(), payload.size(), error)) {
    return {ReadStatus::closed, {}, error};
  }
  return {ReadStatus::frame, std::move(payload), ERROR_SUCCESS};
}

}  // namespace xar::bridge
