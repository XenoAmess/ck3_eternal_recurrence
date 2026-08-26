#include "xar_bridge/event_window_context_v1.hpp"

#include "xar_bridge/ck3_11906.hpp"

#include <algorithm>
#include <charconv>
#include <cstddef>
#include <cstring>
#include <limits>
#include <string_view>
#include <utility>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kIdlerFromOwnerOffset = 0x10;
constexpr std::size_t kManagerFromIdlerOffset = 0x28;
constexpr std::size_t kManagerWindowDataOffset = 0x10;
constexpr std::size_t kManagerWindowCountOffset = 0x1C;
constexpr std::size_t kWindowDataOffset = 0xE8;
constexpr std::size_t kDataInstanceIdOffset = 0x00;
constexpr std::size_t kDataOptionDataOffset = 0x10;
constexpr std::size_t kDataOptionCapacityOffset = 0x18;
constexpr std::size_t kDataOptionCountOffset = 0x1C;
constexpr std::size_t kDataCancelOptionIndexOffset = 0x2C;
constexpr std::size_t kOptionStride = 0x1B8;
constexpr std::size_t kOptionOwnerOffset = 0x160;
constexpr std::size_t kOptionNameOffset = 0x170;
constexpr std::size_t kOptionReasonOffset = 0x190;
constexpr std::size_t kOptionNativeIndexOffset = 0x1B0;
constexpr std::size_t kOptionEnabledOffset = 0x1B4;
constexpr std::size_t kOptionFallbackOffset = 0x1B5;
constexpr std::size_t kMaximumWindows = 32;
constexpr std::size_t kMaximumOptions = 64;
constexpr std::size_t kMaximumStringBytes = 16'384;

template <typename T>
T LoadAt(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset,
              sizeof(value));
  return value;
}

void SetUnavailable(game::EventWindowContextV1 &output,
                    std::string_view reason) {
  const auto revision = output.snapshot_revision;
  const auto date_raw = output.date_raw;
  const auto event_id = output.current_event_instance_id;
  const auto matches = output.window_match_count;
  output = {};
  output.snapshot_revision = revision;
  output.date_raw = date_raw;
  output.current_event_instance_id = event_id;
  output.window_match_count = matches;
  output.unavailable_reason.assign(reason);
}

bool ReadNativeString(const void *object, std::string &output) {
  output.clear();
  if (object == nullptr) {
    return false;
  }
  const auto size = LoadAt<std::uint64_t>(object, 0x10);
  const auto capacity = LoadAt<std::uint64_t>(object, 0x18);
  if (size > kMaximumStringBytes || capacity < size) {
    return false;
  }
  const void *data = object;
  if (capacity >= 16) {
    data = LoadAt<const void *>(object, 0x00);
  }
  if (size != 0 && data == nullptr) {
    return false;
  }
  try {
    output.assign(static_cast<const char *>(data),
                  static_cast<std::size_t>(size));
  } catch (...) {
    output.clear();
    return false;
  }
  return true;
}

bool ValidVector(std::int32_t count, std::int32_t capacity,
                 std::size_t maximum, const void *data) noexcept {
  return count >= 0 && capacity >= count &&
         capacity <= static_cast<std::int32_t>(maximum) &&
         (count == 0 || data != nullptr);
}

bool ReadMatchingWindow(const Bindings &bindings, void *window,
                        std::int32_t expected_event_id,
                        game::EventWindowContextV1 &candidate) {
  if (window == nullptr ||
      LoadAt<std::uintptr_t>(window, 0) !=
          bindings.event_window_primary_vtable) {
    return false;
  }
  auto *const data = static_cast<std::byte *>(window) + kWindowDataOffset;
  if (LoadAt<std::int32_t>(data, kDataInstanceIdOffset) !=
      expected_event_id) {
    return true;
  }
  ++candidate.window_match_count;
  if (candidate.window_match_count != 1) {
    return true;
  }
  void *const items = LoadAt<void *>(data, kDataOptionDataOffset);
  const auto count = LoadAt<std::int32_t>(data, kDataOptionCountOffset);
  const auto capacity = LoadAt<std::int32_t>(
      data, kDataOptionCapacityOffset);
  if (!ValidVector(count, capacity, kMaximumOptions, items)) {
    return false;
  }
  const auto cancel_index =
      LoadAt<std::int32_t>(data, kDataCancelOptionIndexOffset);
  try {
    candidate.options.clear();
    candidate.options.reserve(static_cast<std::size_t>(count));
  } catch (...) {
    return false;
  }
  for (std::int32_t rendered = 0; rendered < count; ++rendered) {
    const auto offset = static_cast<std::size_t>(rendered) * kOptionStride;
    auto *const item = static_cast<std::byte *>(items) + offset;
    if (LoadAt<void *>(item, kOptionOwnerOffset) != data) {
      return false;
    }
    const auto enabled = LoadAt<std::uint8_t>(item, kOptionEnabledOffset);
    const auto fallback = LoadAt<std::uint8_t>(item, kOptionFallbackOffset);
    if (enabled > 1 || fallback > 1) {
      return false;
    }
    game::EventWindowOptionV1 option{};
    option.rendered_index = rendered;
    option.native_option_index =
        LoadAt<std::int32_t>(item, kOptionNativeIndexOffset);
    option.shown = true;
    option.enabled = enabled != 0;
    option.fallback = fallback != 0;
    option.cancel = option.native_option_index == cancel_index;
    const bool duplicate_native_index = std::any_of(
        candidate.options.begin(), candidate.options.end(),
        [&option](const game::EventWindowOptionV1 &existing) {
          return existing.native_option_index == option.native_option_index;
        });
    if (option.native_option_index < 0 || duplicate_native_index ||
        !ReadNativeString(item + kOptionNameOffset,
                          option.resolved_name) ||
        !ReadNativeString(item + kOptionReasonOffset,
                          option.unavailable_reason)) {
      return false;
    }
    try {
      candidate.options.push_back(std::move(option));
    } catch (...) {
      return false;
    }
  }
  return true;
}

