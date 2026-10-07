#pragma once

#include "xar_bridge/ck3_12002_realm_law_action_mailbox.hpp"
#include "xar_bridge/ck3_12004_realm_law_source_adapter.hpp"

namespace xar::ck3_12004 {

inline constexpr std::string_view kRealmLawCrownActionQueryStep12004 =
    ck3_12002::kRealmLawCrownActionQueryStep12002;
inline constexpr std::string_view kRealmLawCrownEnactStep12004 =
    ck3_12002::kRealmLawCrownEnactStep12002;
inline constexpr std::string_view kRealmLawCrownReceiptStep12004 =
    ck3_12002::kRealmLawCrownReceiptStep12002;

using RealmLawActionMailboxState12004 = ck3_12002::RealmLawActionMailboxState12002;
using RealmLawActionMailboxFixture12004 = ck3_12002::RealmLawActionMailboxFixture12002;

bool IsRealmLawPrivateActionStep12004(std::string_view step) noexcept;
bool ExecuteRealmLawPrivateAction12004(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

bool HandleRealmLawPrivate12004(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

bool HandleRealmLawPrivateWithState12004(
    RealmLawActionMailboxState12004 &state,
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure,
    const RealmLawActionMailboxFixture12004 *fixture = nullptr) noexcept;

} // namespace xar::ck3_12004
