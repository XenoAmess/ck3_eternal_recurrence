#pragma once

#include "xar_bridge/ck3_1210_personal_cash_v1.hpp"
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"

namespace xar::ck3_1210 {

inline constexpr char kPersonalCashCapabilityV1[] =
    "game.query.war-cash-current-resources.v1";
inline constexpr char kPersonalCashCapabilityV2[] =
    "game.query.war-cash-current-resources.v2";

// Owned by the synchronous bridge query until its existing Actor MQ ticket
// reaches a terminal state and is reclaimed. No address here is wire input.
struct PersonalCashMailboxContextV1 {
  PersonalCashScopeVersion scope_version = PersonalCashScopeVersion::legacy_nonnegative_v1;
  PersonalCashBindingsV1 bindings{};
  // The unwrapped native adapter, never the WorkerAdapter (which would queue
  // another MQ operation). The trusted bridge supplies this adapter identity.
  const game::GameAdapter *native_full_adapter = nullptr;
  game::Snapshot expected_full{};
  std::uint64_t expected_native_revision = 0;
  // Original single bridge worker state. The worker synchronously waits and
  // does not write/destroy this value until this Actor ticket is reclaimed.
  const std::uint64_t *current_published_revision = nullptr;
  PersonalCashObservationV1 observation{};
  bool application_main_observed = false;
};

// Called only by ExecutePersonalGoldMailboxV1's personal_cash kind branch.
// Independently verifies that exact Actor executor/context/sequence is really
// executing on the warmed paused main owner with the supplied native stamp.
// Only then does a local binding copy open both provider/monthly call gates.
// The existing fixed Actor MQ slot is reused; no executor is registered here.
bool ExecutePersonalCashOnActorOwnerV1(PersonalGoldMailboxContextV1 &parent,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// Inner legacy result only. Bridge owns transport/request wrapping and the
// Java receipt owns queried_* metadata. No roles/capabilities are granted.
std::string SerializePersonalCashFrameResultV1(
    const PersonalCashMailboxContextV1 &context);
std::string SerializePersonalCashFrameResultV2(
    const PersonalCashMailboxContextV1 &context);

} // namespace xar::ck3_1210
