#pragma once
#include "xar_bridge/ck3_1210_actor_resource_leaf_v2.hpp"
#include "xar_bridge/ck3_1210_non_cash_decoder_v1.hpp"
namespace xar::ck3_1210 {
struct NonCashOwnerSourceObservationV3 {
  // Internal DATA only. V2 wire renown/true_treasury remain unavailable.
  bool owner_source_interval_verified = false;
  ActorResourceLeafObservationV2 before{}, after{};
  NonCashRawDecodeV1 renown{}, treasury{};
  std::string_view unavailable_reason = "additional_sources_not_read";
};
// Real Actor mailbox only, behind a separate default-OFF feature. Re-enters
// the actual v2 source reader before/after, resolves the real actor generation,
// samples exact1210 raw source chains, and retains independent unknown rows.
// No caller raw values/pointers, wire/Root/action role or government spend role.
bool ReadNonCashOwnerSourcesV3(const ActorResourceLeafSourceInputV2 &input,
    NonCashOwnerSourceObservationV3 &output) noexcept;
} // namespace xar::ck3_1210
