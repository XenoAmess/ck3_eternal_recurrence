#pragma once
#include "xar_bridge/ck3_121003_lyd_decisions26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct LydNamedRoot267V1{std::uintptr_t widget=0;bool visible=false,enabled=false;friend bool operator==(const LydNamedRoot267V1&,const LydNamedRoot267V1&)=default;};
struct LydScene267V1:LydDecisionScene267V1{
 LydKind267V1 kind=LydKind267V1::decisions;std::uint64_t wall_deadline=0;
 std::uintptr_t application=0,events_layer=0,confirmation_layer=0,personal_root=0;
 bool personal_visible=false,personal_enabled=false;
 std::vector<LydNamedRoot267V1>event_roots,confirmation_roots;
 std::optional<RawResources>resources;
 friend bool operator==(const LydScene267V1&,const LydScene267V1&)=default;
};
struct LydSelectionAssociation267V1{
 LydPersonal267V1 personal=LydPersonal267V1::reverent_heaven;
 std::uintptr_t resident=0,root=0,context=0,definition=0,actor=0;
 std::uint64_t wall_deadline=0,monotonic_deadline=0;
 friend bool operator==(const LydSelectionAssociation267V1&,const LydSelectionAssociation267V1&)=default;
};
struct LydEventRawRow267V1{
 LetterRaw267V1 material;
 std::int32_t instance_id=0;std::uintptr_t controller=0,root=0,data=0,runtime=0,definition=0,option_data=0;
 std::vector<std::uintptr_t>options;
 friend bool operator==(const LydEventRawRow267V1&,const LydEventRawRow267V1&)=default;
};
struct LydPersonalChoice267V1{
 std::string key,token;std::uintptr_t definition=0;bool admissible=false;
 friend bool operator==(const LydPersonalChoice267V1&,const LydPersonalChoice267V1&)=default;
};
struct LydRaw267V1{
 LydSource267V1 source;LydDecisionRaw267V1 decision;
 std::uintptr_t actor=0,resident=0,root=0,modal=0,dialog_manager=0;
 std::vector<std::byte>semantic_model,modal_source;
 std::vector<LydEventRawRow267V1>event_rows;std::vector<LydPersonalChoice267V1>choices;
 LetterRaw267V1 manager_census;
 std::uint64_t token_generation=0,token_query=0;
 bool native_read_entered=false,cleanup_known=true;
 friend bool operator==(const LydRaw267V1&,const LydRaw267V1&)=default;
};
enum class LydRawCallStatus267V1{refused,returned,indeterminate};
struct LydRawCall267V1{LydRawCallStatus267V1 status=LydRawCallStatus267V1::refused;bool effect_entered=false,native_handled=false,cleanup_known=true;};
LydKind267V1 LydKindForAction267V1(LydAction267V1)noexcept;
bool LydQueryAction267V1(LydAction267V1)noexcept;
bool VerifyLydImage267V1(std::uintptr_t)noexcept;
bool ReadLydRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const LydScene267V1&,
 std::uint64_t,const LydRequest267V1&,const std::optional<LydSelectionAssociation267V1>&,LydRaw267V1&,std::string&)noexcept;
bool ReadFull111LydEventRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,
 const LydScene267V1&,std::uint64_t,const LydRequest267V1&,std::uintptr_t,LydRaw267V1&,std::string&)noexcept;
void TokenizeLydRaw267V1(LydRaw267V1&,std::uint64_t,std::uint64_t);
bool SameLydRawForLease267V1(const LydRaw267V1&,const LydRaw267V1&)noexcept;
bool LydRawAdmissible267V1(const LydRaw267V1&,const LydRequest267V1&)noexcept;
LydRawCall267V1 CallLydRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const LydScene267V1&,
 std::uint64_t,const LydRequest267V1&,const std::optional<LydSelectionAssociation267V1>&,const LydRaw267V1&)noexcept;
}
