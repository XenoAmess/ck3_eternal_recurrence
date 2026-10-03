#pragma once

#include "xar_bridge/ck3_12003_spiritual_fulfillment_progress.hpp"

namespace xar::ck3_12003::religion::fulfillment_type {

using Bindings = ck3_12002::religion::fulfillment_progress12003::Bindings;
using CurrentContext = ck3_12002::religion::Context;
inline constexpr std::string_view kSchema = "ck3_12003_spiritual_fulfillment_type_v1";
inline constexpr std::string_view kChristianType = "christian_fulfillment";

struct Type {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::string> spiritual_fulfillment_type_key;
  std::optional<bool> has_christian_fulfillment_type;
};

// Reuses the existing exact .3 progress binding and current Context owner.
// No additional binding, enumeration or getter is created for Tenet/DLC data.
bool ReadPlayerSpiritualFulfillmentType12003(const Bindings &,
    void *actual_played_character, const CurrentContext &, Type &) noexcept;
std::string SerializePlayerSpiritualFulfillmentType12003(const Type &);

} // namespace xar::ck3_12003::religion::fulfillment_type
