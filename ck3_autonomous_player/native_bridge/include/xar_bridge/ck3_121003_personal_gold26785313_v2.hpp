#pragma once
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include <string>
#include <string_view>

namespace xar::ck3_121003::build26785313 {
// V1 retains its original JSON-number amount. V2 uses an exact signed64 string.
inline constexpr char kPersonalGoldStepV2[]="query-personal-gold-frame-v2";
inline constexpr char kPersonalGoldCapabilityV2[]="game.query.personal-gold-frame.v2";
inline constexpr char kPersonalGoldSchemaV2[]="ck3_1210_personal_gold_frame_v2";
inline constexpr std::int32_t kPersonalGoldScaleV2=100000;
const game::AdapterDescriptor &PersonalGoldAdapterDescriptorV2() noexcept;
bool PersonalGoldRouteEnabledV2(const game::AdapterDescriptor &) noexcept;
// Empty unless both the exact current tuple and the explicit V2 step match.
std::string_view PersonalGoldStepCapabilityV2(const game::AdapterDescriptor &,
    std::string_view step) noexcept;
// Accepts only the existing production reader's completed atomic observation.
// An explicit offline fixture never grants application-main or live credit.
std::string SerializePersonalGoldCommandResultV2(std::string_view request_id,
    const ReadonlyObservation &,const game::AdapterDescriptor &);
} // namespace xar::ck3_121003::build26785313
