#include "xar_bridge/ck3_12003_spiritual_fulfillment_progress.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::fulfillment_progress12003 {
namespace {
template <typename T> T Load(const void *source, std::size_t offset = 0) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(source) + offset, sizeof(value));
  return value;
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value.has_value() ? std::to_string(*value) : "null";
}
std::string Bool(const std::optional<bool> &value) {
  return value.has_value() ? *value ? "true" : "false" : "null";
}
} // namespace

Bindings BindSpiritualFulfillmentProgressImage12003(
    std::uintptr_t base, const game::AdapterDescriptor &descriptor) noexcept {
  Bindings out;
  if (base == 0 || !game::IsCk3_12003Descriptor(descriptor)) return out;
  out.enabled = true;
  out.database_slot = reinterpret_cast<void **>(base + kDatabaseSlotRva);
  out.type_for_character = reinterpret_cast<TypeForCharacter>(base + kTypeForCharacterRva);
  out.level_for_value = reinterpret_cast<LevelForValue>(base + kLevelForValueRva);
  out.progress_within_level = reinterpret_cast<ProgressWithinLevel>(base + kProgressWithinLevelRva);
  out.minimum = reinterpret_cast<const std::int64_t *>(base + kMinimumSlotRva);
  out.maximum = reinterpret_cast<const std::int64_t *>(base + kMaximumSlotRva);
  return out;
}
bool ReadPlayerSpiritualFulfillmentProgress12003(const Bindings &b,
    void *actor, const religion::Context &current, Progress &out) noexcept {
  out = {};
  out.capture_epoch = current.capture_epoch;
  out.date_raw = current.date_raw;
  out.played_character_id = current.played_character_id;
  if (!b.enabled || b.database_slot == nullptr || b.type_for_character == nullptr ||
      b.level_for_value == nullptr || b.progress_within_level == nullptr ||
      b.minimum == nullptr || b.maximum == nullptr) return false;
  if (!current.available || !current.spiritual_fulfillment_raw.has_value()) {
    out.failure = Failure::current_context_unavailable; return false;
  }
  if (actor == nullptr || Load<std::int32_t>(actor, 0x18) != current.played_character_id) {
    out.failure = Failure::played_character_mismatch; return false;
  }
  auto *database = Load<void *>(b.database_slot);
  if (database == nullptr) { out.failure = Failure::database_unavailable; return false; }
  auto *type = b.type_for_character(database, actor);
  if (type == nullptr) { out.failure = Failure::type_unavailable; return false; }
  const auto count = Load<std::int32_t>(type, kTypeLevelCountOffset);
  const auto *rows = Load<const std::byte *>(type, kTypeLevelRowsOffset);
  if (count <= 0 || rows == nullptr) { out.failure = Failure::levels_unavailable; return false; }
  const auto value = *current.spiritual_fulfillment_raw;
  auto *level = b.level_for_value(type, value);
  if (level == nullptr) { out.failure = Failure::level_unavailable; return false; }
  const auto index = Load<std::int32_t>(level, kLevelIndexOffset);
  const auto lower = Load<std::int64_t>(level, kLevelLowerBoundOffset);
  const auto upper = Load<std::int64_t>(level, kLevelUpperBoundOffset);
  const auto *last = rows + static_cast<std::size_t>(count - 1) * kLevelStride;
  const bool highest = index == Load<std::int32_t>(last, kLevelIndexOffset);
  // Mirrors the observed GUI value path's highest-level branch; ordinary
  // intervals delegate to the exact native arithmetic, including zero width.
  std::int64_t progress = 10'000'000;
  if (!highest && b.progress_within_level(&progress, value, lower, upper) != &progress) {
    out.failure = Failure::progress_unavailable; return false;
  }
  out.current_fulfillment_raw = value;
  out.active_level_index = index;
  out.level_count = count;
  out.level_lower_bound_raw = lower;
  out.level_upper_bound_raw = upper;
  out.progress_percent_raw = progress;
  out.highest_level = highest;
  out.runtime_minimum_raw = Load<std::int64_t>(b.minimum);
  out.runtime_maximum_raw = Load<std::int64_t>(b.maximum);
  out.available = true;
  out.failure = Failure::none;
  return true;
}
const char *SpiritualFulfillmentProgressFailureName12003(Failure value) noexcept {
  switch (value) {
  case Failure::none: return "none";
  case Failure::current_context_unavailable: return "current_context_unavailable";
  case Failure::played_character_mismatch: return "played_character_mismatch";
  case Failure::database_unavailable: return "database_unavailable";
  case Failure::type_unavailable: return "type_unavailable";
  case Failure::levels_unavailable: return "levels_unavailable";
  case Failure::level_unavailable: return "level_unavailable";
  case Failure::progress_unavailable: return "progress_unavailable";
  default: return "bindings_unavailable";
  }
}
std::string SerializeSpiritualFulfillmentProgress12003(const Progress &p) {
  return std::string{"{\"schema\":\"ck3_12003_spiritual_fulfillment_progress_v1\",\"read_only\":true,\"available\":"} +
      (p.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (p.available ? std::string{"null"} : std::string{"\""} + SpiritualFulfillmentProgressFailureName12003(p.failure) + "\"") +
      ",\"capture_epoch\":" + std::to_string(p.capture_epoch) +
      ",\"date_raw\":" + std::to_string(p.date_raw) +
      ",\"played_character_id\":" + std::to_string(p.played_character_id) +
      ",\"current_fulfillment_raw\":" + Number(p.current_fulfillment_raw) +
      ",\"active_level_index\":" + Number(p.active_level_index) +
      ",\"level_count\":" + Number(p.level_count) +
      ",\"level_lower_bound_raw\":" + Number(p.level_lower_bound_raw) +
      ",\"level_upper_bound_raw\":" + Number(p.level_upper_bound_raw) +
      ",\"progress_percent_raw\":" + Number(p.progress_percent_raw) +
      ",\"highest_level\":" + Bool(p.highest_level) +
      ",\"runtime_minimum_raw\":" + Number(p.runtime_minimum_raw) +
      ",\"runtime_maximum_raw\":" + Number(p.runtime_maximum_raw) +
      ",\"raw_scale\":100000,\"progress_unit\":\"percent\",\"is_monthly_change\":false}";
}
} // namespace xar::ck3_12002::religion::fulfillment_progress12003
