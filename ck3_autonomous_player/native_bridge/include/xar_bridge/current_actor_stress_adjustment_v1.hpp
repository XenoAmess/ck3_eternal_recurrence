#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12003 {

inline constexpr std::string_view kCurrentActorStressAdjustmentV1Step =
    "query-current-actor-stress-adjustment-v1";
inline constexpr std::string_view kCurrentActorStressAdjustmentV1Capability =
    "game.query.current-actor-stress-adjustment.v1";
inline constexpr std::string_view kCurrentActorStressAdjustmentV1Schema =
    "ck3-current-actor-stress-adjustment-v1";

struct CurrentActorStressAdjustmentRequestV1 {
  std::int32_t base_amount = 0;
  std::uint64_t expected_revision = 0;
  std::int32_t expected_player_character_id = -1;
  std::uint32_t expected_game_pid = 0;
  std::uint64_t expected_connection_generation = 0;
};

// Strict flat JSON numeric fields. No bool/float/string, duplicate, nested or
// unknown gameplay field can become a native read parameter.
bool ParseCurrentActorStressAdjustmentRequestV1(
    std::string_view wire, CurrentActorStressAdjustmentRequestV1 &out) noexcept;

struct CurrentActorStressAdjustmentNativeBindingsV1 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  std::string_view executable_sha256{};
  void **character_storage_slot = nullptr;
  bool (*verify_code_pins)(std::uintptr_t) noexcept = nullptr;
  void *(*get_character_modifier_aggregator)(void *) = nullptr;
  std::int64_t *(*read_character_modifier)(void *, std::int64_t *,
                                         std::int32_t) = nullptr;
  std::int32_t (*read_adjusted_stress_delta)(void *, std::int32_t) = nullptr;
};

CurrentActorStressAdjustmentNativeBindingsV1
BindCurrentActorStressAdjustmentImageV1(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
bool VerifyCurrentActorStressAdjustmentCodePinsV1(
    std::uintptr_t image_base) noexcept;

struct CurrentActorStressAdjustmentAccessV1 {
  void *context = nullptr;
  bool (*capture_frame)(void *, game::Snapshot &) noexcept = nullptr;
  bool (*is_owning_thread)(void *) noexcept = nullptr;
};

struct CurrentActorStressAdjustmentObservationV1 {
  bool available = false;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::uint32_t game_pid = 0;
  std::uint64_t connection_generation = 0;
  std::int32_t player_character_id = -1;
  std::int32_t base_amount = 0;
  std::optional<std::int32_t> current_stress_points{};
  std::optional<std::int64_t> stress_gain_modifier_raw{};
  std::optional<std::int64_t> stress_loss_modifier_raw{};
  std::optional<std::int32_t> adjusted_delta_points{};
  bool source_code_pins_verified = false;
  bool actor_binding_verified = false;
  bool owner_thread_verified = false;
  bool tls_verified = false;
  bool frame_verified = false;
  std::uint32_t owner_thread_id = 0;
  std::uint64_t owner_pump_epoch = 0;
  std::string_view unavailable_reason = "not_read";
};

// Only actual current alive paused player. Calls the read-only delta consumer,
// never the stress mutator. All values are withheld unless before/after agree.
bool ReadCurrentActorStressAdjustmentV1(
    const CurrentActorStressAdjustmentNativeBindingsV1 &bindings,
    const CurrentActorStressAdjustmentAccessV1 &access,
    const CurrentActorStressAdjustmentRequestV1 &request,
    const game::Snapshot &expected_frame,
    CurrentActorStressAdjustmentObservationV1 &out) noexcept;

void MakeCurrentActorStressAdjustmentUnavailableV1(
    CurrentActorStressAdjustmentObservationV1 &out,
    std::string_view reason) noexcept;

// Standard command.result contents, not the transport wrapper.
std::string SerializeCurrentActorStressAdjustmentV1(
    const CurrentActorStressAdjustmentObservationV1 &out,
    std::uint64_t query_sequence);

} // namespace xar::ck3_12003
