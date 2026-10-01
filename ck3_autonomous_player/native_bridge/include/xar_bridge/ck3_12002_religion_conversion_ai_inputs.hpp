#pragma once

#include "xar_bridge/ck3_12002.hpp"

#include <optional>
#include <string>

namespace xar::ck3_12002::religion_conversion_ai_inputs {

inline constexpr std::uintptr_t kRiteStorageSlotRva = 0x5D1E2F8;
inline constexpr std::uintptr_t kRiteBaseFulfillmentRva = 0x2BFC270;
inline constexpr std::size_t kCharacterRiteOffset = 0xB4;
inline constexpr std::size_t kRiteIdentityOffset = 0x08;
using BaseFulfillment = std::int64_t *(*)(std::int64_t *out, void *character, void *rite);

struct Bindings {
  bool enabled = false;
  CoreBindings core{};
  void **rite_storage_slot = nullptr;
  BaseFulfillment base_fulfillment = nullptr;
};

enum class Failure {
  none, bindings_unavailable, played_character_unavailable, frame_not_paused,
  current_rite_unavailable, target_rite_unavailable,
  base_fulfillment_unavailable, state_changed,
};

// Predicted base values from the native script evaluator. These are distinct
// from cached/current Spiritual Fulfillment and from post-conversion outcomes.
struct FulfillmentInput {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t target_rite_id = 0xFFFFFFFFU;
  std::optional<std::uint32_t> current_rite_id;
  std::optional<std::int64_t> current_rite_base_raw;
  std::optional<std::int64_t> target_rite_base_raw;
  std::optional<std::int64_t> expected_base_change_raw;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindConversionAIInputsImage12002(std::uintptr_t module_base,
                                         std::string_view executable_sha256) noexcept;
// Existing paused application-main owner only. The actor is always played.
// This query has no AI scheduler, conversion command, legality or policy.
bool ReadExpectedRiteFulfillment12002(const Bindings &, std::uint64_t epoch,
                                    std::uint32_t target_rite_id,
                                    FulfillmentInput &) noexcept;
const char *ConversionAIInputsFailureKey(Failure) noexcept;
std::string SerializeExpectedRiteFulfillment12002(const FulfillmentInput &);

} // namespace xar::ck3_12002::religion_conversion_ai_inputs
