#pragma once
#include "xar_bridge/ck3_121003_courtier_configuration26785313_v1.hpp"
#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct CourtierConfigurationScene267V1{
 std::uintptr_t jomini=0,application=0,context=0,global=0;std::uint64_t wall_deadline=0;
 // Exactly the global, confirmation layer and the three fixed creator ancestors.
 // Missing creator is legal only after complete current confirmation-name inventory.
 std::vector<GuiWindowNodeV1>chain;
 friend bool operator==(const CourtierConfigurationScene267V1&,const CourtierConfigurationScene267V1&)=default;
};
struct CourtierConfigurationRaw267V1{
 CourtierConfigurationSource267V1 source;std::uintptr_t actor=0,definition=0,cost_definition=0;std::array<std::byte,64>definition_header{};
 bool native_read_entered=false,cleanup_known=true;
 friend bool operator==(const CourtierConfigurationRaw267V1&,const CourtierConfigurationRaw267V1&)=default;
};
bool VerifyCourtierConfigurationImage267V1(std::uintptr_t)noexcept;
bool ReadCourtierConfigurationRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CourtierConfigurationScene267V1&,std::uint64_t,CourtierProduct267V1,CourtierSetting267V1,CourtierConfigurationRaw267V1&,std::string&)noexcept;
LetterRawCall267V1 ExecuteCourtierControlRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CourtierConfigurationScene267V1&,std::uint64_t,const CourtierConfigurationRaw267V1&)noexcept;
}
