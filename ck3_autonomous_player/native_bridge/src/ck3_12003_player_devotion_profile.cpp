#include "xar_bridge/ck3_12003_player_devotion_profile.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::devotion_profile12003 {
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

Bindings BindPlayerDevotionProfileImage12003(
    std::uintptr_t base, const game::AdapterDescriptor &descriptor) noexcept {
  Bindings out;
  if (base == 0 || !game::IsCk3_12003Descriptor(descriptor)) return out;
  out.enabled = true;
  out.effective_level = reinterpret_cast<EffectiveLevel>(base + kEffectiveLevelRva);
  out.progress_percent = reinterpret_cast<ProgressPercent>(base + kProgressPercentRva);
  out.effective_cap = reinterpret_cast<EffectiveCap>(base + kEffectiveCapRva);
  out.threshold_progress = reinterpret_cast<ThresholdProgress>(base + kThresholdProgressRva);
  out.threshold_vector = reinterpret_cast<ThresholdVector>(base + kThresholdVectorRva);
  return out;
}

bool ReadPlayerDevotionProfile12003(const Bindings &b,
    void *actor, const religion::Context &current, Profile &out) noexcept {
  out = {};
  out.capture_epoch = current.capture_epoch;
  out.date_raw = current.date_raw;
  out.played_character_id = current.played_character_id;
  if (!b.enabled || b.effective_level == nullptr || b.progress_percent == nullptr ||
      b.effective_cap == nullptr || b.threshold_progress == nullptr ||
      b.threshold_vector == nullptr) return false;
  if (actor == nullptr ||
      Load<std::int32_t>(actor, kCharacterIdOffset) != current.played_character_id) {
    out.failure = Failure::played_character_mismatch; return false;
  }
  const auto *values = Load<const void *>(actor, kCharacterValuesOffset);
  if (values == nullptr) {
    out.failure = Failure::character_values_unavailable; return false;
  }
  PlayerValueItemScope scope{actor, 0, {}};
  const auto level = b.effective_level(actor);
  const auto cap = b.effective_cap(&scope);
  const auto *vector = b.threshold_vector(&scope);
  if (vector == nullptr) {
    out.failure = Failure::thresholds_unavailable; return false;
  }
  const auto count = Load<std::int32_t>(vector, kThresholdCountOffset);
  const auto *rows = Load<const std::byte *>(vector, kThresholdDataOffset);
  if (count < 0 || (count > 0 && rows == nullptr)) {
    out.failure = Failure::thresholds_unavailable; return false;
  }
  std::int64_t percent = 0;
  if (b.progress_percent(&percent, actor) != &percent) {
    out.failure = Failure::progress_unavailable; return false;
  }
  std::int64_t numerator = 0;
  std::int64_t denominator = 0;
  b.threshold_progress(&scope, &numerator, &denominator);
  // These comparisons are the exact native 0x26979F0 terminal branch. A cap
  // does not imply 100% progress, nor does equality with the cap imply this
  // branch. Preserve the native numerator/denominator and percent as returned.
  const bool terminal = level > cap || level >= count;
  if (!terminal && level >= 0) {
    out.level_lower_threshold_raw = level > 0
        ? Load<std::int64_t>(rows, static_cast<std::size_t>(level - 1) * kThresholdStride)
        : 0;
    out.level_upper_threshold_raw =
        Load<std::int64_t>(rows, static_cast<std::size_t>(level) * kThresholdStride);
  }
  out.current_devotion_total_raw = Load<std::int64_t>(values, kDevotionTotalOffset);
  out.effective_level = level;
  out.effective_cap = cap;
  out.progress_percent_raw = percent;
  out.progress_numerator_raw = numerator;
  out.progress_denominator_raw = denominator;
  out.runtime_threshold_count = count;
  out.native_terminal_threshold_branch = terminal;
  out.available = true;
  out.failure = Failure::none;
  return true;
}

const char *PlayerDevotionProfileFailureName12003(Failure value) noexcept {
  switch (value) {
  case Failure::none: return "none";
  case Failure::current_context_unavailable: return "current_context_unavailable";
  case Failure::played_character_mismatch: return "played_character_mismatch";
  case Failure::character_values_unavailable: return "character_values_unavailable";
  case Failure::thresholds_unavailable: return "thresholds_unavailable";
  case Failure::progress_unavailable: return "progress_unavailable";
  default: return "bindings_unavailable";
  }
}

std::string SerializePlayerDevotionProfile12003(const Profile &p) {
  return std::string{"{\"schema\":\"ck3_12003_player_devotion_profile_v1\",\"read_only\":true,\"available\":"} +
      (p.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (p.available ? std::string{"null"} : std::string{"\""} + PlayerDevotionProfileFailureName12003(p.failure) + "\"") +
      ",\"capture_epoch\":" + std::to_string(p.capture_epoch) +
      ",\"date_raw\":" + std::to_string(p.date_raw) +
      ",\"played_character_id\":" + std::to_string(p.played_character_id) +
      ",\"current_devotion_total_raw\":" + Number(p.current_devotion_total_raw) +
      ",\"effective_level\":" + Number(p.effective_level) +
      ",\"effective_cap\":" + Number(p.effective_cap) +
      ",\"progress_percent_raw\":" + Number(p.progress_percent_raw) +
      ",\"progress_numerator_raw\":" + Number(p.progress_numerator_raw) +
      ",\"progress_denominator_raw\":" + Number(p.progress_denominator_raw) +
      ",\"runtime_threshold_count\":" + Number(p.runtime_threshold_count) +
      ",\"level_lower_threshold_raw\":" + Number(p.level_lower_threshold_raw) +
      ",\"level_upper_threshold_raw\":" + Number(p.level_upper_threshold_raw) +
      ",\"native_terminal_threshold_branch\":" + Bool(p.native_terminal_threshold_branch) +
      ",\"raw_scale\":100000,\"progress_unit\":\"percent\",\"is_monthly_change\":false}";
}
} // namespace xar::ck3_12002::religion::devotion_profile12003
