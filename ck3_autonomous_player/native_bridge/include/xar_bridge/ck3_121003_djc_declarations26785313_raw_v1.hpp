#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include <array>
#include <optional>
#include <string>
#include <vector>
namespace xar::ck3_121003::build26785313 {
inline constexpr std::array<std::string_view,3> kDjcCbKeys267V1{"duchy_de_jure_greatwar","kingdom_de_jure_greatwar","empire_de_jure_greatwar"};
struct DjcRawBindings267V1 {std::uintptr_t image=0;bool verified=false;};
struct DjcRawChoice267V1 {
 std::int32_t casus_belli_index=-1,configuration_index=-1,claimant_character_id=-1;
 std::vector<std::int32_t> target_title_ids,extra_configuration_ids;
 friend bool operator==(const DjcRawChoice267V1&,const DjcRawChoice267V1&)=default;
};
struct DjcRawCb267V1 {
 std::string key;bool definition_present=false,enabled=false,evaluation_returned=false;
 std::optional<bool> native_available;bool selection_materialization_available=true;
 std::vector<DjcRawChoice267V1> choices,configurations;
 // Private source material only. Never serialize native addresses/configuration bytes.
 std::uintptr_t definition=0;std::uint32_t flags=0;
 std::vector<std::array<std::byte,0x98>> exact_configurations;
};
struct DjcRawTarget267V1 {
 bool available=false,cleanup_known=true;std::int32_t target_character_id=-1;
 std::uintptr_t actor=0,target=0,database=0;std::array<std::byte,16> database_header{};
 std::array<DjcRawCb267V1,3> casus_belli{};std::string reason;
};
bool VerifyCurrentDjcDeclarationsImage267V1(std::uintptr_t) noexcept;
DjcRawBindings267V1 BindCurrentDjcDeclarations267V1(std::uintptr_t,std::string_view) noexcept;
// Raw fixed-domain algorithm only. This API is not an owner admission. Formal
// caller must establish actual current Core/owner/TLS/ticket/deadlines and retain
// cleanup UNKNOWN across reconnect. No old Full or SHA mapper is changed.
bool ReadCurrentDjcTargetRaw267V1(const ReadonlyBindings&,const DjcRawBindings267V1&,
 const ck3_1210::CoreSnapshotPrefix&,std::int32_t target,std::uint64_t monotonic_deadline,DjcRawTarget267V1&) noexcept;
}
