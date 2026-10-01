#pragma once

#include "xar_bridge/ck3_12002_epidemic_treatment_presence.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerEpidemicTreatmentPrivateStep12002 =
    "query-player-epidemic-treatment-presence-v1";

struct PlayerEpidemicTreatmentMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  TreatmentPresenceBindings12002 bindings{};
  ck3_11906::PlayerEpidemicTreatmentPresenceV1 observation{};
  bool completed = false;
  std::string failure{};
};

bool IsPlayerEpidemicTreatmentPrivateStep12002(std::string_view step) noexcept;
bool ExecutePlayerEpidemicTreatmentMailbox12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Fixture bindings are accepted only by an explicitly offline fixture mailbox.
// All normal callers use the exact-build image binder and the native adapter.
bool HandlePlayerEpidemicTreatmentPrivate12002(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload, std::string_view request_id,
    std::string &serialized, std::string &failure,
    const TreatmentPresenceBindings12002 *fixture_bindings = nullptr) noexcept;

} // namespace xar::ck3_12002
