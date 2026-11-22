#pragma once
#include "xar_bridge/ck3_121003_courtier_controls26785313_v1.hpp"
#include "xar_bridge/ck3_121003_letter26785313_raw_v1.hpp"
#include "xar_bridge/ck3_121003_gui_window26785313_v1.hpp"
namespace xar::ck3_121003::build26785313 {
struct CourtierControlsScene267V1{
 std::uintptr_t jomini=0,application=0,context=0,global=0;std::uint64_t wall_deadline=0;
 // Exactly the global, confirmation layer and the three fixed creator ancestors.
 // Missing creator is legal only after complete current confirmation-name inventory.
 std::vector<GuiWindowNodeV1>chain;
 friend bool operator==(const CourtierControlsScene267V1&,const CourtierControlsScene267V1&)=default;
};
struct CourtierControlsRaw267V1{
 CourtierControlsSource267V1 source;std::uintptr_t actor=0,definition=0;std::array<std::byte,64>definition_header{};
 bool native_read_entered=false,cleanup_known=true;
 friend bool operator==(const CourtierControlsRaw267V1&,const CourtierControlsRaw267V1&)=default;
};
bool VerifyCourtierControlsImage267V1(std::uintptr_t)noexcept;
bool ReadCourtierControlsRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CourtierControlsScene267V1&,std::uint64_t,CourtierProduct267V1,CourtierControl267V1,CourtierControlsRaw267V1&,std::string&)noexcept;
LetterRawCall267V1 ExecuteCourtierControlRaw267V1(const ReadonlyBindings&,const ck3_1210::CoreSnapshotPrefix&,const CourtierControlsScene267V1&,std::uint64_t,const CourtierControlsRaw267V1&)noexcept;
}
