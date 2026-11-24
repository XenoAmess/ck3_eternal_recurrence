#pragma once
#include "xar_bridge/ck3_121003_living_inventory26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_lyd26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
// Native-private read association. Not a packet, capability, or action lease.
// The upstream new Living owner must supply the original common collector row,
// never a pointer/instance/artifact ID decoded from a caller's request.
struct LivingEventScopeData267V1 {
 std::int32_t instance_id=0,recipient_id=-1;
 std::string definition_key;
 LivingArtifactReference267V1 target,material;
 bool target_owned=false,material_owned=false,material_required=false;
 bool complete_named_scopes=false,sampled_twice=false;
 friend bool operator==(const LivingEventScopeData267V1&,const LivingEventScopeData267V1&)=default;
};
struct LivingEventScopeRaw267V1 {
 LivingEventScopeData267V1 source;
 std::vector<std::byte>fingerprint;
 bool entered=false,cleanup_known=true;
};
// Only fixed xalw.12/.10/.11 are understood; this does not acquire an event or
// grant existing LYD roles. Complete original event/census/Can checks remain a
// separate required AND in the future independent Living event owner.
bool ReadLivingEventArtifactScopes267V1(const ReadonlyBindings&,
 const LivingInventoryFrame267V1&,const LivingInventoryRequest267V1&,
 std::uint64_t original_mono,const LydEventRawRow267V1& actual_common_row,
 const LydEventRow267V1& actual_public_row,LivingEventScopeRaw267V1&,std::string&)noexcept;
}
