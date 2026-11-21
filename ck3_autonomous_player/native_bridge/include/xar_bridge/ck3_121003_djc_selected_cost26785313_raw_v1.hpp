#pragma once
#include "xar_bridge/ck3_121003_djc_selected_cost26785313_v1.hpp"
#include "xar_bridge/ck3_121003_djc_declaration_ui26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Not an owner or capability. Prior is the actual private resident query witness.
bool ReadDjcSelectedCostRaw267V1(const ReadonlyBindings&,const DjcUiRawBindings267V1&,
 const ck3_1210::CoreSnapshotPrefix&,std::int32_t target,std::uint8_t cb,
 const DjcUiExpectedScene267V1&,std::uint64_t monotonic_deadline,
 const DjcUiRawObservation267V1&prior,DjcSelectedCostValues267V1&,std::string&)noexcept;
} // namespace
