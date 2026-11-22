#pragma once
#include "xar_bridge/ck3_121003_courtier_choices26785313_v1.hpp"
#include "xar_bridge/ck3_121003_courtier_configuration26785313_raw_v1.hpp"
namespace xar::ck3_121003::build26785313 {
using CourtierChoicesScene267V1=CourtierConfigurationScene267V1;
struct CourtierChoiceIdentity267V1{std::array<std::byte,16>reference{};std::uintptr_t definition=0;std::array<std::byte,64>definition_header{};std::uintptr_t action_definition=0,selected_definition=0;std::array<std::byte,64>action_header{},selected_header{};friend bool operator==(const CourtierChoiceIdentity267V1&,const CourtierChoiceIdentity267V1&)=default;};
struct CourtierChoicesRaw267V1{CourtierChoicesSource267V1 source;std::uintptr_t actor=0,cost_definition=0;std::vector<CourtierChoiceIdentity267V1>identities,ancestors;bool native_read_entered=false,cleanup_known=true;};
bool SameCourtierChoicesRaw267V1(const CourtierChoicesRaw267V1&,const CourtierChoicesRaw267V1&)noexcept;
bool VerifyCourtierChoicesImage267V1(std::uintptr_t)noexcept;
bool ReadCourtierChoicesRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CourtierChoicesScene267V1&,std::uint64_t,CourtierProduct267V1,CourtierCatalog267V1,CourtierChoicesRaw267V1&,std::string&)noexcept;
LetterRawCall267V1 ExecuteCourtierChoiceRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CourtierChoicesScene267V1&,std::uint64_t,const CourtierChoicesRaw267V1&,std::size_t)noexcept;
}
