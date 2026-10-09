#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/raiktor_actual_truce_expiry_v1.hpp"

namespace xar::ck3_12004 {
// Actual4 named has_truce -> CHasTruceTrigger -> readonly pair lookup source.
// Complete concrete predicate/date getter: 29131C0..2913215 / 2913220..29132A6.
// This binding never touches CWar or the relation get-or-create method.
inline constexpr std::uintptr_t kActualHasTruceRva12004 = 0x29131C0;
inline constexpr std::uintptr_t kActualTruceEndDateRva12004 = 0x2913220;
inline constexpr char kActualTruceExpiryBackend12004[] =
    "ck3-1.20.0.4-native-player-truce-expiry-v1";

struct ActualTruceExpiryBindings12004 {
  bool exact_build_admitted = false;
  CoreBindings core{};
  ck3_11906::RaiktorHasTruceV1 has_truce = nullptr;
  ck3_11906::RaiktorGetTruceEndDateV1 get_truce_end_date = nullptr;
};

ActualTruceExpiryBindings12004 BindActualTruceExpiryImage12004(
    void *module, std::string_view executable_sha256) noexcept;
// Called by the existing owning-main-thread semantic mailbox.
game::ReadRaiktorActualTruceExpiryResultV1 ReadActualTruceExpiry12004(
    const ActualTruceExpiryBindings12004 &bindings,
    std::int32_t toward_character_id,
    game::RaiktorActualTruceExpirySnapshotV1 &output) noexcept;
std::string SerializeActualTruceExpiry12004(
    const game::RaiktorActualTruceExpirySnapshotV1 &snapshot);
} // namespace xar::ck3_12004
