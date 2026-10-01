#pragma once

#include "xar_bridge/ck3_12002_realm_law_source_adapter.hpp"

#include <memory>
#include <string>
#include <string_view>

namespace xar::ck3_12002 {

inline constexpr std::string_view kRealmLawCrownActionQueryStep12002 =
    "query-realm-law-crown-action-v1-private";
inline constexpr std::string_view kRealmLawCrownEnactStep12002 =
    "enact-realm-law-crown-v1-private";
inline constexpr std::string_view kRealmLawCrownReceiptStep12002 =
    "verify-realm-law-crown-v1-private";

// Durable LAW4/LAW5 state is shared by subsequent application-main requests.
// A transport ACK never clears the pending independent state verification.
struct RealmLawActionMailboxState12002 {
  RealmLawCrownSource12002 source{};
  bridge::RealmLawNativeBinderStateV1 binder{};
  bridge::RealmLawEnactActionAckV1 pending_ack{};
  std::uint64_t pending_sequence = 0;
  bool has_pending_ack = false;
};

// Fixture callbacks substitute only native image and call operations. The
// actual mailbox owner, frame, source adapter and binder still execute.
struct RealmLawActionMailboxFixture12002 {
  std::uintptr_t module_base = 0;
  void *context = nullptr;
  private_law::ReadRealmLawActiveMemory read_memory = nullptr;
  private_law::RealmLawFinalTerms12002Operations final_operations{};
  private_law::RealmLawComponentBindings12002 component_operations{};
  NativeCampaignRootCharacterResolverV1 primary_title = nullptr;
  private_law::AddLawCommandAccessV1 command_access{};
};

bool IsRealmLawPrivateActionStep12002(std::string_view step) noexcept;
bool ExecuteRealmLawPrivateAction12002(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

bool HandleRealmLawPrivate12002(
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

bool HandleRealmLawPrivateWithState12002(
    RealmLawActionMailboxState12002 &state,
    const game::GameAdapter &adapter,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure,
    const RealmLawActionMailboxFixture12002 *fixture = nullptr) noexcept;

// Value serializers are also consumed by the real offline wire fixture.
std::string SerializeRealmLawCrownActionObservation12002(
    const bridge::RealmLawEnactActionObservationV1 &observation);
std::string SerializeRealmLawCrownActionAck12002(
    const bridge::RealmLawEnactActionAckV1 &ack);
std::string SerializeRealmLawCrownActionReceipt12002(
    const bridge::RealmLawEnactActionReceiptV1 &receipt);

} // namespace xar::ck3_12002