template <typename T>
bool ParsePositiveField(std::string_view json, std::string_view key,
                        T &output) noexcept {
  const auto first = json.find(key);
  if (first == std::string_view::npos ||
      json.find(key, first + key.size()) != std::string_view::npos) {
    return false;
  }
  auto begin = first + key.size();
  while (begin < json.size() && (json[begin] == ' ' || json[begin] == '\t')) {
    ++begin;
  }
  if (begin >= json.size() || json[begin] < '1' || json[begin] > '9') {
    return false;
  }
  auto end = begin;
  while (end < json.size() && json[end] >= '0' && json[end] <= '9') {
    ++end;
  }
  T value{};
  const auto parsed = std::from_chars(json.data() + begin,
                                      json.data() + end, value);
  if (parsed.ec != std::errc{} || parsed.ptr != json.data() + end ||
      value <= 0) {
    return false;
  }
  output = value;
  return true;
}

} // namespace

game::ReadEventWindowContextResultV1 ReadEventWindowContextV1(
    const Bindings &bindings, std::uint64_t expected_snapshot_revision,
    std::int32_t expected_event_instance_id,
    game::EventWindowContextV1 &output) noexcept {
  output = {};
  output.snapshot_revision = expected_snapshot_revision;
  output.current_event_instance_id = expected_event_instance_id;
  try {
    if (!bindings.enabled || expected_snapshot_revision == 0 ||
        expected_event_instance_id <= 0 ||
        bindings.jomini_state_slot == nullptr ||
        bindings.ingame_interface_idler_vtable == 0 ||
        bindings.event_window_primary_vtable == 0) {
      SetUnavailable(output, "unsupported_build");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    game::Snapshot before{};
    if (!ReadSnapshot(bindings, before) || !before.paused ||
        !before.map_ready || !before.has_active_event ||
        before.active_event_instance_id != expected_event_instance_id) {
      SetUnavailable(output, "state_changed");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    output.date_raw = before.date_raw;
    void *const owner = *bindings.jomini_state_slot;
    void *const idler = owner != nullptr
                            ? LoadAt<void *>(owner, kIdlerFromOwnerOffset)
                            : nullptr;
    if (idler == nullptr ||
        LoadAt<std::uintptr_t>(idler, 0) !=
            bindings.ingame_interface_idler_vtable) {
      SetUnavailable(output, "ingame_idler_unavailable");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    void *const manager =
        LoadAt<void *>(idler, kManagerFromIdlerOffset);
    if (manager == nullptr) {
      SetUnavailable(output, "event_window_manager_unavailable");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    void *const windows =
        LoadAt<void *>(manager, kManagerWindowDataOffset);
    const auto count =
        LoadAt<std::int32_t>(manager, kManagerWindowCountOffset);
    if (count < 0 || count > static_cast<std::int32_t>(kMaximumWindows) ||
        (count != 0 && windows == nullptr)) {
      SetUnavailable(output, "event_window_vector_invalid");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    game::EventWindowContextV1 candidate = output;
    for (std::int32_t index = 0; index < count; ++index) {
      void *const window = LoadAt<void *>(
          windows, static_cast<std::size_t>(index) * sizeof(void *));
      if (!ReadMatchingWindow(bindings, window,
                              expected_event_instance_id, candidate)) {
        SetUnavailable(output, "event_window_layout_invalid");
        return game::ReadEventWindowContextResultV1::unavailable;
      }
    }
    output.window_match_count = candidate.window_match_count;
    if (candidate.window_match_count != 1) {
      SetUnavailable(output, candidate.window_match_count == 0
                                 ? "event_window_not_materialized"
                                 : "event_window_ambiguous");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    game::Snapshot after{};
    if (!ReadSnapshot(bindings, after) || after != before) {
      SetUnavailable(output, "state_changed");
      return game::ReadEventWindowContextResultV1::unavailable;
    }
    candidate.status = game::EventWindowContextStatusV1::available;
    candidate.unavailable_reason.clear();
    candidate.option_presentation_ready = true;
    candidate.effect_preview_ready = false;
    candidate.semantic_decision_ready = false;
    output = std::move(candidate);
    return game::ReadEventWindowContextResultV1::available;
  } catch (...) {
    SetUnavailable(output, "internal_error");
    return game::ReadEventWindowContextResultV1::unavailable;
  }
}

bool ParseEventWindowContextRequestV1(
    std::string_view json, std::uint64_t &expected_revision,
    std::int32_t &event_instance_id) noexcept {
  expected_revision = 0;
  event_instance_id = -1;
  return ParsePositiveField(json, "\"expected_revision\":",
                            expected_revision) &&
         ParsePositiveField(json, "\"event_instance_id\":",
                            event_instance_id);
}

} // namespace xar::ck3_11906
