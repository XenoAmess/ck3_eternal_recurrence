#pragma once
#include "xar_bridge/ck3_121003_living_ui26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_weapon26785313_private_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Same private owner/world/complete GUI frame shape; the new detail collector
// must capture artifact_details_view, not reuse an inventory-root frame as one.
using LivingDetailFrame267V1=LivingWeaponFrame267V1;
struct LivingDetailRaw267V1 {
 LivingDetailData267V1 source;
 std::vector<std::byte>fingerprint;
 bool entered=false,cleanup_known=true;
};
bool ReadLivingDetailRaw267V1(const ReadonlyBindings&,const LivingDetailFrame267V1&,
 const LivingInventoryRequest267V1&,std::uint64_t original_mono,
 LivingDetailRaw267V1&,std::string&)noexcept;
}
