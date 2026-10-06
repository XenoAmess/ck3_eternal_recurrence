#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"
#include "xar_bridge/religion_doctrine12002_tenet_rows.hpp"

#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::target_tenet {

inline constexpr const char *kSchema =
    "ck3_12003_target_rite_tenet_comparison_v1";

// The owning mailbox supplies its existing reviewed .3 bindings. This leaf has
// no image binder, process lookup, draft dependency or native command.
struct Bindings {
  ck3_12002::religion::Bindings context{};
  void *const *rite_storage_global{};
  void *const *tenet_database_global{};
  ck3_12002::religion::doctrine12002::NativeTenetState tenet_state{};
};

enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  actor_rite_unavailable,
  target_rite_unavailable,
  actor_faith_unavailable,
  target_faith_unavailable,
  actor_main_rite_unavailable,
  target_main_rite_unavailable,
  actor_core_tenets_unavailable,
  actor_main_core_tenets_unavailable,
  target_core_tenets_unavailable,
  target_main_core_tenets_unavailable,
  tenet_database_unavailable,
  tenet_definitions_unavailable,
  tenet_definition_key_unavailable,
  tenet_definition_unavailable,
  actor_tenet_state_unavailable,
  target_tenet_state_unavailable,
  state_changed,
  tenet_native_read_unavailable,
};

// A scope is published only after both reads close the complete comparison.
// Core membership is literal definition-pointer membership, independently of
// GetTenetStatus. It is not the stock rite_has_tenet trigger.
struct RiteObservation {
  std::uint32_t rite_id{0xFFFFFFFFU};
  std::uint32_t faith_id{0xFFFFFFFFU};
  std::uint32_t faith_main_rite_id{0xFFFFFFFFU};
  bool current_is_main{};
  bool core_tenets_complete{};
  std::vector<std::string> core_tenet_keys;
  bool faith_main_core_tenets_complete{};
  std::vector<std::string> faith_main_core_tenet_keys;
  bool named_tenet_core_member{};
  bool named_tenet_faith_main_core_member{};
  std::uint8_t named_tenet_status{};
  bool operator==(const RiteObservation &) const = default;
};

struct Comparison {
  bool available{};
  Failure failure{Failure::bindings_unavailable};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{0xFFFFFFFFU};
  std::uint32_t requested_target_rite_id{0xFFFFFFFFU};
  std::string tenet_key;
  std::optional<RiteObservation> actor_rite;
  std::optional<RiteObservation> target_rite;
  std::optional<bool> same_rite;
  std::optional<bool> same_faith;
  bool named_comparison_ready{};
};

// Existing paused application-main owner only; resolves the actual played
// character. Explicit target is a full-generation native Rite reference.
// Failure retains request/capture and any read owner date/player metadata;
// the owning mailbox can attach its admitted frame on an early read failure.
bool ReadPlayedTargetRiteTenetComparison12003(const Bindings &,
    std::uint32_t target_rite_id, std::string_view tenet_key,
    std::uint64_t capture_epoch, Comparison &output) noexcept;
const char *TargetRiteTenetComparisonFailureKey(Failure) noexcept;
std::string SerializeTargetRiteTenetComparison12003(const Comparison &);

} // namespace xar::ck3_12003::religion::target_tenet
