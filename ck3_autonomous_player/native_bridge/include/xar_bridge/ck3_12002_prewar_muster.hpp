#pragma once

#include "xar_bridge/ck3_12002_military.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::string_view kPrewarDefaultMusterStepV1 =
    "query-prewar-default-muster-v1";

enum class PrewarDefaultMusterStatusV1 {
  available,
  partial,
  invalid_request,
  requires_paused,
  unavailable,
};

struct PrewarDefaultMusterRequestV1 {
  std::int32_t actor_character_id = -1;
  std::int32_t effective_defender_character_id = -1;
};

struct PrewarDefaultMusterRowV1 {
  std::int32_t character_id = -1;
  bool attacker = false;
  std::optional<std::int32_t> default_raise_province_id;
  std::optional<bool> native_default_raise_legal;
  std::string_view failure = "unavailable";
};

struct PrewarDefaultMusterObservationV1 {
  PrewarDefaultMusterStatusV1 status = PrewarDefaultMusterStatusV1::unavailable;
  std::int32_t date_raw = 0;
  PrewarDefaultMusterRequestV1 request;
  std::array<PrewarDefaultMusterRowV1, 2> rows{};
  bool default_raise_legality_ready = false;
  // Not inferred from default location or final legal command.
  bool hypothetical_raised_roster_ready = false;
  bool muster_time_ready = false;
  bool future_supply_ready = false;
};

// Executes only the existing 1.20 native selection, temporary construction,
// final validation and temporary destruction. No submission callback is used.
PrewarDefaultMusterStatusV1 ReadPrewarDefaultMusterV1(
    const MilitaryBindings &bindings, const MilitaryWorldAccess &world,
    const PrewarDefaultMusterRequestV1 &request,
    PrewarDefaultMusterObservationV1 &output) noexcept;

std::string SerializePrewarDefaultMusterV1(
    std::string_view request_id, std::uint64_t snapshot_revision,
    const PrewarDefaultMusterObservationV1 &observation);

} // namespace xar::ck3_12002
